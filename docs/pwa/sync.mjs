import { identityOf, normalizeTags } from './data.mjs';

export function canUseAccount(boundUserId, signingInUserId) {
  return !boundUserId || boundUserId === signingInUserId;
}

export function localWrite(entry, previous = null) {
  return { ...entry, syncVersion: previous?.syncVersion || 0,
    localRevision: (previous?.localRevision || 0) + 1, dirty: true, deleted: false };
}

export function localDelete(entry) {
  return { ...entry, localRevision: (entry.localRevision || 0) + 1,
    dirty: true, deleted: true, updatedAt: new Date().toISOString() };
}

function cleanCopy(remote) {
  return { ...remote, syncVersion: remote.revision, dirty: false, deleted: Boolean(remote.deleted) };
}

function sameCardContent(left, right) {
  const fields = ['kind', 'word', 'meaning', 'sentence', 'translation', 'structure', 'source', 'status'];
  return fields.every((field) => String(left[field] || '') === String(right[field] || ''))
    && normalizeTags(left.tags).join(',') === normalizeTags(right.tags).join(',');
}

export async function syncCards(store, api) {
  const local = await store.getAllSyncEntries();
  const remote = await api.listCards();
  const remoteById = new Map(remote.map((entry) => [entry.id, entry]));
  const remoteByIdentity = new Map(remote.filter((entry) => !entry.deleted).map((entry) => [identityOf(entry), entry]));
  const localIds = new Set(local.map((entry) => entry.id));
  const result = { uploaded: 0, downloaded: 0, conflicts: 0 };

  for (const entry of local) {
    const server = remoteById.get(entry.id);
    const dirty = entry.dirty !== false;
    if (dirty) {
      if (server) {
        if (!entry.syncVersion && server.revision === 1 && sameCardContent(entry, server) && !entry.deleted) {
          await store.acknowledgeSyncedEntry(cleanCopy(server), entry);
          result.downloaded += 1;
          continue;
        }
        if (server.revision !== (entry.syncVersion || 0) && !(server.revision === 1 && !entry.syncVersion)) {
          result.conflicts += 1; continue;
        }
        const updated = await api.updateCard(entry, server.revision);
        if (!updated) { result.conflicts += 1; continue; }
        await store.acknowledgeSyncedEntry(cleanCopy(updated), entry);
        result.uploaded += 1;
      } else if (entry.syncVersion) {
        result.conflicts += 1;
      } else if (entry.deleted) {
        await store.removeSyncedEntryIfUnchanged(entry);
      } else if (remoteByIdentity.has(identityOf(entry))) {
        const matching = remoteByIdentity.get(identityOf(entry));
        if (sameCardContent(entry, matching)) {
          const adopted = await store.adoptSyncedEntry(cleanCopy(matching), entry);
          localIds.add(matching.id);
          if (adopted) result.downloaded += 1;
        } else result.conflicts += 1;
      } else {
        const created = await api.createCard(entry);
        await store.acknowledgeSyncedEntry(cleanCopy(created), entry);
        result.uploaded += 1;
      }
    } else if (server && server.revision > (entry.syncVersion || 0)) {
      if (await store.putSyncedEntryIfUnchanged(cleanCopy(server), entry)) result.downloaded += 1;
    }
  }

  for (const entry of remote) {
    if (localIds.has(entry.id)) continue;
    if (!entry.deleted && local.some((item) => !item.deleted && identityOf(item) === identityOf(entry))) {
      result.conflicts += 1;
      continue;
    }
    if (await store.putSyncedEntryIfAbsent(cleanCopy(entry))) result.downloaded += 1;
  }
  return result;
}
