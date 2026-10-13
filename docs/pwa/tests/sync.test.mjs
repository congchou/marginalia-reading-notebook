import test from 'node:test';
import assert from 'node:assert/strict';
import { syncCards, localWrite, localDelete, canUseAccount } from '../sync.mjs';

function memoryStore(entries) {
  const records = new Map(entries.map((entry) => [entry.id, { ...entry }]));
  return {
    records,
    getAllSyncEntries: async () => [...records.values()],
    putSyncedEntry: async (entry) => { records.set(entry.id, { ...entry }); },
    removeSyncedEntry: async (id) => { records.delete(id); },
    removeSyncedEntryIfUnchanged: async (snapshot) => {
      if (records.get(snapshot.id)?.localRevision === snapshot.localRevision) records.delete(snapshot.id);
    },
    adoptSyncedEntry: async (remote, snapshot) => {
      if (records.get(snapshot.id)?.localRevision !== snapshot.localRevision) return false;
      records.delete(snapshot.id); records.set(remote.id, { ...remote }); return true;
    },
    putSyncedEntryIfAbsent: async (remote) => {
      if (records.has(remote.id)) return false;
      records.set(remote.id, { ...remote }); return true;
    },
    acknowledgeSyncedEntry: async (remote, snapshot) => {
      const current = records.get(snapshot.id);
      if (!current || current.localRevision !== snapshot.localRevision) {
        if (current && current.syncVersion === snapshot.syncVersion) records.set(snapshot.id, { ...current, syncVersion: remote.revision });
        return false;
      }
      records.set(snapshot.id, { ...remote, dirty: false, syncVersion: remote.revision, localRevision: current.localRevision });
      return true;
    },
    putSyncedEntryIfUnchanged: async (remote, snapshot) => {
      const current = records.get(snapshot.id);
      if (!current || current.localRevision !== snapshot.localRevision || current.dirty !== snapshot.dirty) return false;
      records.set(snapshot.id, { ...remote, dirty: false, syncVersion: remote.revision, localRevision: current.localRevision });
      return true;
    },
  };
}

const word = (id, changes = {}) => ({ id, kind: 'word', word: 'criterion', meaning: '标准', sentence: '', translation: '', structure: '', source: '', tags: [], status: '待复习', createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z', ...changes });

test('local edit preserves cloud version and marks record dirty', () => {
  const edited = localWrite(word('card-1', { meaning: '新释义' }), word('card-1', { syncVersion: 4, dirty: false }));
  assert.equal(edited.syncVersion, 4);
  assert.equal(edited.dirty, true);
  assert.equal(edited.meaning, '新释义');
});

test('local deletion retains a tombstone for later upload', () => {
  const deleted = localDelete(word('card-1', { syncVersion: 4, dirty: false }));
  assert.equal(deleted.deleted, true);
  assert.equal(deleted.dirty, true);
  assert.equal(deleted.syncVersion, 4);
});

test('rejects a different account on a device already bound to one user', () => {
  assert.equal(canUseAccount(null, 'user-1'), true);
  assert.equal(canUseAccount('user-1', 'user-1'), true);
  assert.equal(canUseAccount('user-1', 'user-2'), false);
});

test('uploads a new offline card and marks it clean only after success', async () => {
  const store = memoryStore([word('local-1', { dirty: true, syncVersion: 0 })]);
  const api = { listCards: async () => [], createCard: async (entry) => ({ ...entry, revision: 1, user_id: 'user-1' }) };
  const result = await syncCards(store, api);
  assert.deepEqual(result, { uploaded: 1, downloaded: 0, conflicts: 0 });
  assert.equal(store.records.get('local-1').dirty, false);
  assert.equal(store.records.get('local-1').syncVersion, 1);
});

test('does not overwrite a dirty local card when remote revision changed', async () => {
  const store = memoryStore([word('card-1', { meaning: '本地修改', dirty: true, syncVersion: 1 })]);
  const api = { listCards: async () => [word('card-1', { meaning: '另一端修改', revision: 2 })], updateCard: async () => { throw new Error('must not overwrite'); } };
  const result = await syncCards(store, api);
  assert.equal(result.conflicts, 1);
  assert.equal(store.records.get('card-1').meaning, '本地修改');
  assert.equal(store.records.get('card-1').dirty, true);
});

test('downloads remote changes and tombstones to a clean local store', async () => {
  const store = memoryStore([word('card-1', { syncVersion: 1, dirty: false })]);
  const api = { listCards: async () => [word('card-1', { meaning: '新版', revision: 2 }), word('card-2', { word: 'obsolete', deleted: true, revision: 3 })] };
  const result = await syncCards(store, api);
  assert.deepEqual(result, { uploaded: 0, downloaded: 2, conflicts: 0 });
  assert.equal(store.records.get('card-1').meaning, '新版');
  assert.equal(store.records.get('card-2').deleted, true);
});

test('sends offline deletion as a tombstone', async () => {
  const store = memoryStore([word('card-1', { deleted: true, dirty: true, syncVersion: 2 })]);
  const api = { listCards: async () => [word('card-1', { revision: 2 })], updateCard: async (entry, version) => {
    assert.equal(version, 2);
    assert.equal(entry.deleted, true);
    return { ...entry, revision: 3 };
  } };
  const result = await syncCards(store, api);
  assert.equal(result.uploaded, 1);
  assert.equal(store.records.get('card-1').deleted, true);
  assert.equal(store.records.get('card-1').dirty, false);
});

test('adopts an identical cloud card instead of duplicating first-sync data', async () => {
  const store = memoryStore([word('local-1', { dirty: true, syncVersion: 0 })]);
  const api = { listCards: async () => [word('cloud-1', { revision: 1 })], createCard: async () => { throw new Error('duplicate upload'); } };
  const result = await syncCards(store, api);
  assert.equal(result.conflicts, 0);
  assert.equal(store.records.has('local-1'), false);
  assert.equal(store.records.get('cloud-1').dirty, false);
});

test('keeps an edit made while a cloud upload is in flight', async () => {
  const store = memoryStore([word('card-1', { dirty: true, syncVersion: 0, localRevision: 1 })]);
  const api = { listCards: async () => [], createCard: async (entry) => {
    store.records.set('card-1', localWrite(word('card-1', { meaning: '更新的本地释义' }), store.records.get('card-1')));
    return { ...entry, revision: 1 };
  } };
  await syncCards(store, api);
  assert.equal(store.records.get('card-1').meaning, '更新的本地释义');
  assert.equal(store.records.get('card-1').dirty, true);
  assert.equal(store.records.get('card-1').syncVersion, 1);
});

test('keeps an offline delete made while remote download is in flight', async () => {
  const store = memoryStore([word('card-1', { dirty: false, syncVersion: 1, localRevision: 1 })]);
  const api = { listCards: async () => {
    store.records.set('card-1', localDelete(store.records.get('card-1')));
    return [word('card-1', { meaning: 'remote', revision: 2 })];
  } };
  await syncCards(store, api);
  assert.equal(store.records.get('card-1').deleted, true);
  assert.equal(store.records.get('card-1').dirty, true);
});

test('recovers a POST that reached cloud but whose response was lost', async () => {
  const store = memoryStore([word('card-1', { dirty: true, syncVersion: 0, localRevision: 1 })]);
  const api = { listCards: async () => [word('card-1', { revision: 1 })], updateCard: async (entry, version) => ({ ...entry, revision: version + 1 }) };
  const result = await syncCards(store, api);
  assert.equal(result.conflicts, 0);
  assert.equal(store.records.get('card-1').dirty, false);
});
