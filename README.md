# Fez o quê?

Observatório da Câmara Municipal do Rio e da ALERJ. A pergunta é simples: quando um parlamentar diz
que “aprovou 100 leis”, quantas são de verdade e quantas são nome de rua, data comemorativa,
utilidade pública, patrimônio ou homenagem?

O site mostra, para cada vereador e deputado estadual:

- as leis aprovadas (Câmara) e os projetos de lei protocolados (Câmara e ALERJ), classificados pela
  ementa: as cinco categorias simbólicas e, no resto ("regras e políticas"), o tema (saúde, educação,
  transporte...); na Câmara, cada projeto que virou lei aponta para a lei;
- tudo separado por mandato, para quem passou por mais de uma legislatura (na Câmara, as leis vão
  até 2017; projetos, votações e presença, até 2021);
- como votou em cada votação nominal e os pedidos de informação ao Executivo, filtráveis por tema;
  o voto vira "a favor" ou "contra o projeto" (na Câmara, o sim ao veto é contra o projeto), e cada
  projeto votado tem uma página com quem foi a favor e quem foi contra;
- o **peso real** da autoria (uma lei com 20 coautores vale 1/20 para cada um);
- requerimentos de informação (fiscalização), títulos e medalhas, moções;
- presença e votos nas votações nominais;
- o plenário em semicírculo, colorido por partido, por produção simbólica, por presença ou por como
  cada um votou num tema (e, dentro dele, num projeto).

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
  sobre a ementa (concordam com as listas da Câmara em 98% das leis). O tema das leis e projetos que
  não são simbólicos sai de `pipeline/observatorio/temas.py` (palavras-chave por tema; ganha o tema
  com mais palavras na ementa).
- `site/` é um site estático em [Astro](https://astro.build): uma página por parlamentar e por votação.

## Rodar na máquina

Pré-requisitos: Python 3.12+, Node 22+, Git.

```bash
git submodule update --init

# 1. coleta da Tomoyo (a primeira vez leva ~1 h por casa, a 1 pedido por segundo; depois é incremental)
#    no Windows, rode com PYTHONUTF8=1: sem isso o Python grava os arquivos em cp1252 e a coleta quebra no fim
export PYTHONUTF8=1
cd vendor/como-votou/backend
python -m venv .venv && .venv/Scripts/pip install -e .      # no Linux/Mac: .venv/bin/pip
.venv/Scripts/python -m app.etl.export_snapshot --all
.venv/Scripts/python -m app.etl.export_static_frontend
cd ../../..
# (ALERJ: o mesmo em vendor/assembleias/backend com --uf RJ; os dados de 15/10 já vêm no repositório)

# 2. leis da Câmara e montagem dos dados do site
cd pipeline
python -m observatorio.coletar          # ~1 h na primeira vez (uma ficha por lei, desde 2017); depois só as novas
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

`python -m observatorio.resumir` (ou `atualizar.ps1`, quando `ANTHROPIC_API_KEY` existe) resume em linguagem simples as leis que não são simbólicas
(~1.100 desde 2021), uma vez cada, e guarda em `data/cache/resumos.json` (versionado, para não pagar
de novo). Usa a Message Batches API da Anthropic (metade do preço) e precisa de `pip install -r
pipeline/requirements-ia.txt` e de `ANTHROPIC_API_KEY`. O modelo padrão é `claude-opus-5-5`;
`RESUMO_MODELO=claude-haiku-5-5` é bem mais barato. Rode `--estimar` para ver quantas faltam e
`--limite 20` para testar antes.

## Atualizar e publicar

Site no ar: https://gbbastos.github.io/observatorio-rio/

Os servidores da Câmara do Rio não respondem às máquinas do GitHub, então a coleta roda aqui e o
GitHub só constrói e publica. Um comando faz tudo (coleta, monta, commita os dados e dá push):

```powershell
.\atualizar.ps1                 # Câmara e ALERJ
.\atualizar.ps1 -PularALERJ     # só a Câmara (a primeira coleta da ALERJ leva horas)
.\atualizar.ps1 -SemPublicar    # atualiza os dados locais sem dar push
```

Cada push na `main` dispara `.github/workflows/publicar.yml`, que constrói o site a partir de
`site/src/data/` (versionado) e publica no GitHub Pages. O push usa a conta do GitHub CLI guardada
no cofre do Windows, ignorando o `GITHUB_TOKEN` do ambiente.

Para rodar sozinho a cada dois dias, dá para agendar `atualizar.ps1 -PularALERJ` no Agendador de
Tarefas do Windows (o computador precisa estar ligado no horário).

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
