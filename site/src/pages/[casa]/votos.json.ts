// Índice compacto das votações nominais de uma casa, lido pela seção "Como votou" das fichas: cada
// ficha guarda só a posição da votação neste índice e o voto. O navegador baixa o índice uma vez.
import type { APIRoute } from 'astro';
import { casasDisponiveis, votacoes, type Casa } from '../../lib/dados';
import { ementa } from '../../lib/formatar';

export function getStaticPaths() {
  return casasDisponiveis().map((casa) => ({ params: { casa } }));
}

/** [id, data, proposição, ementa, objeto, categoria, tema, legislatura] na ordem de votacoes(casa) */
export const GET: APIRoute = ({ params }) => {
  const linhas = votacoes(params.casa as Casa).map((v) => [
    v.id, v.data, v.proposicao.id, ementa(v.proposicao.ementa), v.objeto, v.proposicao.categoria,
    v.proposicao.tema, v.legislatura == null ? null : Number(v.legislatura),
  ]);
  return new Response(JSON.stringify(linhas), { headers: { 'Content-Type': 'application/json' } });
};
