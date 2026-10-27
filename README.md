# Fez o quê?

Observatório da Câmara Municipal do Rio e da ALERJ. A pergunta é simples: quando um parlamentar diz
que “aprovou 100 leis”, quantas são de verdade e quantas são nome de rua, data comemorativa,
utilidade pública, patrimônio ou homenagem?

O site mostra, para cada vereador e deputado estadual:

- as leis aprovadas (Câmara) ou os projetos apresentados (ALERJ), classificados pela ementa;
- o **peso real** da autoria (uma lei com 20 coautores vale 1/20 para cada um);
- requerimentos de informação (fiscalização), títulos e medalhas, moções;
- presença e votos nas votações nominais;
- o plenário em semicírculo, colorido por partido, por produção simbólica, por presença ou por uma votação.

Nome provisório: trocar em `site/src/lib/site.ts` e no logo em `site/src/layouts/Base.astro`.

## Como funciona

```
fontes públicas ──► vendor/como-votou   (Tomoyo: vereadores, proposições, votações, presença)
                ──► vendor/assembleias  (Tomoyo: o mesmo para a ALERJ)
                ──► pipeline/coletar    (nosso: base de leis da Câmara, contlei.nsf)
                         │
                pipeline/montar  ──► site/src/data/<casa>/*.json  ──► site (Astro, estático)
                pipeline/resumir (opcional, IA) ─┘
```

- `vendor/` são submódulos com os projetos abertos da
  [Tomoyo](https://github.com/Tomoyo-Computer-Science-Research-Unit) (licença MIT). A coleta deles
  resolve a parte difícil: bases Lotus Domino, atas, Diário Oficial em PDF e casamento de nomes.
- `pipeline/` (Python, só biblioteca padrão) lê a base de leis da Câmara, classifica cada lei e
  monta os JSON do site. A classificação está em `pipeline/observatorio/classificar.py`: para nome
  de rua, calendário e utilidade pública usa as listas temáticas da própria Câmara; no resto, regras
  sobre a ementa (concordam com as listas da Câmara em 98% das leis).
- `site/` é um site estático em [Astro](https://astro.build): uma página por parlamentar e por votação.

## Rodar na máquina

Pré-requisitos: Python 3.12+, Node 22+, Git.

```bash
git submodule update --init

# 1. coleta da Tomoyo (a primeira vez leva ~1 h por casa, a 1 pedido por segundo; depois é incremental)
cd vendor/como-votou/backend
python -m venv .venv && .venv/Scripts/pip install -e .      # no Linux/Mac: .venv/bin/pip
.venv/Scripts/python -m app.etl.export_snapshot --all
.venv/Scripts/python -m app.etl.export_static_frontend
cd ../../..
# (ALERJ: o mesmo em vendor/assembleias/backend com --uf RJ; os dados de 15/10 já vêm no repositório)

# 2. leis da Câmara e montagem dos dados do site
cd pipeline
python -m observatorio.coletar          # ~50 min na primeira vez (uma ficha por lei); depois só as novas
python -m observatorio.montar
cd ..

# 3. site
cd site
npm install
npm run dev                             # http://localhost:4321
npm run build                           # gera site/dist
```

Sem pressa? `python -m observatorio.coletar --sem-fichas` pula as fichas (o site sai sem a data
exata de cada lei e sem o texto para os resumos).

### Resumos por IA (opcional)

`python -m observatorio.resumir` resume em linguagem simples as leis que não são simbólicas
(~1.100 desde 2021), uma vez cada, e guarda em `data/cache/resumos.json` (versionado, para não pagar
de novo). Usa a Message Batches API da Anthropic (metade do preço) e precisa de `pip install -r
pipeline/requirements-ia.txt` e de `ANTHROPIC_API_KEY`. O modelo padrão é `claude-opus-5-5`;
`RESUMO_MODELO=claude-haiku-5-5` é bem mais barato. Rode `--estimar` para ver quantas faltam e
`--limite 20` para testar antes.

## Publicar

`.github/workflows/atualizar.yml` roda a cada dois dias: coleta, monta, constrói e publica no
GitHub Pages. Para ligar:

1. criar o repositório no GitHub e dar push (com os submódulos);
2. em *Settings → Pages*, escolher **GitHub Actions** como origem;
3. (opcional) em *Settings → Secrets*, criar `ANTHROPIC_API_KEY` para os resumos;
4. rodar o workflow uma vez em *Actions → Atualizar dados e publicar → Run workflow*.

## Limites conhecidos

- **ALERJ sem leis aprovadas.** A base de legislação da ALERJ (`alerjln1.alerj.rj.gov.br/contlei.nsf`)
  recusa consultas automáticas às listas de leis, e o site não contorna isso. Por enquanto a ALERJ
  aparece com os projetos apresentados. O caminho é um pedido pela Lei de Acesso à Informação
  (fala.br / ouvidoria da ALERJ) pela base de leis com autoria em CSV.
- **Presença por sessão** não é publicada nem pela Câmara nem pela ALERJ; o site mostra as faltas
  mensais e a presença nas votações nominais.
- **Votações simbólicas** (a maioria) não registram quem votou o quê.
- A classificação lê só a ementa; ementas vagas podem cair na categoria errada.

## Créditos

Coleta de vereadores, deputados, proposições, votações e presença:
[Tomoyo / como-votou e assembleias](https://github.com/Tomoyo-Computer-Science-Research-Unit), licença MIT.
