// Ordem e cor das categorias: tons de ocre para as simbólicas, azul para regras e políticas. Nada de
// vermelho: a cor não deve sugerir que homenagem é "ruim", só separar uma coisa da outra.
export const ORDEM_CATEGORIAS = ['calendario', 'patrimonio', 'logradouro', 'utilidade_publica', 'honraria', 'normativa'];

export const COR_CATEGORIA: Record<string, string> = {
  calendario: 'var(--cat-calendario)',
  patrimonio: 'var(--cat-patrimonio)',
  logradouro: 'var(--cat-logradouro)',
  utilidade_publica: 'var(--cat-utilidade)',
  honraria: 'var(--cat-honraria)',
  normativa: 'var(--cat-regras)',
};

/** O que entra em cada categoria, em uma ou duas frases (glossário da ficha e página de método). */
export const DEFINICAO_CATEGORIA: Record<string, string> = {
  calendario: 'Cria um dia, semana ou mês comemorativo, ou põe um evento no calendário oficial. Não obriga ninguém a nada.',
  patrimonio: 'Declara algo patrimônio cultural, histórico ou imaterial, cria polo gastronômico ou cultural, ou põe um lugar no roteiro turístico. É reconhecimento, sem verba nem regra nova (o tombamento, que tem efeito sobre o imóvel, também entra aqui).',
  logradouro: 'Dá ou troca o nome de rua, praça, escola, túnel, hospital ou outro lugar público.',
  utilidade_publica: 'Declara uma associação, ONG ou instituto “de utilidade pública”. É um título que ajuda a entidade a conseguir convênios e isenções, mas não cria política pública.',
  honraria: 'Título de cidadão honorário, medalha, diploma, prêmio ou cidade-irmã.',
  normativa: 'Tudo que não cai nas cinco acima: cria programa, regra, obrigação, direito, imposto ou cargo, ou muda uma lei. Inclui campanhas de conscientização e leis que só “autorizam” o governo a fazer algo, que podem ter pouco efeito prático. Por isso aparecem separadas por tema.',
};

/** Temas das regras e políticas, na ordem dos filtros quando empatam. */
export const ORDEM_TEMAS = ['saude', 'educacao', 'direitos', 'transporte', 'seguranca', 'ambiente', 'urbanismo',
  'economia', 'cultura', 'tributos', 'administracao', 'outros'];

/** Tema no meio de uma frase ("sobretudo saúde, urbanismo e transporte"). */
export const TEMA_FRASE: Record<string, string> = {
  saude: 'saúde', educacao: 'educação', direitos: 'direitos sociais', transporte: 'transporte',
  seguranca: 'segurança', ambiente: 'meio ambiente', urbanismo: 'urbanismo', economia: 'economia',
  cultura: 'cultura', tributos: 'finanças públicas', administracao: 'administração pública',
};

export const ROTULO_TEMA: Record<string, string> = {
  saude: 'Saúde',
  educacao: 'Educação',
  direitos: 'Direitos e assistência',
  transporte: 'Transporte e trânsito',
  seguranca: 'Segurança e defesa civil',
  ambiente: 'Meio ambiente e animais',
  urbanismo: 'Obras e urbanismo',
  economia: 'Comércio e trabalho',
  cultura: 'Cultura e esporte',
  tributos: 'Impostos e orçamento',
  administracao: 'Governo e servidores',
  outros: 'Outros',
};

/** Escala do "quanto da produção é simbólica": azul (quase tudo regra e política) a ocre (quase tudo
 *  simbólico), passando por cinza. Cores fixas: servem nos dois temas e no SVG do plenário. */
export function corSimbolica(fracao: number): string {
  const paradas = ['#2f5d8a', '#5f7d9c', '#9a958c', '#bf9142', '#c9851a'];
  const i = Math.min(paradas.length - 1, Math.max(0, Math.round(fracao * (paradas.length - 1))));
  return paradas[i];
}

/** Escala de presença nas votações nominais: claro = pouco, escuro = muito. */
export function corPresenca(taxa: number): string {
  const paradas = ['#f2b6a8', '#d9b48a', '#9fae8c', '#4f8a6a', '#1f5c45'];
  const i = Math.min(paradas.length - 1, Math.max(0, Math.floor(taxa * paradas.length)));
  return paradas[i];
}
