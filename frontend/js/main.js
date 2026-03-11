// js/main.js
import { isAuthenticated } from './core/auth.js';
import { openDB } from './core/db.js';
import { sincronizar } from './core/sync.js';

// Inicialização global
(async () => {

  try {
    await openDB();
    console.log('Banco de dados inicializado');
  } catch (error) {
    console.error('Erro ao abrir o banco de dados:', error);
  }

  const publicPages = ['/', '/index.html'];
  const currentPath = window.location.pathname;
  const autenticado = isAuthenticated();

  // proteção de páginas
  if (!publicPages.includes(currentPath) && !autenticado) {
    window.location.href = '/';
    return;
  }

  // sincronização inicial
  if (autenticado && navigator.onLine) {
    try {
      await sincronizar();
      document.body.dispatchEvent(new CustomEvent('sync-complete'));
      console.log('Sincronização inicial concluída');
    } catch (error) {
      console.warn('Sincronização inicial falhou:', error);
      document.body.dispatchEvent(
        new CustomEvent('sync-error', { detail: error })
      );
    }
  }

})();

// conexão voltou
window.addEventListener('online', async () => {

  console.log('Conexão restabelecida');

  if (!isAuthenticated()) return;

  try {
    await sincronizar();
    document.body.dispatchEvent(new CustomEvent('sync-complete'));
  } catch (error) {
    document.body.dispatchEvent(
      new CustomEvent('sync-error', { detail: error })
    );
  }

});

// perdeu conexão
window.addEventListener('offline', () => {
  console.warn('Aplicação offline');
});