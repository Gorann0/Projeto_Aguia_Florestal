// js/core/auth.js
import { apiPublic, apiPost } from './api.js';

// Carrega a lista de perfis (público)
export async function carregarPerfis() {
  return apiPublic('/usuarios/perfis');
}

// Efetua login com apelido e senha (PIN)
export async function login(apelido, senha) {

    const data = await apiPost('/auth/login', { apelido, senha });
  
    if (!data.access_token) {
      throw new Error('Falha na autenticação');
    }
  
    sessionStorage.setItem('token', data.access_token);
  
    if (data.usuario) {
      sessionStorage.setItem('user', JSON.stringify(data.usuario));
    }
  
    return data;
  }

// Logout: limpa sessão
export function logout() {
  sessionStorage.clear();
  // Opcional: chamar endpoint de logout se existir
  window.location.href = '/index.html';
}

// Verifica se está autenticado
export function isAuthenticated() {
  return !!sessionStorage.getItem('token');
}

export function getUser() {
    const user = sessionStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }