// js/core/db.js
import { DB_NAME, DB_VERSION, STORES } from './config.js';

let dbInstance = null;

export async function openDB() {
  if (dbInstance) return dbInstance;

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Cria as stores (apenas se não existirem)
      if (!db.objectStoreNames.contains(STORES.USUARIOS)) {
        db.createObjectStore(STORES.USUARIOS, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORES.MAQUINAS)) {
        const store = db.createObjectStore(STORES.MAQUINAS, { keyPath: 'id' });
        store.createIndex('atualizado_em', 'atualizado_em');
      }
      if (!db.objectStoreNames.contains(STORES.MANUAIS)) {
        const store = db.createObjectStore(STORES.MANUAIS, { keyPath: 'id' });
        store.createIndex('maquina_id', 'maquina_id');
        store.createIndex('atualizado_em', 'atualizado_em');
      }
      if (!db.objectStoreNames.contains(STORES.MODELOS_CHECKLIST)) {
        const store = db.createObjectStore(STORES.MODELOS_CHECKLIST, { keyPath: 'id' });
        store.createIndex('atualizado_em', 'atualizado_em');
      }
      if (!db.objectStoreNames.contains(STORES.AGENDAMENTOS_CHECKLIST)) {
        const store = db.createObjectStore(STORES.AGENDAMENTOS_CHECKLIST, { keyPath: 'id' });
        store.createIndex('maquina_id', 'maquina_id');
        store.createIndex('data_vencimento', 'data_vencimento');
        store.createIndex('atualizado_em', 'atualizado_em');
      }
      if (!db.objectStoreNames.contains(STORES.ITENS_CHECKLIST)) {
        const store = db.createObjectStore(STORES.ITENS_CHECKLIST, { keyPath: 'id' });
        store.createIndex('agendamento_id', 'agendamento_id');
        store.createIndex('atualizado_em', 'atualizado_em');
      }
      if (!db.objectStoreNames.contains(STORES.ORDENS_SERVICO)) {
        const store = db.createObjectStore(STORES.ORDENS_SERVICO, { keyPath: 'id' });
        store.createIndex('maquina_id', 'maquina_id');
        store.createIndex('status', 'status');
        store.createIndex('atualizado_em', 'atualizado_em');
      }
      if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
        const store = db.createObjectStore(STORES.SYNC_QUEUE, { keyPath: 'id' });
        store.createIndex('entityType', 'entityType');
        store.createIndex('createdAt', 'createdAt');
      }
      if (!db.objectStoreNames.contains(STORES.SYNC_METADATA)) {
        db.createObjectStore(STORES.SYNC_METADATA, { keyPath: 'key' });
      }
    };

    request.onsuccess = (event) => {
      dbInstance = event.target.result;
      resolve(dbInstance);
    };

    request.onerror = (event) => {
      reject(event.target.error);
    };

    request.onblocked = () => {
        console.warn('IndexedDB blocked. Close other tabs.');
    };
  });
}

// Operações genéricas
export async function getAll(storeName) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function get(storeName, id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const request = store.get(id);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function put(storeName, data) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    const request = store.put(data);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function deleteItem(storeName, id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// Fila de sincronização
export async function addToQueue(entityType, data) {
  const db = await openDB();
  const id = crypto.randomUUID();
  const queueItem = {
    id,
    entityType,
    data,
    operation: 'upsert',
    createdAt: new Date().toISOString()
  };
  await put(STORES.SYNC_QUEUE, queueItem);
  return id;
}

export async function getQueue() {
  return getAll(STORES.SYNC_QUEUE);
}

export async function removeFromQueue(queueItemId) {
  return deleteItem(STORES.SYNC_QUEUE, queueItemId);
}

// Metadados (última sincronização)
export async function getLastSync() {
  const db = await openDB();
  return new Promise((resolve) => {
    const tx = db.transaction(STORES.SYNC_METADATA, 'readonly');
    const store = tx.objectStore(STORES.SYNC_METADATA);
    const request = store.get('last_sync');
    request.onsuccess = () => {
      resolve(request.result ? request.result.value : '1970-01-01T00:00:00.000Z');
    };
    request.onerror = () => resolve('1970-01-01T00:00:00.000Z');
  });
}

export async function setLastSync(timestamp) {
  const db = await openDB();
  return put(STORES.SYNC_METADATA, { key: 'last_sync', value: timestamp });
}

// Consultas por índice
export async function getAllFromIndex(storeName, indexName, value) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const index = store.index(indexName);
    const request = index.getAll(value);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function clearStore(storeName) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }