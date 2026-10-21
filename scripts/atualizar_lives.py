
import json
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARQUIVO_CANAIS = BASE / "canais.txt"
ARQUIVO_SAIDA = BASE / "youtube.txt"

def consultar_live(url):
    try:
        proc = subprocess.run(
            [
                "yt-dlp",
                "--dump-single-json",
                "--no-warnings",
                "--no-playlist",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )

        if proc.returncode != 0 or not proc.stdout.strip():
            print(f"Falha ao consultar: {url}")
            print(proc.stderr[-500:])
            return None

        dados = json.loads(proc.stdout)
        entradas = dados.get("entries")

        if entradas:
            candidatos = [
                item for item in entradas
                if item and (
                    item.get("is_live") is True
                    or item.get("live_status") == "is_live"
                )
            ]
            dados = candidatos[0] if candidatos else {}

        if not (
            dados.get("is_live") is True
            or dados.get("live_status") == "is_live"
        ):
            print(f"Nenhuma live ativa encontrada: {url}")
            return None

        video_id = dados.get("id", "")

        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            print(f"ID de vídeo inválido para: {url}")
            return None

        return f"https://www.youtube.com/watch?v={video_id}"

    except Exception as erro:
        print(f"Erro ao consultar {url}: {erro}")
        return None


def ler_canais():
    canais = []

    for linha in ARQUIVO_CANAIS.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        linha = linha.strip()

        if not linha or "|" not in linha:
            continue

        nome, url = linha.split("|", 1)
        canais.append((nome.strip(), url.strip()))

    return canais


def ler_links_anteriores():
    links = {}

    if not ARQUIVO_SAIDA.exists():
        return links

    for linha in ARQUIVO_SAIDA.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        partes = linha.split("|")

        if len(partes) >= 3:
            links[partes[0].strip().lower()] = partes[2].strip()

    return links


def main():
    canais = ler_canais()
    anteriores = ler_links_anteriores()
    linhas = []

    if not canais:
        raise RuntimeError("Nenhum canal encontrado em canais.txt")

    for nome, url in canais:
        novo = consultar_live(url)

        if novo:
            link = novo
        else:
            link = anteriores.get(nome.lower(), url)

        linhas.append(f"Notícias|{nome}|{link}")
        print(f"{nome}: {link}")

    ARQUIVO_SAIDA.write_text(
        "\n".join(linhas) + "\n",
        encoding="utf-8",
    )

    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
