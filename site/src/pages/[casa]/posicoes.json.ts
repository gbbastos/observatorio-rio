// "Como votou" do plenário da página inicial: para cada projeto de regras e políticas votado de forma
// nominal, a posição de cada cadeira de hoje (a favor, contra...). O navegador só baixa quando a pessoa
// escolhe esse modo do plenário.
import type { APIRoute } from 'astro';
import { bancada, casasDisponiveis, type Casa } from '../../lib/dados';
import { ementa, rotuloNorma } from '../../lib/formatar';
import { CODIGO_POSICAO, projetosDoPlenario, ultimaVotacao } from '../../lib/proposicoes';

export function getStaticPaths() {
  return casasDisponiveis().map((casa) => ({ params: { casa } }));
}

/**
 * { ids: [id de cada cadeira], projetos: [[slug, número, ementa, tema, data da última votação,
 *   posições]] }. As posições são uma letra por id, na ordem de ids: f (a favor), c (contra),
 * a (abstenção), x (ausente), p (presidindo) ou - (não votou: ainda não estava na casa).
 */
export const GET: APIRoute = ({ params }) => {
  const casa = params.casa as Casa;
  const ids = bancada(casa).map((p) => p.id);
  const projetos = projetosDoPlenario(casa).map(({ p, pos }) => {
    const texto = ementa(p.ementa);
    return [
      p.slug, rotuloNorma(p.id), texto.length > 140 ? `${texto.slice(0, 137).trimEnd()}…` : texto, p.tema,
      ultimaVotacao(p).data, ids.map((id) => { const x = pos.get(id); return x ? CODIGO_POSICAO[x] : '-'; }).join(''),
    ];
  });
  return new Response(JSON.stringify({ ids, projetos }), { headers: { 'Content-Type': 'application/json' } });
};
