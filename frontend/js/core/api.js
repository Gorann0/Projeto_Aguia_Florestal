// js/core/api.js
import { API_BASE_URL, FETCH_TIMEOUT } from './config.js';
import { openDB, addToQueue } from './db.js';

// Função auxiliar para incluir token e timeout
async function fetchWithToken(endpoint, options = {}) {
  const token = sessionStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

  try {
    const response = await fetch(API_BASE_URL + endpoint, {
      ...options,
      headers,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Erro HTTP ${response.status}`);
    }
    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

// Cliente público (sem token) para endpoints de login/perfis
async function fetchPublic(endpoint, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const response = await fetch(API_BASE_URL + endpoint, { ...options, headers });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Erro HTTP ${response.status}`);
  }
  return response.json();
}

// Método GET (pode ser usado para leituras que não precisam de cache offline)
export async function apiGet(endpoint) {
  return fetchWithToken(endpoint);
}

// Método POST com suporte a fila offline para entidades graváveis
export async function apiPost(endpoint, data) {
  // Se for um endpoint de escrita offline (itens_checklist ou ordens_servico)
  if (endpoint === '/itens_checklist' || endpoint === '/ordens_servico') {
    const entityType = endpoint.slice(1); // remove a barra
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const record = {
      ...data,
      id,
      atualizado_em: now,
      criado_em: now
    };

    const db = await openDB();
    await db.put(entityType, record);
    await addToQueue(entityType, record);

    return { queued: true, id };
  }

  // Demais endpoints (login, sync, etc.) fazem requisição normal
  return fetchWithToken(endpoint, { method: 'POST', body: JSON.stringify(data) });
}

// PUT similar (se necessário)
export async function apiPut(endpoint, data) {

    if (endpoint === '/itens_checklist' || endpoint === '/ordens_servico') {
  
      const entityType = endpoint.slice(1);
      const now = new Date().toISOString();
  
      const record = {
        ...data,
        atualizado_em: now
      };
  
      const db = await openDB();
  
      await db.put(entityType, record);
  
      await addToQueue(entityType, record);
  
      return { queued: true, id: record.id };
    }
  
    return fetchWithToken(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

// Função para upload de arquivo (manual) - não passa pela fila
export async function uploadManual(formData) {
  const token = sessionStorage.getItem('token');
  const response = await fetch(API_BASE_URL + '/manuais/upload', {
    method: 'POST',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}, // não setar Content-Type, o browser define com boundary
    body: formData
  });
  if (!response.ok) throw new Error('Erro no upload');
  return response.json();
}