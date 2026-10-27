// Ordem e cor das categorias: os tons de vermelho são as simbólicas, a tinta é o resto.
export const ORDEM_CATEGORIAS = ['calendario', 'patrimonio', 'logradouro', 'utilidade_publica', 'honraria', 'normativa'];

export const COR_CATEGORIA: Record<string, string> = {
  calendario: '#cf2e1b',
  patrimonio: '#e8664f',
  logradouro: '#9e1f10',
  utilidade_publica: '#f09a86',
  honraria: '#f2c2b5',
  normativa: 'var(--tinta)',
};

/** Escala do vermelho para o "quanto da produção é simbólica" (0 = tinta, 1 = carimbo). */
export function corSimbolica(fracao: number): string {
  const paradas = ['#2b2925', '#6e4a3c', '#a8402c', '#cf2e1b', '#ff4a2e'];
  const i = Math.min(paradas.length - 1, Math.max(0, Math.round(fracao * (paradas.length - 1))));
  return paradas[i];
}

/** Escala de presença nas votações nominais: claro = pouco, escuro = muito. */
export function corPresenca(taxa: number): string {
  const paradas = ['#f2b6a8', '#d9b48a', '#9fae8c', '#4f8a6a', '#1f5c45'];
  const i = Math.min(paradas.length - 1, Math.max(0, Math.floor(taxa * paradas.length)));
  return paradas[i];
}
