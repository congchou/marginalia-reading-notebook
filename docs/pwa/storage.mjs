import { localWrite, localDelete } from './sync.mjs';

const DATABASE_NAME = 'marginalia-pwa';
const DATABASE_VERSION = 1;

let databasePromise;

export function openDatabase() {
  if (!('indexedDB' in globalThis)) return Promise.reject(new Error('当前浏览器不支持本地数据库'));
  if (databasePromise) return databasePromise;
  databasePromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains('entries')) {
        const store = database.createObjectStore('entries', { keyPath: 'id' });
        store.createIndex('kind', 'kind');
        store.createIndex('status', 'status');
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('无法打开本地数据库'));
  }).catch((error) => {
    databasePromise = undefined;
    throw error;
  });
  return databasePromise;
}

async function runTransaction(mode, action) {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction('entries', mode);
    const store = transaction.objectStore('entries');
    let result;
    transaction.oncomplete = () => resolve(result);
    transaction.onerror = () => reject(transaction.error || new Error('本地保存失败'));
    transaction.onabort = () => reject(transaction.error || new Error('本地保存已取消'));
    try { action(store, (value) => { result = value; }); }
    catch (error) { transaction.abort(); reject(error); }
  });
}

export function getAllEntries() {
  return runTransaction('readonly', (store, setResult) => {
    const request = store.getAll();
    request.onsuccess = () => setResult(request.result.filter((entry) => !entry.deleted));
  });
}

export function getAllSyncEntries() {
  return runTransaction('readonly', (store, setResult) => {
    const request = store.getAll();
    request.onsuccess = () => setResult(request.result);
  });
}

export function putEntry(entry) {
  return runTransaction('readwrite', (store) => {
    const request = store.get(entry.id);
    request.onsuccess = () => store.put(localWrite(entry, request.result));
  });
}

export function putEntries(entries) {
  return runTransaction('readwrite', (store) => {
    for (const entry of entries) store.put(localWrite(entry));
  });
}

export function removeEntry(id) {
  return runTransaction('readwrite', (store) => {
    const request = store.get(id);
    request.onsuccess = () => { if (request.result) store.put(localDelete(request.result)); };
  });
}


export function putSyncedEntry(entry) {
  return runTransaction('readwrite', (store) => { store.put(entry); });
}

export function removeSyncedEntry(id) {
  return runTransaction('readwrite', (store) => { store.delete(id); });
}

function unchanged(current, snapshot) {
  return current && current.localRevision === snapshot.localRevision
    && current.syncVersion === snapshot.syncVersion && current.dirty === snapshot.dirty;
}

export function acknowledgeSyncedEntry(remote, snapshot) {
  return runTransaction('readwrite', (store, setResult) => {
    const request = store.get(snapshot.id);
    request.onsuccess = () => {
      const current = request.result;
      if (unchanged(current, snapshot)) {
        store.put({ ...remote, localRevision: current.localRevision });
        setResult(true);
      } else {
        // The network write succeeded, but a newer local edit must remain dirty.
        if (current && current.syncVersion === snapshot.syncVersion) {
          store.put({ ...current, syncVersion: remote.revision });
        }
        setResult(false);
      }
    };
  });
}

export function putSyncedEntryIfUnchanged(remote, snapshot) {
  return runTransaction('readwrite', (store, setResult) => {
    const request = store.get(snapshot.id);
    request.onsuccess = () => {
      if (unchanged(request.result, snapshot)) {
        store.put({ ...remote, localRevision: request.result.localRevision });
        setResult(true);
      } else setResult(false);
    };
  });
}

export function putSyncedEntryIfAbsent(remote) {
  return runTransaction('readwrite', (store, setResult) => {
    const request = store.get(remote.id);
    request.onsuccess = () => {
      if (!request.result) { store.put(remote); setResult(true); }
      else setResult(false);
    };
  });
}

export function removeSyncedEntryIfUnchanged(snapshot) {
  return runTransaction('readwrite', (store, setResult) => {
    const request = store.get(snapshot.id);
    request.onsuccess = () => {
      if (unchanged(request.result, snapshot)) { store.delete(snapshot.id); setResult(true); }
      else setResult(false);
    };
  });
}

export function adoptSyncedEntry(remote, snapshot) {
  return runTransaction('readwrite', (store, setResult) => {
    const request = store.get(snapshot.id);
    request.onsuccess = () => {
      if (!unchanged(request.result, snapshot)) { setResult(false); return; }
      const target = store.get(remote.id);
      target.onsuccess = () => {
        if (target.result) { setResult(false); return; }
        store.delete(snapshot.id);
        store.put(remote);
        setResult(true);
      };
    };
  });
}
