const base = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Caminho interno com a base do deploy ("/camara/x/" -> "/observatorio-rio/camara/x/"). */
export const u = (caminho: string) => `${base}${caminho.startsWith('/') ? caminho : `/${caminho}`}`;

export const num = (n: number | null | undefined, casas = 0) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas });

export const pct = (parte: number, todo: number) => (todo ? Math.round((100 * parte) / todo) : 0);

export const pctTaxa = (taxa: number | null | undefined) => (taxa == null ? '—' : `${Math.round(taxa * 100)}%`);

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const MESES_LONGOS = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
  'setembro', 'outubro', 'novembro', 'dezembro'];

export const dataCurta = (iso: string | null | undefined) => {
  if (!iso) return '';
  const [a, m, d] = iso.slice(0, 10).split('-').map(Number);
  return `${d} ${MESES[m - 1]} ${a}`;
};

/** Datas com hora (carimbos de atualização, em UTC) viram a data no horário do Rio. */
export const dataLonga = (iso: string) => {
  const dia = iso.length > 10
    ? new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(new Date(iso))
    : iso;
  const [a, m, d] = dia.split('-').map(Number);
  return `${d} de ${MESES_LONGOS[m - 1]} de ${a}`;
};

/** "PL-758/2025" -> "PL 758/2025"; "LEI-9672/2026" -> "Lei 9.672/2026". */
export const rotuloNorma = (id: string) => {
  const i = id.indexOf('-');
  const tipo = id.slice(0, i);
  const [numero, ano] = id.slice(i + 1).split('/');
  const n = /^\d+$/.test(numero) ? Number(numero).toLocaleString('pt-BR') : numero;
  const nome: Record<string, string> = { LEI: 'Lei', LC: 'Lei Compl.', DL: 'Decreto Leg.', RES: 'Resolução' };
  return `${nome[tipo] ?? tipo} ${n}/${ano}`;
};

/** Ementas do SPL vêm em caixa alta; passa para caixa de frase. */
export const ementa = (texto: string | null | undefined) => {
  if (!texto) return '';
  const letras = texto.replace(/[^A-Za-zÀ-ÿ]/g, '');
  const maiusculas = letras.replace(/[^A-ZÀ-Þ]/g, '').length;
  if (letras.length && maiusculas / letras.length < 0.8) return texto;
  const t = texto.toLowerCase();
  return (t.charAt(0).toUpperCase() + t.slice(1)).replace(/\brio de janeiro\b/g, 'Rio de Janeiro');
};

export const ROTULO_CURTO: Record<string, string> = {
  logradouro: 'Nome de rua',
  calendario: 'Data comemorativa',
  utilidade_publica: 'Utilidade pública',
  patrimonio: 'Patrimônio / polo',
  honraria: 'Homenagem',
  normativa: 'Demais leis',
};

export const ROTULO_VOTO: Record<string, string> = {
  sim: 'Sim', nao: 'Não', abstencao: 'Abstenção', ausente: 'Ausente', presidindo: 'Presidindo',
};
