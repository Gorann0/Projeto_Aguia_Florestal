// js/utils/utils.js

/**
 * Retorna a data/hora atual no formato ISO 8601 UTC.
 * @returns {string} Ex: "2025-03-11T14:30:00.000Z"
 */
export function agoraUTC() {
    return new Date().toISOString();
  }
  
  /**
   * Compara dois timestamps ISO 8601.
   * @param {string} a - Primeiro timestamp.
   * @param {string} b - Segundo timestamp.
   * @returns {number} -1 se a < b, 0 se iguais, 1 se a > b.
   */
  export function compararTimestamps(a, b) {
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
  }
  
  /**
   * Verifica se o timestamp local é mais recente que o do servidor.
   * @param {string} local - Timestamp local.
   * @param {string} server - Timestamp do servidor.
   * @returns {boolean} True se local for mais novo.
   */
  export function isLocalMaisRecente(local, server) {
    return compararTimestamps(local, server) > 0;
  }
  
  /**
   * Formata uma data ISO para exibição local (dd/mm/aaaa hh:mm).
   * @param {string} isoString - Data em ISO UTC.
   * @returns {string} Data formatada.
   */
  export function formatarDataHora(isoString) {
    const data = new Date(isoString);
    return data.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  /**
   * Remove campos de autoria de um objeto antes de enviar ao backend.
   * @param {Object} obj - Objeto original.
   * @returns {Object} Objeto sem os campos proibidos.
   */
  export function removerCamposAutoria(obj) {
    const camposProibidos = ['criado_por_id', 'atualizado_por_id', 'operador_id'];
    const novo = { ...obj };
    for (const campo of camposProibidos) {
      delete novo[campo];
    }
    return novo;
  }
  
  /**
   * Gera um UUID v4.
   * @returns {string} UUID.
   */
  export function gerarUUID() {
    return crypto.randomUUID();
  }