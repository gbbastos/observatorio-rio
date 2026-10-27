// Geometria do plenário em semicírculo: fileiras concêntricas, cadeiras proporcionais ao raio de
// cada fileira, e a ordem da esquerda para a direita por ângulo (assim cada bancada vira uma fatia).

export interface Assento { x: number; y: number; r: number }

export const LARGURA = 200;
export const ALTURA = 104;
const CX = 100;
const CY = 100;
const RAIO_EXTERNO = 96;
const RAIO_INTERNO_PROP = 0.4;

function distribuir(n: number, fileiras: number) {
  const rin = RAIO_INTERNO_PROP;
  const raios = Array.from({ length: fileiras }, (_, i) =>
    fileiras === 1 ? 1 : rin + ((1 - rin) * i) / (fileiras - 1));
  const soma = raios.reduce((a, b) => a + b, 0);
  const qtd = raios.map((r) => Math.max(1, Math.round((n * r) / soma)));
  // acerta o arredondamento pelas fileiras de fora; nunca deixa uma fileira vazia
  let dif = n - qtd.reduce((a, b) => a + b, 0);
  for (let i = fileiras - 1, voltas = 0; dif !== 0 && voltas < 4 * fileiras * (Math.abs(dif) + 1); voltas++, i = (i - 1 + fileiras) % fileiras) {
    if (dif > 0) { qtd[i]++; dif--; } else if (qtd[i] > 1) { qtd[i]--; dif++; }
  }
  return { raios, qtd };
}

/** Escolhe o número de fileiras em que o espaço entre cadeiras na fileira ≈ o espaço entre fileiras. */
function melhorNumeroDeFileiras(n: number): number {
  let melhor = 1;
  let erro = Infinity;
  // cada fileira precisa de pelo menos 2 cadeiras
  for (let f = 1; f <= Math.min(12, Math.max(1, Math.floor(n / 2))); f++) {
    const { raios, qtd } = distribuir(n, f);
    const passoFileira = f === 1 ? 1 - RAIO_INTERNO_PROP : (1 - RAIO_INTERNO_PROP) / (f - 1);
    const passosArco = raios.map((r, i) => (qtd[i] > 1 ? (Math.PI * r) / (qtd[i] - 1) : Math.PI * r));
    const e = Math.abs(Math.log(Math.min(...passosArco) / passoFileira));
    if (e < erro) { erro = e; melhor = f; }
  }
  return melhor;
}

export function layoutPlenario(n: number): Assento[] {
  if (n <= 0) return [];
  const fileiras = melhorNumeroDeFileiras(n);
  const { raios, qtd } = distribuir(n, fileiras);
  const passoFileira = fileiras === 1 ? 0.3 : (1 - RAIO_INTERNO_PROP) / (fileiras - 1);
  const passoArco = Math.min(...raios.map((r, i) => (qtd[i] > 1 ? (Math.PI * r) / (qtd[i] - 1) : 1)));
  const raioCadeira = 0.46 * Math.min(passoFileira, passoArco) * RAIO_EXTERNO;

  const pontos: { x: number; y: number; ang: number; fila: number }[] = [];
  raios.forEach((rel, fila) => {
    const r = rel * (RAIO_EXTERNO - raioCadeira);
    for (let j = 0; j < qtd[fila]; j++) {
      const ang = qtd[fila] === 1 ? Math.PI / 2 : Math.PI * (1 - j / (qtd[fila] - 1));
      pontos.push({ x: CX + r * Math.cos(ang), y: CY - r * Math.sin(ang), ang, fila });
    }
  });
  pontos.sort((a, b) => b.ang - a.ang || a.fila - b.fila);
  return pontos.map(({ x, y }) => ({ x: +x.toFixed(2), y: +y.toFixed(2), r: +raioCadeira.toFixed(2) }));
}

/** Ordena as cadeiras: bancadas da maior para a menor, e dentro de cada uma por nome. */
export function ordenarPorBancada<T>(itens: T[], partidoDe: (x: T) => string, nomeDe: (x: T) => string): T[] {
  const tamanho = new Map<string, number>();
  for (const i of itens) tamanho.set(partidoDe(i), (tamanho.get(partidoDe(i)) ?? 0) + 1);
  return [...itens].sort((a, b) =>
    (tamanho.get(partidoDe(b))! - tamanho.get(partidoDe(a))!) ||
    partidoDe(a).localeCompare(partidoDe(b)) ||
    nomeDe(a).localeCompare(nomeDe(b), 'pt-BR'));
}
