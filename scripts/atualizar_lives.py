
import json
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARQUIVO_CANAIS = BASE / "canais.txt"
ARQUIVO_LISTA = BASE / "youtube.txt"

# Identifica o canal pelo nome, inclusive quando há variações.
def identificar_canal(nome):
    n = nome.casefold()
    n = re.sub(r"\s+", " ", n).strip()

    if "cnn brasil" in n:
        return "cnn"
    if "bandnews" in n or "band news" in n:
        return "bandnews"
    if "sbt news" in n:
        return "sbt"
    if "record news" in n:
        return "record"
    if "jovem pan" in n:
        return "jovem"
    if "bandjornal" in n:
        return "bandjornal"
    if "tv novo tempo" in n:
        return "tvnovotempo"

    return None


def ler_canais():
    canais = {}

    for linha in ARQUIVO_CANAIS.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        if not linha.strip() or "|" not in linha:
            continue

        nome, url = linha.split("|", 1)
        chave = identificar_canal(nome)

        if chave and url.strip().startswith("https://"):
            canais[chave] = url.strip()

    return canais


def obter_live(url):
    """Retorna a URL direta somente se houver live ativa."""

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
            check=False,
        )

        if proc.returncode != 0 or not proc.stdout.strip():
            print(f"Consulta indisponível: {url}")
            if proc.stderr:
                print(proc.stderr[-400:])
            return None

        dados = json.loads(proc.stdout)
        entradas = dados.get("entries")

        if entradas:
            dados = next(
                (
                    item for item in entradas
                    if item and (
                        item.get("is_live") is True
                        or item.get("live_status") == "is_live"
                    )
                ),
                {},
            )

        ativo = (
            dados.get("is_live") is True
            or dados.get("live_status") == "is_live"
        )

        video_id = dados.get("id", "")

        if ativo and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return f"https://www.youtube.com/watch?v={video_id}"

        print(f"Sem transmissão ativa identificada: {url}")
        return None

    except Exception as erro:
        print(f"Erro consultando {url}: {erro}")
        return None


def main():
    if not ARQUIVO_CANAIS.exists():
        raise FileNotFoundError("canais.txt não foi encontrado.")

    if not ARQUIVO_LISTA.exists():
        raise FileNotFoundError(
            "youtube.txt não existe. O script não criará uma lista vazia."
        )

    fontes = ler_canais()

    if not fontes:
        raise RuntimeError(
            "Nenhum canal válido foi encontrado em canais.txt."
        )

    # Consulta cada canal uma vez.
    lives = {}

    for chave, url in fontes.items():
        print(f"Consultando {chave}: {url}")
        lives[chave] = obter_live(url)

    # Preserva todas as linhas e altera somente URLs elegíveis.
    texto = ARQUIVO_LISTA.read_text(encoding="utf-8-sig")
    linhas = texto.splitlines()
    resultado = []
    alteracoes = 0

    for linha in linhas:
        if not linha.strip() or linha.lstrip().startswith("#"):
            resultado.append(linha)
            continue

        partes = linha.split("|")

        # Formato esperado:
        # Tema|Categoria|Classificação|Episódio/Título|Nome|URL
        if len(partes) < 6:
            resultado.append(linha)
            continue

        nome = partes[4].strip()
        url_atual = partes[5].strip()
        chave = identificar_canal(nome)

        # Não tocar em links que não sejam do YouTube.
        if (
            chave
            and chave in lives
            and lives[chave]
            and re.match(
                r"^https?://(www\.)?(youtube\.com|youtu\.be)/",
                url_atual,
                re.IGNORECASE,
            )
        ):
            if url_atual != lives[chave]:
                partes[5] = lives[chave]
                linha = "|".join(partes)
                alteracoes += 1
                print(f"Atualizado: {nome} -> {lives[chave]}")

        resultado.append(linha)

    # Não cria linhas novas e não apaga outros canais.
    novo_texto = "\n".join(resultado)
    if texto.endswith("\n"):
        novo_texto += "\n"

    if novo_texto != texto:
        ARQUIVO_LISTA.write_text(novo_texto, encoding="utf-8")
        print(f"Concluído: {alteracoes} URL(s) alterada(s).")
    else:
        print("Nenhuma alteração necessária.")
        print("Todas as linhas existentes foram preservadas.")


if __name__ == "__main__":
    main()
