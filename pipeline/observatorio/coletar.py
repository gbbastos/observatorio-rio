"""Coleta o que a Tomoyo não lê: as normas aprovadas pela Câmara do Rio.

    python -m observatorio.coletar               # visões + ficha de cada lei desde 2017
    python -m observatorio.coletar --sem-fichas  # só as visões (rápido, ~20 pedidos)

Saída: data/camara/normas.json. As fichas ficam no cache (data/raw), então só leis novas vão à rede.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from . import config, leis_cmrj

SAIDA = config.DATA_DIR / "camara" / "normas.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sem-fichas", action="store_true", help="não abre o documento de cada lei")
    ap.add_argument("--offline", action="store_true", help="usa só o cache, sem ir à rede")
    args = ap.parse_args()

    normas = leis_cmrj.coletar_normas(atualizar=not args.offline)
    recentes = [n for n in normas if n["ano"] >= config.ANO_INICIAL_LEIS and n["tipo"] in ("LEI", "LC")]
    print(f"{len(normas)} normas; {len(recentes)} leis desde {config.ANO_INICIAL_LEIS}", flush=True)

    anteriores: dict[str, dict] = {}
    if SAIDA.exists():
        anteriores = {n["id"]: n for n in json.loads(SAIDA.read_text(encoding="utf-8"))["normas"]}

    if not args.sem_fichas:
        for i, n in enumerate(recentes, 1):
            try:
                n["ficha"] = leis_cmrj.ler_ficha(n)
            except Exception as e:  # uma ficha que não abre não derruba a coleta
                print(f"  ficha {n['id']}: {e}", file=sys.stderr)
            if i % 200 == 0:
                print(f"  {i}/{len(recentes)} fichas", flush=True)
    for n in normas:
        if "ficha" not in n and n["id"] in anteriores and "ficha" in anteriores[n["id"]]:
            n["ficha"] = anteriores[n["id"]]["ficha"]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": config.CONTLEI,
        "normas": normas,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"gravado {SAIDA}")


if __name__ == "__main__":
    main()
