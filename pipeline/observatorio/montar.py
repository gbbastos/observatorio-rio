"""Junta os dados da Tomoyo (parlamentares, proposições, votações, presença) com as normas e a
classificação, e escreve os JSON que o site lê em site/src/data/<casa>/.

    python -m observatorio.montar              # todas as casas com dados
    python -m observatorio.montar --casa alerj
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import classificar as C
from . import config
from . import temas as T

sys.path.insert(0, str(config.COMO_VOTOU / "backend"))
from app.etl.aggregates import legislatura_of, party_majority, party_of  # noqa: E402
from app.names import NameResolver, is_institutional  # noqa: E402  (casamento de nomes da Tomoyo)

RESUMOS = config.CACHE_DIR / "resumos.json"
PARTIDOS = {"PROGRESSISTAS": "PP", "UNIAO": "UNIÃO", "UNIÃO BRASIL": "UNIÃO", "PODEMOS": "PODE",
            "SOLIDARIEDADE": "SD", "SDD": "SD", "REP": "REPUBLICANOS", "PC DO B": "PCDOB", "PCDOB": "PCDOB"}
TIPOS_LEI = ("LEI", "LC")
TIPOS_PROJETO = ("PL", "PLC")
TIPOS_HONRARIA = ("PDL", "PR")   # títulos, medalhas e diplomas saem por decreto legislativo ou resolução
MINUSCULAS = {"DE", "DA", "DO", "DOS", "DAS", "E"}


@dataclass(frozen=True)
class Casa:
    id: str
    nome: str
    curto: str
    membro: str
    membros: str
    cadeiras: int
    ano_inicial: int
    tomoyo: Path            # frontend/data/<uf> do repositório da Tomoyo
    chave_lista: str        # "vereadores" ou "deputados" no static-data
    pasta_detalhe: str      # static-vereadores ou static-deputados
    fonte_tomoyo: tuple[str, str]
    normas: Path | None = None   # sem normas, a casa entra só com projetos, votações e presença
    ano_inicial_leis: int | None = None   # as leis podem ir mais atrás que os dados da Tomoyo
    legislaturas_extras: tuple[dict[str, Any], ...] = ()   # legislaturas que só têm leis

    @property
    def desde_leis(self) -> int:
        return self.ano_inicial_leis or self.ano_inicial


CASAS = {
    "camara": Casa(
        id="camara", nome="Câmara Municipal do Rio de Janeiro", curto="Câmara do Rio",
        membro="vereador", membros="vereadores", cadeiras=51, ano_inicial=config.ANO_INICIAL,
        tomoyo=config.COMO_VOTOU / "frontend" / "data" / "rj", chave_lista="vereadores",
        pasta_detalhe="static-vereadores",
        fonte_tomoyo=("Tomoyo / como-votou (vereadores, proposições, votações nominais, presença)",
                      "https://github.com/Tomoyo-Computer-Science-Research-Unit/como-votou"),
        normas=config.DATA_DIR / "camara" / "normas.json",
        ano_inicial_leis=config.ANO_INICIAL_LEIS,
        legislaturas_extras=tuple(config.LEGISLATURAS_EXTRAS_CAMARA),
    ),
    "alerj": Casa(
        id="alerj", nome="Assembleia Legislativa do Estado do Rio de Janeiro", curto="ALERJ",
        membro="deputado", membros="deputados", cadeiras=70, ano_inicial=2019,
        tomoyo=config.ASSEMBLEIAS / "frontend" / "data" / "rj", chave_lista="deputados",
        pasta_detalhe="static-deputados",
        fonte_tomoyo=("Tomoyo / assembleias (deputados, proposições, votações nominais, presença)",
                      "https://github.com/Tomoyo-Computer-Science-Research-Unit/assembleias"),
    ),
}


def consertar(s: Any) -> Any:
    """Desfaz UTF-8 lido como latin-1 ("UNIÃ\x83O" -> "UNIÃO"), que aparece em alguns campos."""
    if not isinstance(s, str) or not re.search(r"[ÃÂ][\x80-\xbf]", s):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return s


def partido(sigla: str | None) -> str | None:
    if not sigla:
        return None
    s = consertar(sigla).strip().upper()
    if "," in s:  # "PSD , PSC , PSD": o painel às vezes imprime o histórico
        s = s.split(",")[-1].strip()
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return PARTIDOS.get(s) or PARTIDOS.get(sem_acento) or s


def slugify(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def nome_bonito(autor: str) -> str:
    s = re.sub(r"^(vereador(a|es|as)?|deputad[oa]s?|sr\.?a?)\s+", "", autor.strip(), flags=re.I)
    if s.isupper():
        s = " ".join(p.lower() if i and p in MINUSCULAS else p.capitalize() for i, p in enumerate(s.split()))
    return s


def ler_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def gravar(p: Path, dado: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dado, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def resumo_categorias(xs: list[dict[str, Any]]) -> dict[str, Any]:
    cats = Counter(x["categoria"] for x in xs)
    temas = Counter(x["tema"] for x in xs if x.get("tema"))
    return {"total": len(xs), "simbolicas": sum(cats[c] for c in cats if C.simbolica(c)), "por_categoria": dict(cats),
            "por_tema": dict(temas)}


def tema_de(categoria: str | None, ementa: str, texto: str | None = None) -> str | None:
    """Só as leis e projetos que não são simbólicos ganham tema."""
    return T.tema(ementa, texto) if categoria and not C.simbolica(categoria) else None


def mandatos_da_casa(legislaturas: list[dict[str, Any]], ano_inicial: int,
                     so_leis: set[int]) -> list[dict[str, Any]]:
    """Legislaturas cobertas pelos dados, com rótulo em anos ("2021–2024"; a da ALERJ que acaba em
    31/1/2023 vira "2019–2022"). `so_leis`: as que só têm leis (sem projetos, votos e presença)."""
    out = []
    for lg in legislaturas:
        if int(lg["fim"][:4]) < ano_inicial:
            continue
        fim = int(lg["fim"][:4]) - (1 if lg["fim"][5:7] == "01" else 0)
        out.append({"leg": int(lg["numero"]), "inicio": lg["inicio"], "fim": lg["fim"],
                    "rotulo": f"{lg['inicio'][:4]}–{fim}", "so_leis": int(lg["numero"]) in so_leis})
    return out


def montar_normas(casa: Casa, resolver: NameResolver, slugs: dict[str, str], nome_por_id: dict[str, str],
                  resumos: dict[str, str], legislaturas: list[dict[str, Any]]
                  ) -> tuple[list[dict[str, Any]], Counter[str], str | None]:
    if not casa.normas or not casa.normas.exists():
        return [], Counter(), None
    doc = ler_json(casa.normas)
    leis: list[dict[str, Any]] = []
    nao_casados: Counter[str] = Counter()
    for n in doc["normas"]:
        if n["ano"] < casa.desde_leis or n["tipo"] not in ("LEI", "LC", "DL"):
            continue
        autores: list[dict[str, Any]] = []
        vistos: set[str] = set()
        for bruto in n["autores_raw"]:
            if is_institutional(bruto):
                if bruto.lower() not in vistos:
                    vistos.add(bruto.lower())
                    autores.append({"nome": nome_bonito(bruto), "inst": True})
                continue
            ids = resolver.resolve(bruto, count_unmatched=False)
            if not ids:
                nao_casados[bruto] += 1
                if slugify(bruto) not in vistos:
                    vistos.add(slugify(bruto))
                    autores.append({"nome": nome_bonito(bruto)})
                continue
            for vid in ids:
                if vid not in vistos:
                    vistos.add(vid)
                    autores.append({"id": vid, "slug": slugs[vid], "nome": nome_por_id[vid]})
        ficha = n.get("ficha") or {}
        categoria = C.classificar(n["ementa"], tema_camara=n.get("tema_camara"))
        leis.append({
            "id": n["id"], "tipo": n["tipo"], "numero": n["numero"], "ano": n["ano"],
            "data": ficha.get("data"), "ementa": consertar(n["ementa"]), "categoria": categoria,
            "simbolica": C.simbolica(categoria),
            "tema": tema_de(categoria, n["ementa"], ficha.get("texto")) if n["tipo"] in TIPOS_LEI else None,
            "leg": legislatura_of(ficha.get("data") or f"{n['ano']}-07-01", legislaturas),
            "status": n.get("status"),
            "projeto": ficha.get("projeto"), "forma": ficha.get("forma"),
            "autores": autores, "n_autores": sum(1 for a in autores if not a.get("inst")),
            "url": f"{config.CONTLEI}/{n['visao']}/{n['unid']}?OpenDocument",
            "resumo": resumos.get(n["id"]),
        })
    leis.sort(key=lambda x: (x["data"] or f"{x['ano']}-00-00", x["numero"]), reverse=True)
    return leis, nao_casados, doc["coletado_em"]


def montar(casa: Casa) -> None:
    saida = config.SITE_DATA_DIR / casa.id
    fotos = config.SITE_PUBLIC_DIR / "fotos" / casa.id
    estatico = ler_json(casa.tomoyo / "static-data.generated.json")
    resumos: dict[str, str] = ler_json(RESUMOS) if RESUMOS.exists() else {}

    roster = estatico[casa.chave_lista]
    resolver = NameResolver(roster)
    slugs: dict[str, str] = {}
    for v in roster:
        s = slugify(v["nome_parlamentar"] or v["nome"])
        slugs[v["id"]] = s if s not in slugs.values() else f"{s}-{v['id'].split(':')[-1]}"
    nome_por_id = {v["id"]: consertar(v["nome_parlamentar"] or v["nome"]) for v in roster}

    if saida.exists():
        shutil.rmtree(saida)
    if fotos.exists():
        shutil.rmtree(fotos)
    fotos.mkdir(parents=True, exist_ok=True)

    legislaturas = sorted([*casa.legislaturas_extras, *estatico["legislaturas"]], key=lambda lg: int(lg["numero"]))
    mandatos = mandatos_da_casa(legislaturas, casa.desde_leis, {int(lg["numero"]) for lg in casa.legislaturas_extras})
    legs_cobertas = {m["leg"] for m in mandatos}

    leis, nao_casados, coletado_em = montar_normas(casa, resolver, slugs, nome_por_id, resumos, legislaturas)
    tem_leis = bool(leis)
    leis_por_parlamentar: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lei_do_projeto: dict[str, str] = {}
    for lei in leis:
        for a in lei["autores"]:
            if a.get("id"):
                leis_por_parlamentar[a["id"]].append(lei)
        if lei["projeto"] and lei["tipo"] in TIPOS_LEI:
            lei_do_projeto[lei["projeto"]] = lei["id"]
    por_id = {v["id"]: v for v in roster}
    contra_partido: dict[tuple[str, str], bool] = {}   # (parlamentar, votação) -> votou contra a maioria do partido

    # --- votações -----------------------------------------------------------------------------
    votacoes: list[dict[str, Any]] = []
    for vt in estatico["votacoes"]:
        slug = vt["id"].replace(":", "-")
        arq = casa.tomoyo / "static-votacoes" / f"{slug}.generated.json"
        completo = ler_json(arq) if arq.exists() else {}
        prop = vt.get("proposicao") or {}
        ementa = consertar(completo.get("proposicao", {}).get("ementa") or prop.get("ementa"))
        cat_vt = C.classificar(ementa) if ementa else None
        resumo = {
            "id": slug, "data": vt["data"], "legislatura": vt.get("legislatura"),
            "sessao": {k: consertar(x) for k, x in (vt.get("sessao") or {}).items()},
            "proposicao": {
                "id": prop.get("id"), "tipo": prop.get("tipo"), "ementa": ementa,
                "autores": [nome_por_id.get(i, i) for i in prop.get("autores_ids") or []]
                           or [nome_bonito(consertar(a)) for a in prop.get("autores") or []],
                "categoria": cat_vt, "tema": tema_de(cat_vt, ementa) if ementa else None,
            },
            "objeto": vt.get("objeto"), "resultado": vt.get("resultado"),
            "resultado_frase": consertar(completo.get("resultado_frase")),
            "contagem": vt.get("contagem"), "lado_vencedor": vt.get("lado_vencedor"), "fonte": vt.get("fonte"),
        }
        votacoes.append(resumo)
        # mesma conta da Tomoyo (aggregates.py), guardada voto a voto para dar o número de cada mandato
        votos_vt = completo.get("votos", {})
        leg_vt = int(vt["legislatura"]) if vt.get("legislatura") else legislatura_of(vt["data"], legislaturas)
        partido_de = {vid: party_of(por_id[vid], leg_vt) if vid in por_id else None for vid in votos_vt}
        for vid, voto in votos_vt.items():
            if voto in ("sim", "nao"):
                maioria = party_majority(votos_vt, partido_de, partido_de.get(vid))
                if maioria is not None:
                    contra_partido[(vid, slug)] = voto != maioria
        gravar(saida / "votacoes" / f"{slug}.json",
               {**resumo, "votos": completo.get("votos", {}), "presidente": vt.get("presidente")})
    votacoes.sort(key=lambda x: (x["data"], x["id"]), reverse=True)
    data_votacao = {v["id"]: v["data"] for v in votacoes}
    leg_votacao = {v["id"]: int(v["legislatura"]) if v.get("legislatura") else legislatura_of(v["data"], legislaturas)
                   for v in votacoes}

    # --- ficha de cada parlamentar --------------------------------------------------------
    lista: list[dict[str, Any]] = []
    todos_projetos: dict[str, dict[str, Any]] = {}
    for v in roster:
        vid, slug = v["id"], slugs[v["id"]]
        foto = None
        if v.get("foto") and (casa.tomoyo / v["foto"]).exists():
            shutil.copy(casa.tomoyo / v["foto"], fotos / f"{slug}.jpg")
            foto = f"fotos/{casa.id}/{slug}.jpg"

        arq = casa.tomoyo / casa.pasta_detalhe / f"{vid.replace(':', '-')}.generated.json"
        detalhe = ler_json(arq) if arq.exists() else {"votos": [], "proposicoes": []}

        minhas = leis_por_parlamentar.get(vid, [])
        leis_ord = [x for x in minhas if x["tipo"] in TIPOS_LEI]
        por_cat = Counter(x["categoria"] for x in leis_ord)
        sozinho = sum(1 for x in leis_ord if x["n_autores"] == 1)

        props = []
        for p in detalhe["proposicoes"]:
            if (p.get("ano") or 0) < casa.ano_inicial:
                continue
            classificavel = p["tipo"] in TIPOS_PROJETO + TIPOS_HONRARIA
            cat = C.classificar(p["ementa"]) if classificavel else None
            item = {"id": p["id"], "tipo": p["tipo"], "data": p.get("data"), "ementa": consertar(p["ementa"]),
                    "categoria": cat, "simbolica": C.simbolica(cat) if cat else None,
                    # pedidos de informação também ganham tema (o assunto ou o órgão perguntado)
                    "tema": (tema_de(cat, p["ementa"]) if p["tipo"] in TIPOS_PROJETO
                             else T.tema(p["ementa"]) if p["tipo"] == "REQINF" else None),
                    "leg": legislatura_of(p.get("data") or f"{p['ano']}-07-01", legislaturas),
                    "lei": lei_do_projeto.get(p["id"]),
                    "coautores": len(p.get("coautores") or [])}
            props.append(item)
            if p["tipo"] in TIPOS_PROJETO:
                todos_projetos.setdefault(p["id"], item)
        tipos = Counter(p["tipo"] for p in props)
        projetos = [p for p in props if p["tipo"] in TIPOS_PROJETO]
        cat_projetos = Counter(p["categoria"] for p in projetos)

        votos = []
        for x in detalhe["votos"]:
            vot = x["votacao_id"].replace(":", "-")
            votos.append({"id": vot, "voto": x["voto"], "leg": leg_votacao.get(vot),
                          "contra_partido": contra_partido.get((vid, vot))})
        votos.sort(key=lambda x: data_votacao.get(x["id"], ""), reverse=True)

        resumo = {
            "id": vid, "slug": slug, "nome": nome_por_id[vid], "nome_civil": consertar(v.get("nome")),
            "partido": partido(v.get("partido")),
            "partidos_por_legislatura": {k: partido(p) for k, p in (v.get("partidos_por_legislatura") or {}).items()},
            "em_exercicio": v.get("situacao") == "em_exercicio", "legislaturas": v.get("legislaturas", []),
            "mandatos": sorted(int(x) for x in v.get("legislaturas", []) if int(x) in legs_cobertas),
            "foto": foto, "email": v.get("email"), "perfil_url": v.get("perfil_url"),
            "leis": {
                "total": len(leis_ord), "simbolicas": sum(por_cat[c] for c in por_cat if C.simbolica(c)),
                "por_categoria": dict(por_cat),
                "peso": round(sum(1 / x["n_autores"] for x in leis_ord if x["n_autores"]), 2),
                "peso_normativas": round(sum(1 / x["n_autores"] for x in leis_ord
                                             if x["n_autores"] and not x["simbolica"]), 2),
                "sozinho": sozinho, "em_grupo": len(leis_ord) - sozinho,
            },
            "titulos": sum(1 for x in minhas if x["tipo"] == "DL" and x["categoria"] == "honraria"),
            "proposicoes": {
                "por_tipo": dict(tipos), "pl": len(projetos),
                "pl_simbolicos": sum(cat_projetos[c] for c in cat_projetos if C.simbolica(c)),
                "pl_por_categoria": dict(cat_projetos),
                "pl_viraram_lei": sum(1 for p in projetos if p["lei"]),
                "honrarias": sum(1 for p in props if p["tipo"] in TIPOS_HONRARIA and p["categoria"] == "honraria"),
                "reqinf": tipos.get("REQINF", 0), "indicacoes": tipos.get("IND", 0), "mocoes": tipos.get("MOC", 0),
                "ultima": max((p["data"] for p in props if p["data"]), default=None),
            },
            "votacoes": {**v.get("votos", {}).get("total", {}), "participacao": v.get("participacao"),
                         "com_maioria": v.get("com_maioria"), "contra_partido": v.get("contra_partido"),
                         "contra_partido_taxa": v.get("contra_partido_taxa")},
            "presenca": v.get("presenca", {}).get("por_ano", {}),
        }
        lista.append(resumo)
        gravar(saida / "parlamentares" / f"{slug}.json", {
            **resumo,
            "lista_leis": [{k: x[k] for k in ("id", "tipo", "numero", "ano", "data", "ementa", "categoria",
                                              "simbolica", "tema", "leg", "projeto", "status", "n_autores", "url",
                                              "resumo")}
                           | {"coautores": [a["nome"] for a in x["autores"] if a.get("id") != vid]}
                           for x in minhas],
            "lista_proposicoes": sorted(props, key=lambda p: p["data"] or "", reverse=True),
            "lista_votos": votos,
        })

    # --- casa: números gerais ------------------------------------------------------------
    leg_atual = estatico["legislaturas"][-1]
    ano_leg = int(leg_atual["inicio"][:4])
    leis_ord_todas = [x for x in leis if x["tipo"] in TIPOS_LEI]
    projetos = list(todos_projetos.values())

    def por_ano(xs: list[dict[str, Any]], ano_de) -> dict[str, Any]:
        return {str(a): resumo_categorias([x for x in xs if ano_de(x) == a]) for a in sorted({ano_de(x) for x in xs})}

    def ano_projeto(p: dict[str, Any]) -> int:
        return int(p["id"].rsplit("/", 1)[-1])

    meta = {
        "casa": casa.id, "nome": casa.nome, "curto": casa.curto, "membro": casa.membro, "membros": casa.membros,
        "cadeiras": casa.cadeiras, "legislatura_atual": leg_atual, "ano_inicial": casa.ano_inicial,
        "ano_inicial_leis": casa.desde_leis,
        "mandatos": mandatos,
        "tem_leis": tem_leis,
        "atualizado_em": max(filter(None, [estatico["generated_at"], coletado_em])),
        "montado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "categorias": C.CATEGORIAS,
        "temas": T.TEMAS,
        "leis": resumo_categorias(leis_ord_todas),
        "leis_legislatura": resumo_categorias([x for x in leis_ord_todas if x["ano"] >= ano_leg]),
        "leis_por_ano": por_ano(leis_ord_todas, lambda x: x["ano"]),
        "projetos": resumo_categorias(projetos),
        "projetos_viraram_lei": sum(1 for p in projetos if p["lei"]),
        "projetos_por_ano": por_ano(projetos, ano_projeto),
        "titulos": sum(1 for x in leis if x["tipo"] == "DL" and x["categoria"] == "honraria"),
        "votacoes": len(votacoes),
        "fontes": [{"nome": casa.fonte_tomoyo[0], "url": casa.fonte_tomoyo[1]}]
                  + ([{"nome": "Câmara Municipal do Rio: base de legislação (contlei.nsf)", "url": config.CONTLEI}]
                     if tem_leis else []),
        "autores_nao_casados": nao_casados.most_common(40),
    }
    gravar(saida / "meta.json", meta)
    gravar(saida / "parlamentares.json", lista)
    gravar(saida / "leis.json", leis)
    gravar(saida / "votacoes.json", votacoes)
    print(f"[{casa.id}] {len(lista)} parlamentares, {len(leis)} normas, {len(projetos)} projetos, "
          f"{len(votacoes)} votações")
    if tem_leis:
        print(f"[{casa.id}] leis desde {casa.desde_leis}: {meta['leis']['total']}, "
              f"simbólicas {meta['leis']['simbolicas']}; autores sem casamento: {sum(nao_casados.values())}")
    print(f"[{casa.id}] projetos desde {casa.ano_inicial}: {meta['projetos']['total']}, "
          f"simbólicos {meta['projetos']['simbolicas']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--casa", choices=sorted(CASAS), action="append", help="só esta casa (pode repetir)")
    args = ap.parse_args()
    for cid in args.casa or sorted(CASAS):
        casa = CASAS[cid]
        if not (casa.tomoyo / "static-data.generated.json").exists():
            print(f"[{cid}] sem dados da Tomoyo em {casa.tomoyo}; pulando")
            continue
        montar(casa)


if __name__ == "__main__":
    main()
