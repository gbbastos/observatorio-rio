// Índice compacto das votações nominais de uma casa, lido pela seção "Como votou" das fichas: cada
// ficha guarda só a posição da votação neste índice e o voto. O navegador baixa o índice uma vez.
import type { APIRoute } from 'astro';
import { casasDisponiveis, votacoes, type Casa } from '../../lib/dados';
import { ementa } from '../../lib/formatar';
import { codigoSentido, sentidoDoSim, slugProposicao } from '../../lib/proposicoes';

export function getStaticPaths() {
  return casasDisponiveis().map((casa) => ({ params: { casa } }));
}

/**
 * [id, data, proposição, ementa, objeto, categoria, tema, legislatura, sentido do sim, slug do projeto]
 * na ordem de votacoes(casa). Sentido em código (ver CODIGO_SENTIDO): 'p' projeto, 'v' veto total,
 * 'vp' veto parcial, 'va' veto na ALERJ, 'e' emenda, ou null.
 */
export const GET: APIRoute = ({ params }) => {
  const casa = params.casa as Casa;
  const linhas = votacoes(casa).map((v) => [
    v.id, v.data, v.proposicao.id, ementa(v.proposicao.ementa), v.objeto, v.proposicao.categoria,
    v.proposicao.tema, v.legislatura == null ? null : Number(v.legislatura),
    codigoSentido(sentidoDoSim(casa, v)), v.proposicao.id ? slugProposicao(v.proposicao.id) : null,
  ]);
  return new Response(JSON.stringify(linhas), { headers: { 'Content-Type': 'application/json' } });
};
