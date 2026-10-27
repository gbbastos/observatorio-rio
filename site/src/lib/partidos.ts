// Cor de cada partido no plenário. Não é a cor oficial de cada sigla: é uma paleta escolhida para
// que bancadas vizinhas se distingam; a legenda e o cartão de cada cadeira dizem o nome.

const CORES: Record<string, string> = {
  PSD: '#2f6fd0',
  PL: '#17325e',
  PT: '#c8102e',
  PSOL: '#f2a900',
  PP: '#53b6c9',
  MDB: '#7dae2b',
  UNIÃO: '#0d7f86',
  REPUBLICANOS: '#2c6e49',
  PODE: '#6d4fa8',
  PSDB: '#93b7e3',
  SD: '#f07a1e',
  PDT: '#e3647a',
  PSB: '#f5c14b',
  AVANTE: '#b08bc9',
  PRD: '#8a6240',
  PCDOB: '#7d0f16',
  NOVO: '#ff7b2e',
  PV: '#3f9b36',
  REDE: '#1f9e8f',
  CIDADANIA: '#e06fa8',
  AGIR: '#5a7d8c',
  DC: '#b5a642',
  MOBILIZA: '#9c9c4a',
  PMB: '#c76b98',
};

const RESERVA = ['#7a8b99', '#a3876a', '#6f8f72', '#9a7896', '#8c8f5a'];

export function corPartido(sigla: string | null | undefined): string {
  if (!sigla) return '#9a948a';
  const s = sigla.toUpperCase();
  if (CORES[s]) return CORES[s];
  let h = 0;
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return RESERVA[h % RESERVA.length];
}
