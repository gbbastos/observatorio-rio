<#
.SYNOPSIS
  Atualiza os dados do observatório e publica o site.

.DESCRIPTION
  Roda na máquina local porque os sites da Câmara do Rio não respondem aos servidores do GitHub.
  1. coleta da Tomoyo (Câmara e, se não for pulada, ALERJ), só o que mudou desde a última vez;
  2. leis da Câmara (fichas novas), resumos por IA se ANTHROPIC_API_KEY existir, testes e montagem;
  3. commit dos dados em site/src/data e push; o GitHub constrói e publica sozinho.

  O push usa a conta do GitHub CLI guardada no cofre do Windows (gbbastos), ignorando o
  GITHUB_TOKEN do ambiente só durante o push.

.EXAMPLE
  .\atualizar.ps1                 # tudo
  .\atualizar.ps1 -PularALERJ     # só a Câmara (a primeira coleta da ALERJ leva horas)
  .\atualizar.ps1 -SemPublicar    # atualiza os dados locais e não dá push
#>
param(
  [switch]$PularALERJ,
  [switch]$SemPublicar
)

$ErrorActionPreference = 'Continue'
$raiz = $PSScriptRoot
$env:PYTHONUTF8 = '1'          # sem isso a coleta da Tomoyo grava em cp1252 e quebra
$env:PYTHONIOENCODING = 'utf-8'

function Passo([string]$titulo) { Write-Host "`n== $titulo" -ForegroundColor Cyan }

function Rodar([string]$pasta, [string]$exe, [string[]]$argumentos) {
  Push-Location $pasta
  try {
    & $exe @argumentos
    if ($LASTEXITCODE -ne 0) { throw "falhou ($LASTEXITCODE): $exe $($argumentos -join ' ')" }
  } finally { Pop-Location }
}

function Venv([string]$backend) {
  $py = Join-Path $backend '.venv\Scripts\python.exe'
  if (-not (Test-Path $py)) {
    Write-Host "criando ambiente Python em $backend"
    python -m venv (Join-Path $backend '.venv')
    & $py -m pip install -q -e $backend
    if ($LASTEXITCODE -ne 0) { throw "não instalou as dependências de $backend" }
  }
  return $py
}

$inicio = Get-Date

Passo 'Câmara do Rio (Tomoyo)'
$backend = Join-Path $raiz 'vendor\como-votou\backend'
$py = Venv $backend
Rodar $backend $py @('-m', 'app.etl.export_snapshot', '--all')
Rodar $backend $py @('-m', 'app.etl.export_static_frontend')

if (-not $PularALERJ) {
  Passo 'ALERJ (Tomoyo)'
  $backend = Join-Path $raiz 'vendor\assembleias\backend'
  try {
    $py = Venv $backend
    Rodar $backend $py @('-m', 'app.etl.export_snapshot', '--uf', 'RJ', '--all')
    Rodar $backend $py @('-m', 'app.etl.export_static_frontend', '--uf', 'RJ')
  } catch {
    Write-Warning "A coleta da ALERJ falhou ($_); o site segue com o último dado da ALERJ."
  }
}

$pipeline = Join-Path $raiz 'pipeline'

Passo 'Leis da Câmara'
Rodar $pipeline 'python' @('-m', 'observatorio.coletar')

if ($env:ANTHROPIC_API_KEY) {
  Passo 'Resumos por IA'
  python -m pip install -q -r (Join-Path $pipeline 'requirements-ia.txt')
  Rodar $pipeline 'python' @('-m', 'observatorio.resumir')
}

Passo 'Testes e montagem'
Rodar $pipeline 'python' @('-m', 'unittest', '-q')
Rodar $pipeline 'python' @('-m', 'observatorio.montar')

if ($SemPublicar) {
  Write-Host "`nDados atualizados em site\src\data (sem publicar)." -ForegroundColor Green
  return
}

Passo 'Publicar'
$caminhos = @('site/src/data', 'site/public/fotos')
if (Test-Path (Join-Path $raiz 'data\cache\resumos.json')) { $caminhos += 'data/cache/resumos.json' }
git -C $raiz add -- $caminhos
git -C $raiz diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host 'Nada mudou desde a última publicação.' -ForegroundColor Green
  return
}
git -C $raiz commit -q -m "dados: atualização de $(Get-Date -Format 'yyyy-MM-dd')"

$tokenDoTrabalho = $env:GITHUB_TOKEN
Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
try {
  git -C $raiz -c credential.helper= -c 'credential.helper=!gh auth git-credential' push
  if ($LASTEXITCODE -ne 0) { throw 'o push falhou' }
} finally {
  if ($tokenDoTrabalho) { $env:GITHUB_TOKEN = $tokenDoTrabalho }
}

$minutos = [math]::Round(((Get-Date) - $inicio).TotalMinutes)
Write-Host "`nPronto em $minutos min. O GitHub publica em alguns minutos: https://gbbastos.github.io/observatorio-rio/" -ForegroundColor Green
