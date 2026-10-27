// Resumo dos votos de um parlamentar por projeto, usado na ficha (no build e no navegador, por isso
// não lê os dados). Cada projeto conta uma vez, pelo último voto que diz a posição: sim ou não nas
// votações do projeto e do veto total. Emendas e vetos parciais ficam de fora.

/** Votos em código de uma letra: s (sim), n (não), a (abstenção), x (ausente), p (presidindo). */
export interface VotoNoProjeto {
  slug: string | null;
  /** 'p' (sim = a favor do projeto), 'v' (veto total: sim = manter o veto); o resto não conta */
  sentido: string | null;
  voto: string;
}

const PESO: Record<string, number> = { x: 1, p: 2, a: 3 };

/** Votos da mais antiga para a mais recente; devolve quantos projetos em cada posição. */
export function resumirPorProjeto(votos: VotoNoProjeto[]) {
  const pos = new Map<string, string>();
  for (const v of votos) {
    if (!v.slug || (v.sentido !== 'p' && v.sentido !== 'v')) continue;
    const c = v.voto === 's' || v.voto === 'n'
      ? ((v.voto === 's') === (v.sentido === 'p') ? 'f' : 'c')
      : PESO[v.voto] ? v.voto : null;
    if (!c) continue;
    const antes = pos.get(v.slug);
    if (c === 'f' || c === 'c' || !antes || (antes !== 'f' && antes !== 'c' && PESO[c] > PESO[antes])) pos.set(v.slug, c);
  }
  const cont: Record<string, number> = { f: 0, c: 0, a: 0, x: 0, p: 0 };
  for (const c of pos.values()) cont[c]++;
  return cont;
}

export function textoResumo(cont: Record<string, number>, tema?: string) {
  const nf = (n: number) => n.toLocaleString('pt-BR');
  const partes = [`a favor em ${nf(cont.f)} ${cont.f === 1 ? 'projeto' : 'projetos'}`, `contra em ${nf(cont.c)}`];
  if (cont.a) partes.push(`abstenção em ${nf(cont.a)}`);
  partes.push(`ausente em ${nf(cont.x)}`);
  const t = partes.join(' · ');
  return tema ? `Em ${tema}: ${t}` : t.charAt(0).toUpperCase() + t.slice(1);
}

/**
 * No veto, o que o voto fez: "para derrubar o veto (a favor do projeto)". Sentido em código: 'v' (veto
 * total, sim mantém), 'vp' (veto parcial, sim mantém) ou 'va' (veto na ALERJ, sim derruba).
 */
export function dicaVeto(sentido: string | null, voto: string) {
  if (voto !== 's' && voto !== 'n') return '';
  const mantem = sentido === 'v' || sentido === 'vp' ? voto === 's' : sentido === 'va' ? voto === 'n' : null;
  if (mantem == null) return '';
  if (sentido === 'v') return mantem ? 'para manter o veto (contra o projeto)' : 'para derrubar o veto (a favor do projeto)';
  if (sentido === 'vp') return mantem ? 'para manter o veto parcial' : 'para derrubar o veto parcial';
  return mantem ? 'para manter o veto' : 'para derrubar o veto';
}
