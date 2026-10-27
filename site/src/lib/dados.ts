// Leitura dos JSON gerados por pipeline/observatorio/montar.py (um diretório por casa legislativa).

export type Casa = 'camara' | 'alerj';

export interface Categoria { rotulo: string; simbolica: boolean }

export interface ResumoLeis {
  total: number;
  simbolicas: number;
  por_categoria: Record<string, number>;
}

export interface Meta {
  casa: Casa;
  nome: string;
  curto: string;
  membro: string;
  membros: string;
  cadeiras: number;
  legislatura_atual: { numero: number; inicio: string; fim: string };
  ano_inicial: number;
  /** false quando a casa não tem base de leis aprovadas (ALERJ): o site mostra os projetos apresentados */
  tem_leis: boolean;
  atualizado_em: string;
  categorias: Record<string, Categoria>;
  leis: ResumoLeis;
  leis_legislatura: ResumoLeis;
  leis_por_ano: Record<string, ResumoLeis>;
  projetos: ResumoLeis;
  projetos_por_ano: Record<string, ResumoLeis>;
  titulos: number;
  votacoes: number;
  fontes: { nome: string; url: string }[];
}

export interface Parlamentar {
  id: string;
  slug: string;
  nome: string;
  nome_civil?: string;
  partido: string | null;
  partidos_por_legislatura: Record<string, string | null>;
  em_exercicio: boolean;
  legislaturas: number[];
  foto: string | null;
  email?: string | null;
  perfil_url?: string | null;
  leis: {
    total: number; simbolicas: number; por_categoria: Record<string, number>;
    peso: number; peso_normativas: number; sozinho: number; em_grupo: number;
  };
  titulos: number;
  proposicoes: {
    por_tipo: Record<string, number>; pl: number; pl_simbolicos: number; pl_por_categoria: Record<string, number>;
    honrarias: number; reqinf: number; indicacoes: number; mocoes: number; ultima: string | null;
  };
  votacoes: {
    sim?: number; nao?: number; abstencao?: number; ausente?: number; presidindo?: number;
    participacao?: number | null; com_maioria?: number | null; contra_partido?: number | null; contra_partido_taxa?: number | null;
  };
  presenca: Record<string, { faltas: number; abonadas: number; total: number; meses: number }>;
}

export interface LeiResumo {
  id: string; tipo: string; numero: number; ano: number; data: string | null; ementa: string;
  categoria: string; simbolica: boolean; status: string | null; n_autores: number; url: string;
  resumo: string | null; coautores: string[];
}

export interface Proposicao {
  id: string; tipo: string; data: string | null; ementa: string; categoria: string | null;
  simbolica: boolean | null; coautores: number;
}

export interface ParlamentarDetalhe extends Parlamentar {
  lista_leis: LeiResumo[];
  lista_proposicoes: Proposicao[];
  lista_votos: { id: string; voto: string }[];
}

export interface Autor { id?: string; slug?: string; nome: string; inst?: boolean }

export interface Lei {
  id: string; tipo: string; numero: number; ano: number; data: string | null; ementa: string;
  categoria: string; simbolica: boolean; status: string | null; projeto: string | null; forma: string | null;
  autores: Autor[]; n_autores: number; url: string; resumo: string | null;
}

export interface Votacao {
  id: string; data: string; legislatura: number | null;
  sessao: { tipo?: string; numero?: string; fase?: string };
  proposicao: { id: string | null; tipo: string | null; ementa: string | null; autores: string[]; categoria: string | null };
  objeto: string | null; resultado: string | null; resultado_frase: string | null;
  contagem: { sim: number; nao: number; abstencao: number; presentes_votando?: number } | null;
  lado_vencedor: string | null; fonte: string | null;
}

export interface VotacaoDetalhe extends Votacao {
  votos: Record<string, string>;
  presidente: string | null;
}

type Modulos<T> = Record<string, { default: T }>;

const metas = import.meta.glob('../data/*/meta.json', { eager: true }) as Modulos<Meta>;
const listas = import.meta.glob('../data/*/parlamentares.json', { eager: true }) as Modulos<Parlamentar[]>;
const detalhes = import.meta.glob('../data/*/parlamentares/*.json', { eager: true }) as Modulos<ParlamentarDetalhe>;
const leisMod = import.meta.glob('../data/*/leis.json', { eager: true }) as Modulos<Lei[]>;
const votacoesMod = import.meta.glob('../data/*/votacoes.json', { eager: true }) as Modulos<Votacao[]>;
const votacaoDet = import.meta.glob('../data/*/votacoes/*.json', { eager: true }) as Modulos<VotacaoDetalhe>;

const caminho = (casa: string, arquivo: string) => `../data/${casa}/${arquivo}`;

export const casasDisponiveis = (): Casa[] =>
  Object.keys(metas).map((k) => k.split('/')[2] as Casa).sort((a) => (a === 'camara' ? -1 : 1));

export const meta = (casa: Casa): Meta => metas[caminho(casa, 'meta.json')].default;
export const parlamentares = (casa: Casa): Parlamentar[] => listas[caminho(casa, 'parlamentares.json')].default;
export const parlamentar = (casa: Casa, slug: string): ParlamentarDetalhe =>
  detalhes[caminho(casa, `parlamentares/${slug}.json`)].default;
export const leis = (casa: Casa): Lei[] => leisMod[caminho(casa, 'leis.json')].default;
export const votacoes = (casa: Casa): Votacao[] => votacoesMod[caminho(casa, 'votacoes.json')].default;
export const votacao = (casa: Casa, id: string): VotacaoDetalhe => votacaoDet[caminho(casa, `votacoes/${id}.json`)].default;

export const porId = (casa: Casa): Map<string, Parlamentar> => new Map(parlamentares(casa).map((p) => [p.id, p]));

/** Bancada atual: quem está em exercício. */
export const bancada = (casa: Casa): Parlamentar[] => parlamentares(casa).filter((p) => p.em_exercicio);
