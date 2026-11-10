
#!/usr/bin/env python3
"""Atualiza cnn_portugal.m3u8 com o endereço HLS autenticado da IOL."""

from __future__ import annotations

import base64
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://services.iol.pt/matrix"

STREAM_BASE = (
    "https://video-auth1.iol.pt/live_cnn/live_cnn/"
    "edge_servers/cnn-720p/playlist.m3u8"
)

OUTPUT = Path("cnn_portugal.m3u8")


def obter_token() -> str:
    user_id = os.environ.get("IOL_USER_ID", "").strip()

    url = ENDPOINT + "?" + urllib.parse.urlencode({
        "userId": user_id
    })

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/plain, */*",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode(
                "utf-8", errors="replace"
            ).strip()

    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Endpoint IOL respondeu HTTP {exc.code}."
        ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível consultar a IOL: {exc}"
        ) from exc

    try:
        decoded = base64.b64decode(
            body, validate=True
        ).decode("utf-8")

    except Exception as exc:
        raise RuntimeError(
            "A resposta da IOL não veio no formato esperado."
        ) from exc

    fields = dict(
        item.split("=", 1)
        for item in decoded.split("&")
        if "=" in item
    )

    token_time = fields.get("server_time", "")
    hash_value = fields.get("hash_value", "")
    valid_minutes = fields.get("validminutes", "")

    if not hash_value or not re.fullmatch(
        r"\d+", valid_minutes or ""
    ):
        raise RuntimeError(
            "A resposta não contém os campos de token esperados."
        )

    if int(valid_minutes) <= 0:
        raise RuntimeError(
            "A IOL informou validade inválida para o token."
        )

    if not token_time:
        raise RuntimeError(
            "A resposta não contém server_time."
        )

    return body


def main() -> None:
    token = obter_token()

    stream_url = (
        STREAM_BASE
        + "?wmsAuthSign="
        + urllib.parse.quote(token, safe="")
    )

    # Grava SOMENTE o endereço, sem cabeçalho M3U.
    OUTPUT.write_text(stream_url, encoding="utf-8")

    print(
        f"Arquivo {OUTPUT} atualizado com sucesso. "
        "Token omitido do log."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
