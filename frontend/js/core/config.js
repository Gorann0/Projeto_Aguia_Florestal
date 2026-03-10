// js/core/config.js

export const API_BASE_URL = 'http://localhost:8000'; // Adicionar URL real dps

export const DB_VERSION = 1;
export const DB_NAME = 'aguia-florestal-db';

export const STORES = Object.freeze({
  USUARIOS: 'usuarios',
  MAQUINAS: 'maquinas',
  MANUAIS: 'manuais',
  MODELOS_CHECKLIST: 'modelos_checklist',
  AGENDAMENTOS_CHECKLIST: 'agendamentos_checklist',
  ITENS_CHECKLIST: 'itens_checklist',
  ORDENS_SERVICO: 'ordens_servico',
  SYNC_QUEUE: 'sync_queue',
  SYNC_METADATA: 'sync_metadata'
});

export const FETCH_TIMEOUT = 10000;

export const SYNC_INTERVAL = 30000;

export const MAX_SYNC_QUEUE = 500;