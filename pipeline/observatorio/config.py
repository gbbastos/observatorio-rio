"""Caminhos e fontes do pipeline."""
from __future__ import annotations

from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
RAIZ = PIPELINE_DIR.parent
DATA_DIR = RAIZ / "data"
RAW_DIR = DATA_DIR / "raw"            # respostas brutas (cache, fora do git)
CACHE_DIR = DATA_DIR / "cache"        # resultados caros de refazer (resumos de IA)
SITE_DATA_DIR = RAIZ / "site" / "src" / "data"
SITE_PUBLIC_DIR = RAIZ / "site" / "public"

VENDOR = RAIZ / "vendor"
COMO_VOTOU = VENDOR / "como-votou"
ASSEMBLEIAS = VENDOR / "assembleias"
CA_BUNDLE = COMO_VOTOU / "backend" / "app" / "cabundle.pem"

USER_AGENT = "observatorio-rio (projeto pessoal de dados publicos)"
INTERVALO_S = 1.0
TIMEOUT_S = 120.0

# Câmara Municipal do Rio: base de legislação (Lotus Domino).
CONTLEI = "https://aplicnt.camara.rj.gov.br/APL/Legislativos/contlei.nsf"
VISOES_LEIS = {
    # tipo de norma -> visão com todas as normas daquele tipo
    "LEI": "7cb7d306c2b748cb0325796000610ad8",
    "LC": "a99e317a9cfec383032568620071f5d2",
    "DL": "1103082e25d77b2203256500004ddfd5",
    "RES": "803720d56d09c0e70325663200757b59",
}
VISOES_TEMAS = {
    # a própria Câmara separa estas leis ordinárias em listas temáticas
    "logradouro": "5f9bf440c7e16437032579640061d978",
    "calendario": "51f10ce23366abed032579640061be91",
    "utilidade_publica": "111e7b2098e20dc0032579640060e98a",
}

ANO_INICIAL = 2021   # início da 11ª legislatura, o mesmo recorte da Tomoyo
