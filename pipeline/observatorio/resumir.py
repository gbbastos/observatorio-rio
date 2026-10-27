"""Resumo em linguagem simples de cada lei "normativa" (as simbólicas a ementa já explica).

    python -m observatorio.resumir --estimar     # quantas leis faltam, sem chamar a API
    python -m observatorio.resumir --limite 20   # testa com poucas
    python -m observatorio.resumir               # todas as que faltam

Usa a Message Batches API (metade do preço, resultado em até 24 h, normalmente < 1 h). Cada lei é
resumida uma vez e guardada em data/cache/resumos.json; rodadas seguintes só mandam leis novas.
Se o processo for interrompido, a próxima rodada retoma o lote pendente (data/cache/resumos-lote.json).

Precisa do pacote `anthropic` (pipeline/requirements-ia.txt) e de credencial da API
(ANTHROPIC_API_KEY ou `ant auth login`). O modelo pode ser trocado com RESUMO_MODELO.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time

from . import classificar as C
from . import config

NORMAS = config.DATA_DIR / "camara" / "normas.json"
RESUMOS = config.CACHE_DIR / "resumos.json"
LOTE_PENDENTE = config.CACHE_DIR / "resumos-lote.json"
MODELO = os.environ.get("RESUMO_MODELO", "claude-opus-5-5")

SISTEMA = (
    "Você resume leis municipais do Rio de Janeiro para leitores comuns. Em no máximo duas frases curtas, "
    "em português simples, diga o que a lei muda na prática e para quem. Se a lei só autoriza o Executivo, "
    "cria diretrizes ou campanhas sem obrigação concreta, diga isso com clareza. Não opine, não elogie e "
    "não critique. Responda só com o resumo, sem título nem aspas."
)


def _id_api(lei_id: str) -> str:
    """custom_id aceita só letras, números, - e _: "LEI-9672/2026" -> "LEI-9672-2026"."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", lei_id)


def pendentes(resumos: dict[str, str]) -> list[dict]:
    normas = json.loads(NORMAS.read_text(encoding="utf-8"))["normas"]
    out = []
    for n in normas:
        if n["tipo"] not in ("LEI", "LC") or n["ano"] < config.ANO_INICIAL_LEIS or n["id"] in resumos:
            continue
        if C.simbolica(C.classificar(n["ementa"], tema_camara=n.get("tema_camara"))):
            continue
        out.append(n)
    return out


def _pedido(n: dict) -> str:
    texto = (n.get("ficha") or {}).get("texto")
    corpo = f"Ementa: {n['ementa']}"
    if texto:
        corpo += f"\n\nTexto da lei:\n{texto}"
    return corpo


def _gravar_resumos(resumos: dict[str, str]) -> None:
    RESUMOS.parent.mkdir(parents=True, exist_ok=True)
    RESUMOS.write_text(json.dumps(resumos, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estimar", action="store_true", help="só conta o que falta, sem chamar a API")
    ap.add_argument("--limite", type=int, default=0, help="manda no máximo N leis (0 = todas)")
    args = ap.parse_args()

    resumos: dict[str, str] = json.loads(RESUMOS.read_text(encoding="utf-8")) if RESUMOS.exists() else {}
    faltam = pendentes(resumos)
    sem_texto = sum(1 for n in faltam if not (n.get("ficha") or {}).get("texto"))
    print(f"{len(resumos)} resumos prontos; faltam {len(faltam)} leis ({sem_texto} sem o texto integral, "
          f"resumidas só pela ementa); modelo {MODELO}")
    if args.estimar or (not faltam and not LOTE_PENDENTE.exists()):
        return

    import anthropic  # noqa: PLC0415 (só esta etapa depende do SDK)
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    client = anthropic.Anthropic()

    if LOTE_PENDENTE.exists():
        lote_id = json.loads(LOTE_PENDENTE.read_text(encoding="utf-8"))["id"]
        print(f"retomando o lote {lote_id}")
    else:
        enviar = faltam[: args.limite] if args.limite else faltam
        lote = client.messages.batches.create(requests=[
            Request(
                custom_id=_id_api(n["id"]),
                params=MessageCreateParamsNonStreaming(
                    model=MODELO,
                    # o raciocínio do modelo conta dentro de max_tokens; o resumo em si é curto
                    max_tokens=4000,
                    output_config={"effort": "low"},
                    system=SISTEMA,
                    messages=[{"role": "user", "content": _pedido(n)}],
                ),
            )
            for n in enviar
        ])
        lote_id = lote.id
        LOTE_PENDENTE.parent.mkdir(parents=True, exist_ok=True)
        LOTE_PENDENTE.write_text(json.dumps({"id": lote_id, "ids": [n["id"] for n in enviar]}), encoding="utf-8")
        print(f"lote {lote_id} criado com {len(enviar)} leis")

    while True:
        lote = client.messages.batches.retrieve(lote_id)
        if lote.processing_status == "ended":
            break
        print(f"  {lote.processing_status}: {lote.request_counts.processing} em processamento", flush=True)
        time.sleep(60)

    por_id_api = {_id_api(n["id"]): n["id"] for n in faltam}
    for k in json.loads(LOTE_PENDENTE.read_text(encoding="utf-8")).get("ids", []):
        por_id_api.setdefault(_id_api(k), k)
    novos = falhas = 0
    for r in client.messages.batches.results(lote_id):
        lei_id = por_id_api.get(r.custom_id)
        if r.result.type != "succeeded" or not lei_id:
            falhas += 1
            continue
        msg = r.result.message
        if msg.stop_reason in ("refusal", "max_tokens"):
            falhas += 1
            continue
        texto = "".join(b.text for b in msg.content if b.type == "text").strip()
        if texto:
            resumos[lei_id] = texto
            novos += 1
    _gravar_resumos(resumos)
    LOTE_PENDENTE.unlink(missing_ok=True)
    print(f"{novos} resumos novos, {falhas} sem resumo (ficam para a próxima rodada)")


if __name__ == "__main__":
    main()
