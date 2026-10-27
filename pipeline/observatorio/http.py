"""Downloads educados: cache em disco, 1 pedido por segundo por servidor, CA da Câmara."""
from __future__ import annotations

import hashlib
import ssl
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from . import config

_ultimo_pedido: dict[str, float] = {}
_ctx: ssl.SSLContext | None = None


def _contexto() -> ssl.SSLContext:
    # aplicnt.camara.rj.gov.br manda o certificado sem a intermediária; o bundle da Tomoyo a inclui.
    global _ctx
    if _ctx is None:
        _ctx = ssl.create_default_context(cafile=str(config.CA_BUNDLE)) if config.CA_BUNDLE.exists() \
            else ssl.create_default_context()
    return _ctx


def _caminho_cache(url: str) -> Path:
    partes = urlsplit(url)
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:20]
    return config.RAW_DIR / partes.netloc / f"{h}.bin"


def baixar(url: str, *, usar_cache: bool = True, tentativas: int = 4) -> bytes:
    """Devolve o corpo da resposta; com usar_cache, uma URL já baixada não volta à rede."""
    destino = _caminho_cache(url)
    if usar_cache and destino.exists():
        return destino.read_bytes()

    host = urlsplit(url).netloc
    erro: Exception | None = None
    for tentativa in range(tentativas):
        espera = config.INTERVALO_S - (time.monotonic() - _ultimo_pedido.get(host, 0.0))
        if espera > 0:
            time.sleep(espera)
        _ultimo_pedido[host] = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=config.TIMEOUT_S, context=_contexto()) as resp:
                corpo = resp.read()
            break
        except Exception as e:  # rede instável no Domino: espera e repete
            erro = e
            time.sleep(2 ** tentativa * 3)
    else:
        raise RuntimeError(f"falhou depois de {tentativas} tentativas: {url}") from erro

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(corpo)
    return corpo
