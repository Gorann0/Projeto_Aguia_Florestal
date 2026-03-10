// js/core/sync.js
import { apiPost, apiGet } from './api.js';
import {
  getQueue,
  removeFromQueue,
  getLastSync,
  setLastSync,
  put,
  get
} from './db.js';

import { STORES } from './config.js';

// Função auxiliar para comparar timestamps (last write wins)
function isLocalNewer(local, server) {
  return new Date(local.atualizado_em) > new Date(server.atualizado_em);
}

// Push: envia alterações locais para /sync/push
export async function push() {
  const queue = await getQueue();
  if (queue.length === 0) return;

  // Agrupar por tipo
  const payload = {
    ordens_servico: [],
    itens_checklist: []
  };

  for (const item of queue) {
    // Remover campos de autoria antes de enviar
    const data = { ...item.data };
    delete data.criado_por_id;
    delete data.atualizado_por_id;
    delete data.operador_id;

    if (item.entityType === 'ordens_servico') {
      payload.ordens_servico.push(data);
    } else if (item.entityType === 'itens_checklist') {
      payload.itens_checklist.push(data);
    }
    // Outros tipos não são enviados (ignorar)
  }

  try {
    const response = await apiPost('/sync/push', payload);

    // Processar applied
    for (const appliedId of (response.applied || [])) {
      // Encontrar o item na fila com esse ID (data.id)
      const queueItem = queue.find(q => q.data.id === appliedId);
      if (queueItem) {
        await removeFromQueue(queueItem.id);
      }
    }

    // Processar conflitos
    for (const conflict of (response.conflicts || [])) {
      const queueItem = queue.find(q => q.data.id === conflict.id);
      if (!queueItem) continue;

      if (isLocalNewer(queueItem.data, conflict.serverVersion)) {
        // Local mais novo: manter na fila (será reenviado no próximo push)
        // Não faz nada
      } else {
        // Servidor mais novo: substituir local e remover da fila
        await put(conflict.entityType, conflict.serverVersion);
        await removeFromQueue(queueItem.id);
      }
    }

    return response.timestamp;
  } catch (error) {
    console.error('Erro no push:', error);
    throw error;
  }
}

// Pull: busca atualizações desde last_sync
export async function pull() {
  const lastSync = await getLastSync();
  const payload = { last_sync: lastSync };

  try {
    const response = await apiPost('/sync/pull', payload);
    const { timestamp, ...entities } = response;

    // Atualizar cada store
    const local = await get(entityType, serverRecord.id);
    for (const [entityType, records] of Object.entries(entities)) {
      if (!Array.isArray(records)) continue;

      for (const serverRecord of records) {
        const local = await db.get(entityType, serverRecord.id);
        if (!local) {
          // Novo registro
          await put(entityType, serverRecord);
        } else {
          // Comparar timestamps
          if (new Date(local.atualizado_em) < new Date(serverRecord.atualizado_em)) {
            await put(entityType, serverRecord);
          }
          // Se local for mais novo, manter local (não sobrescrever)
        }
      }
    }

    await setLastSync(timestamp);
    return timestamp;
  } catch (error) {
    console.error('Erro no pull:', error);
    throw error;
  }
}

// Função completa: push + pull
export async function sincronizar() {
  if (!navigator.onLine) {
    throw new Error('Offline');
  }
  await push();
  await pull();
}