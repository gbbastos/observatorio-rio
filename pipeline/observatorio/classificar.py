"""Classificação de leis e projetos pela ementa.

Quando a própria Câmara já pôs a lei numa lista temática (logradouro, calendário, utilidade
pública), vale a lista dela; no resto, regras sobre a ementa. Tudo que não cai numa categoria
simbólica fica como "normativa": a regra só afirma o que a ementa diz com todas as letras.
"""
from __future__ import annotations

import re
import unicodedata

CATEGORIAS = {
    "logradouro": {"rotulo": "Nome de rua ou lugar", "simbolica": True},
    "calendario": {"rotulo": "Data comemorativa", "simbolica": True},
    "utilidade_publica": {"rotulo": "Utilidade pública", "simbolica": True},
    "patrimonio": {"rotulo": "Patrimônio, polo e roteiro", "simbolica": True},
    "honraria": {"rotulo": "Título, medalha e homenagem", "simbolica": True},
    "normativa": {"rotulo": "Demais leis", "simbolica": False},
}

_LUGAR = (r"logradouro|rua|pra[cç]a|travessa|avenida|estrada|alameda|largo|beco|vila|viaduto|t[uú]nel|"
          r"passarela|ponte|parque|jardim|bosque|escola|creche|ciep|unidade|hospital|cl[ií]nica|"
          r"pr[oó]prio|espa[cç]o|centro|complexo|quadra|campo|est[aá]dio|gin[aá]sio|biblioteca|"
          r"esta[cç][aã]o|terminal|mirante|areninha|arena|lona|nave|plenario|plen[aá]rio|sala|audit[oó]rio|"
          r"via|caminho|ciclovia|rotat[oó]ria|elevado|trecho|area|[aá]rea de lazer|ponto|equipamento|pista|"
          r"coordenadoria|galeria|museu|teatro|cine|clube|posto|base|sede|predio|edificio|ala|leito|"
          r"enfermaria|ambulatorio|maternidade|policlinica|upa|cras|creas|capsi?|naves?|vila ol[ií]mpica")

_REGRAS: list[tuple[str, re.Pattern[str]]] = [
    ("logradouro", re.compile(
        rf"\b(da o nome|da nome|denomina|altera a denominacao|altera o nome|nomina|atribui o nome|"
        rf"confere o nome|da a denominacao|passa a denominar)\b.*\b({_LUGAR})\b|\bdenominacao de\b.*\b({_LUGAR})\b")),
    ("calendario", re.compile(
        r"calendario oficial|\binstitui o dia\b|\binstitui a semana\b|\binstitui o mes\b|"
        r"\b(dia|semana|mes|jornada|campanha anual) (municipal|da|do|de)\b.*\bcalendario\b|"
        r"\binclui\b.*\b(dia|semana|mes|festa|festival|evento|feira)\b.*\bcalendario\b")),
    ("utilidade_publica", re.compile(r"utilidade publica")),
    ("patrimonio", re.compile(
        r"patrimonio (cultural|historico|imaterial|material|turistico|afetivo|gastronomico|esportivo|religioso)|"
        r"\bbem cultural\b|guia oficial|roteiro turistico|roteiro cultural|\bdeclara\b.*\bpatrimonio\b|"
        r"\btomba\b|\btombamento\b|capital (municipal|nacional) d[oa]|\bmarco historico\b|"
        r"\bpolo (gastronomico|cultural|turistico|recreativo|de lazer)|"
        r"\b(reconhece|considera|declara)\b.{0,40}\bde (relevante )?interesse (cultural|turistico|publico|social|historico)")),
    ("honraria", re.compile(
        r"\btitulo de cidada|\bcidadao (honorario|benemerito|carioca)|\bcidada (honoraria|benemerita|carioca)|"
        r"\bmedalha\b|\bdiploma\b|\bhonraria\b|\bcomenda\b|\bmoca(o)? de\b|\bvoto de (louvor|aplauso|congratula)|"
        r"\bconcede (o titulo|a medalha|o diploma|a comenda|o premio|honraria)|\bpremio\b.*\b(concede|institui)\b|"
        r"\bhomenage(m|ia)\b|\bsessao solene\b|cidade[- ]irma")),
]


def _normalizar(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", s)


def classificar(ementa: str, *, tema_camara: str | None = None) -> str:
    if tema_camara in CATEGORIAS:
        return tema_camara
    e = _normalizar(ementa)
    for categoria, regra in _REGRAS:
        if regra.search(e):
            return categoria
    return "normativa"


def simbolica(categoria: str) -> bool:
    return bool(CATEGORIAS.get(categoria, {}).get("simbolica"))
