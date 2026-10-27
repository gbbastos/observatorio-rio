// Proposições que passaram por votação nominal: junta as votações de cada projeto (projeto, emendas,
// redação final, veto) e traduz cada voto em "a favor" ou "contra" o projeto.
import { bancada, leis, meta, parlamentares, parlamentar, votacoes, votacao,
  type Casa, type Lei, type Proposicao, type Votacao } from './dados';

/** "PLC-44-A/2021" -> "PLC-44/2021": a letra marca o substitutivo, mas o projeto é o mesmo. */
export const chaveProposicao = (id: string) => id.replace(/-[A-Z]+(?=\/)/, '');
/** "PLC-44-A/2021" -> "plc-44-2021", o endereço da página do projeto. */
export const slugProposicao = (id: string) => chaveProposicao(id).toLowerCase().replace(/[^a-z0-9]+/g, '-');

/**
 * O que a votação decide e o que o "sim" quer dizer:
 * - 'projeto': o projeto, o substitutivo ou a redação final; sim = a favor do projeto.
 * - 'veto': veto total (Câmara); sim = manter o veto, ou seja, contra o projeto.
 * - 'veto_parcial': veto a uma parte do projeto, que no resto já virou lei (Câmara); sim = manter o veto.
 * - 'veto_alerj': veto na ALERJ, onde o sim derruba o veto; os dados não dizem se era total ou parcial.
 * - 'emenda': uma mudança no texto; sim = a favor da emenda.
 * Só 'projeto' e 'veto' dizem a posição sobre o projeto inteiro. Total ou parcial sai da frase do
 * resultado ("o veto parcial... está mantido e o dispositivo vetado segue ao arquivo").
 */
export type Sentido = 'projeto' | 'veto' | 'veto_parcial' | 'veto_alerj' | 'emenda' | null;
export function sentidoDoSim(casa: Casa, v: Pick<Votacao, 'objeto' | 'resultado' | 'resultado_frase'>): Sentido {
  switch (v.objeto) {
    case 'projeto': case 'substitutivo': case 'redacao_final': return 'projeto';
    case 'emenda': return 'emenda';
    case 'veto': {
      if (casa !== 'camara') return v.resultado === 'derrubado' || v.resultado === 'mantido' ? 'veto_alerj' : null;
      const frase = v.resultado_frase ?? '';
      if (/parcia|dispositivo/i.test(frase)) return 'veto_parcial';
      if (/veto total|promulga|ao arquivo|e o projeto/i.test(frase)) return 'veto';
      return null;
    }
    default: return null;
  }
}

/** Se a votação diz a posição sobre o projeto inteiro. */
export const dizPosicao = (s: Sentido) => s === 'projeto' || s === 'veto';

/** Código de uma letra ou duas, para os índices lidos no navegador (ver resumoVotos.ts). */
export const CODIGO_SENTIDO: Record<Exclude<Sentido, null>, string> = {
  projeto: 'p', veto: 'v', veto_parcial: 'vp', veto_alerj: 'va', emenda: 'e',
};
export const codigoSentido = (s: Sentido) => (s ? CODIGO_SENTIDO[s] : null);

export type Posicao = 'favor' | 'contra' | 'abstencao' | 'ausente' | 'presidindo';
/** O voto como posição sobre o projeto; null quando o voto não diz (emenda, veto parcial...). */
export function posicaoDoVoto(sentido: Sentido, voto: string): Posicao | null {
  if (voto === 'sim' || voto === 'nao') {
    if (sentido === 'projeto') return voto === 'sim' ? 'favor' : 'contra';
    if (sentido === 'veto') return voto === 'sim' ? 'contra' : 'favor';
    return null;
  }
  return voto === 'abstencao' || voto === 'ausente' || voto === 'presidindo' ? voto : null;
}

/** Quem veta: o prefeito na Câmara, o governador na ALERJ. */
export const quemVeta = (casa: Casa) => (casa === 'camara' ? 'do prefeito' : 'do governador');

/** Frase que explica o voto num veto, para as páginas de votação e de projeto ('' fora dos vetos). */
export function explicaVeto(casa: Casa, sentido: Sentido) {
  const de = quemVeta(casa);
  if (sentido === 'veto') return `Nesta votação do veto total ${de}, quem votou sim manteve o veto (ficou contra o projeto) e quem votou não derrubou o veto (ficou a favor do projeto).`;
  if (sentido === 'veto_parcial') return `Este é um veto parcial ${de}: ele cortou só uma parte do projeto, e o resto virou lei. Quem votou sim manteve o corte; quem votou não queria derrubá-lo. O voto não diz se a pessoa apoia o projeto inteiro.`;
  if (sentido === 'veto_alerj') return `Nesta votação do veto ${de}, quem votou sim derrubou o veto e quem votou não o manteve. Os dados da ALERJ não dizem se o veto era total ou parcial, por isso este voto não entra na conta de a favor e contra o projeto.`;
  return '';
}

/** O que conta como a favor, para as notas do plenário e da ficha (frase sem ponto final). */
export const comoContamos = (casa: Casa) => (casa === 'camara'
  ? `A favor é o sim ao projeto ou o voto que derrubou um veto total ${quemVeta(casa)}; emendas e vetos parciais ficam de fora`
  : 'A favor é o sim ao projeto; emendas e vetos ficam de fora, porque os dados da ALERJ não dizem se um veto era total ou parcial');

