"""Normas aprovadas da Câmara do Rio (leis, leis complementares, decretos legislativos, resoluções).

As proposições e votações vêm da Tomoyo; o que a Tomoyo não lê é a base de legislação (contlei.nsf),
que diz o que virou norma, quem é o autor, se está em vigor e de que projeto veio.
"""
from __future__ import annotations

import html
import json
import re
import sys
from typing import Any, Iterator

from . import config, http

sys.path.insert(0, str(config.COMO_VOTOU / "backend"))

POR_PAGINA = 1000
_RE_TAGS = re.compile(r"<[^>]+>")
_RE_ESPACO = re.compile(r"\s+")


def _valor(coluna: dict[str, Any]) -> Any:
    for chave in ("text", "number", "datetime"):
        if chave in coluna:
            return coluna[chave].get("0")
    if "textlist" in coluna:
        return [t.get("0") for t in coluna["textlist"].get("text", [])]
    return None


def _ler_visao(visao: str, *, atualizar: bool) -> Iterator[dict[str, Any]]:
    inicio = 1
    while True:
        url = f"{config.CONTLEI}/{visao}?ReadViewEntries&OutputFormat=JSON&Start={inicio}&Count={POR_PAGINA}"
        doc = json.loads(http.baixar(url, usar_cache=not atualizar).decode("utf-8", "replace"), strict=False)
        entradas = doc.get("viewentry", [])
        yield from entradas
        if len(entradas) < POR_PAGINA:
            return
        inicio += POR_PAGINA


def _autores(valor: Any) -> list[str]:
    """Um texto por autor. A visão traz uma lista, mas um item pode juntar vários ("Vereador A.
    Vereador B", "VEREADORES A, B E C"); a divisão em si é a da Tomoyo, que preserva comissões."""
    from app.names import split_authors  # noqa: PLC0415 (vendor/como-votou/backend no sys.path)

    brutos = valor if isinstance(valor, list) else [valor or ""]
    out: list[str] = []
    for b in brutos:
        if re.match(r"\s*comiss", b or "", re.I):  # um item de comissão é um autor só
            out.append(b.strip())
            continue
        b = re.sub(r"[.;]\s+(?=vereador)", ", ", b or "", flags=re.I)
        out.extend(p for p in (x.strip() for x in split_authors(b)) if p)
    return out


def _norma(tipo: str, entrada: dict[str, Any]) -> dict[str, Any] | None:
    colunas = {c.get("@name"): _valor(c) for c in entrada.get("entrydata", [])}
    valores = [_valor(c) for c in entrada.get("entrydata", [])]
    if not valores:
        return None
    numero = str(valores[0] or "").strip()
    ano = colunas.get("ComplL")
    if not numero.isdigit() or not ano:
        return None
    ementa = colunas.get("EmentaL") or colunas.get("$9") or ""
    return {
        "id": f"{tipo}-{int(numero)}/{int(float(ano))}",
        "tipo": tipo,
        "numero": int(numero),
        "ano": int(float(ano)),
        "status": (colunas.get("Status") or "").strip() or None,
        "ementa": _RE_ESPACO.sub(" ", str(ementa)).strip(),
        "autores_raw": _autores(valores[-1]),
        "unid": entrada.get("@unid"),
        "visao": None,
    }


def coletar_normas(*, atualizar: bool = True) -> list[dict[str, Any]]:
    """Todas as normas, uma vez cada.

    A visão "Leis Ordinárias" do site deixa de fora as leis de logradouro, de calendário e de
    utilidade pública, que só aparecem nas listas temáticas; a lei ordinária completa é a soma das
    duas, e `tema_camara` guarda a lista temática em que a própria Câmara pôs a lei.
    """
    normas: dict[str, dict[str, Any]] = {}
    visoes = [(tipo, None, visao) for tipo, visao in config.VISOES_LEIS.items()]
    visoes += [("LEI", tema, visao) for tema, visao in config.VISOES_TEMAS.items()]
    for tipo, tema, visao in visoes:
        for e in _ler_visao(visao, atualizar=atualizar):
            n = _norma(tipo, e)
            if not n:
                continue
            n["visao"] = visao
            n["tema_camara"] = tema
            atual = normas.setdefault(n["id"], n)
            if tema and not atual.get("tema_camara"):
                atual["tema_camara"] = tema
    return list(normas.values())


# --- ficha de cada norma (data, projeto de origem, forma de vigência) --------------------------

_CAMPOS_FICHA = {
    "data": re.compile(r"Data da (?:Lei|Norma|Resolução|Decreto Legislativo)\s+(\d{1,2})/(\d{1,2})/(\d{4})", re.I),
    "projeto": re.compile(r"Projeto de (Lei Complementar|Lei|Decreto Legislativo|Resolução) nº\s*([\d.]+)\s*/\s*(\d{4})", re.I),
    "forma": re.compile(r"Forma de Vigência\s+(.+?)\s+(?:Leis relacionadas|Atalho|$)", re.I),
}
_SIGLA_PROJETO = {"lei": "PL", "lei complementar": "PLC", "decreto legislativo": "PDL", "resolução": "PR"}


def _texto(html_bytes: bytes) -> str:
    t = html_bytes.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    return _RE_ESPACO.sub(" ", html.unescape(_RE_TAGS.sub(" ", t))).strip()


def ler_ficha(norma: dict[str, Any]) -> dict[str, Any]:
    """Abre o documento da norma; documentos já lidos vêm do cache (a ficha de uma lei não muda)."""
    url = f"{config.CONTLEI}/{norma['visao']}/{norma['unid']}?OpenDocument"
    texto = _texto(http.baixar(url))
    ficha: dict[str, Any] = {"url": url}
    if m := _CAMPOS_FICHA["data"].search(texto):
        mes, dia, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))   # o Domino imprime MM/DD/AAAA
        ficha["data"] = f"{ano:04d}-{mes:02d}-{dia:02d}"
    if m := _CAMPOS_FICHA["projeto"].search(texto):
        sigla = _SIGLA_PROJETO.get(m.group(1).lower(), "PL")
        ficha["projeto"] = f"{sigla}-{int(m.group(2).replace('.', ''))}/{m.group(3)}"
    if m := _CAMPOS_FICHA["forma"].search(texto):
        forma = m.group(1).strip()
        ficha["forma"] = forma[:60] if forma else None
    if m := _TEXTO_LEI.search(texto):
        ficha["texto"] = m.group(1).strip()
    return ficha


# o corpo da lei vai do cabeçalho "LEI Nº ..." até o aviso de que o texto não substitui o publicado
_TEXTO_LEI = re.compile(r"Texto d[ao] (?:Lei|Norma|Resolução|Decreto)\s+(?:Texto d[ao] \w+\s+)?(.+?)\s+Este texto não substitui",
                        re.I | re.S)
