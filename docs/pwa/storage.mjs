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
    request.onsuccess = () => setResult(request.result);
  });
}

export function putEntry(entry) {
  return runTransaction('readwrite', (store) => { store.put(entry); });
}

export function putEntries(entries) {
  return runTransaction('readwrite', (store) => {
    for (const entry of entries) store.put(entry);
  });
}

export function removeEntry(id) {
  return runTransaction('readwrite', (store) => { store.delete(id); });
}