/** "emenda", "veto parcial"...: do que foi a votação, quando não foi do projeto inteiro. */
export const ROTULO_PARTE: Record<string, string> = {
  emenda: 'emenda', veto_parcial: 'veto parcial', veto_alerj: 'veto', veto: 'veto', projeto: 'projeto',
};

export interface ProposicaoVotada {
  slug: string;
  /** como a votação mais recente escreve o número (com a letra do substitutivo, se houver) */
  id: string;
  tipo: string | null; ementa: string | null; autores: string[];
  categoria: string | null; tema: string | null;
  /** do mais antigo para o mais recente */
  votacoes: Votacao[];
  /** as votações que dizem a posição sobre o projeto (não emendas) */
  decisivas: Votacao[];
  /** a ficha do projeto, quando o autor é parlamentar (data de protocolo) */
  ficha: Proposicao | null;
  lei: Lei | null;
}

const cache = new Map<Casa, Map<string, ProposicaoVotada>>();

/** Todas as proposições com ao menos uma votação nominal, pelo slug. */
export function proposicoesVotadas(casa: Casa): Map<string, ProposicaoVotada> {
  const pronto = cache.get(casa);
  if (pronto) return pronto;
  const fichas = new Map<string, Proposicao>();
  for (const p of parlamentares(casa)) {
    for (const x of parlamentar(casa, p.slug).lista_proposicoes) fichas.set(slugProposicao(x.id), x);
  }
  const leiDe = new Map<string, Lei>();
  if (meta(casa).tem_leis) for (const l of leis(casa)) if (l.projeto) leiDe.set(slugProposicao(l.projeto), l);

  const r = new Map<string, ProposicaoVotada>();
  // votacoes.json vem da mais recente para a mais antiga (no mesmo dia, a última votada primeiro)
  for (const v of [...votacoes(casa)].reverse()) {
    if (!v.proposicao.id) continue;
    const slug = slugProposicao(v.proposicao.id);
    let p = r.get(slug);
    if (!p) {
      p = { slug, id: v.proposicao.id, tipo: v.proposicao.tipo, ementa: v.proposicao.ementa, autores: v.proposicao.autores,
        categoria: v.proposicao.categoria, tema: v.proposicao.tema, votacoes: [], decisivas: [],
        ficha: fichas.get(slug) ?? null, lei: leiDe.get(slug) ?? null };
      r.set(slug, p);
    }
    p.votacoes.push(v);
    if (dizPosicao(sentidoDoSim(casa, v))) p.decisivas.push(v);
    // a votação mais recente dá o número e o texto
    p.id = v.proposicao.id;
    if (v.proposicao.ementa) p.ementa = v.proposicao.ementa;
    if (v.proposicao.autores.length) p.autores = v.proposicao.autores;
  }
  cache.set(casa, r);
  return r;
}

/** A votação mais recente de um projeto. */
export const ultimaVotacao = (p: ProposicaoVotada) => p.votacoes[p.votacoes.length - 1];

export const simbolica = (p: { categoria: string | null }) => !!p.categoria && p.categoria !== 'normativa';

const PESO: Record<string, number> = { ausente: 1, presidindo: 2, abstencao: 3 };

/**
 * A posição de cada um sobre o projeto: vale o último voto que diz algo (sim ou não nas votações do
 * projeto e do veto); quem só se absteve, presidiu ou faltou fica assim.
 */
export function posicoes(casa: Casa, p: ProposicaoVotada): Map<string, Posicao> {
  const r = new Map<string, Posicao>();
  for (const v of p.decisivas) {
    const s = sentidoDoSim(casa, v);
    for (const [id, voto] of Object.entries(votacao(casa, v.id).votos)) {
      const pos = posicaoDoVoto(s, voto);
      if (!pos) continue;
      const antes = r.get(id);
      if (pos === 'favor' || pos === 'contra' || !antes
          || (antes !== 'favor' && antes !== 'contra' && PESO[pos] > PESO[antes])) r.set(id, pos);
    }
  }
  return r;
}

/** Código de uma letra por posição, para as listas compactas lidas no navegador. */
export const CODIGO_POSICAO: Record<Posicao, string> = { favor: 'f', contra: 'c', abstencao: 'a', ausente: 'x', presidindo: 'p' };

/**
 * Projetos de regras e políticas (não simbólicos) com tema e com voto de quem está hoje na casa: o
 * "como votou" do plenário. Do mais recente para o mais antigo.
 */
export function projetosDoPlenario(casa: Casa) {
  const atuais = bancada(casa).map((p) => p.id);
  const r: { p: ProposicaoVotada; pos: Map<string, Posicao> }[] = [];
  for (const p of proposicoesVotadas(casa).values()) {
    if (!p.decisivas.length || simbolica(p) || !p.tema) continue;
    const pos = posicoes(casa, p);
    if (!atuais.some((id) => pos.get(id) === 'favor' || pos.get(id) === 'contra')) continue;
    r.push({ p, pos });
  }
  return r.sort((a, b) => ultimaVotacao(b.p).data.localeCompare(ultimaVotacao(a.p).data));
}
