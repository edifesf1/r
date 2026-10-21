
import json
import re
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARQUIVO_CANAIS = BASE / "canais.txt"
ARQUIVO_LISTA = BASE / "youtube.txt"

PADROES_CLIENTE = [
    "tv,web_safari",
    "web_safari,tv",
    "default,-android_sdkless",
]


def identificar_canal(nome):
    n = re.sub(r"\s+", " ", nome.casefold()).strip()

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
    if "novo tempo" in n:
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
    """Retorna somente um vídeo identificado como live ativa."""

    for cliente in PADROES_CLIENTE:
        comando = [
            "yt-dlp",
            "--dump-single-json",
            "--no-warnings",
            "--no-playlist",
            "--extractor-args",
            f"youtube:player_client={cliente}",
            url,
        ]

        print(f"Tentando cliente {cliente}: {url}")

        try:
            proc = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )

            if proc.returncode != 0 or not proc.stdout.strip():
                erro = proc.stderr.strip()

                if "Sign in to confirm" in erro:
                    print("YouTube exige confirmação contra bots.")
                elif erro:
                    print(f"Falha de consulta: {erro[-300:]}")

                time.sleep(2)
                continue

            dados = json.loads(proc.stdout)
            entradas = dados.get("entries")

            candidatos = entradas if entradas else [dados]

            for item in candidatos:
                if not item:
                    continue

                ativo = (
                    item.get("is_live") is True
                    or item.get("live_status") == "is_live"
                )

                video_id = item.get("id", "")

                if (
                    ativo
                    and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id)
                ):
                    print(f"Live identificada: {video_id}")
                    return (
                        "https://www.youtube.com/watch?v=" + video_id
                    )

            print("Nenhuma live ativa identificada nesta tentativa.")

        except subprocess.TimeoutExpired:
            print(f"Tempo esgotado: {url}")
        except (json.JSONDecodeError, OSError) as erro:
            print(f"Erro na consulta: {erro}")

        time.sleep(2)

    print(f"Consulta indisponível após as tentativas: {url}")
    return None


def main():
    if not ARQUIVO_CANAIS.exists():
        raise FileNotFoundError("canais.txt não foi encontrado.")

    if not ARQUIVO_LISTA.exists():
        raise FileNotFoundError("youtube.txt não existe.")

    fontes = ler_canais()

    if not fontes:
        raise RuntimeError("Nenhum canal válido em canais.txt.")

    lives = {}

    for chave, url in fontes.items():
        print(f"\nConsultando {chave}: {url}")
        lives[chave] = obter_live(url)

    texto = ARQUIVO_LISTA.read_text(encoding="utf-8-sig")
    linhas = texto.splitlines()
    resultado = []
    alteracoes = 0

    for linha in linhas:
        if not linha.strip() or linha.lstrip().startswith("#"):
            resultado.append(linha)
            continue

        partes = linha.split("|")

        if len(partes) < 6:
            resultado.append(linha)
            continue

        nome = partes[4].strip()
        url_atual = partes[5].strip()
        chave = identificar_canal(nome)

        if (
            chave in lives
            and lives[chave]
            and re.match(
                r"^https?://(www\.)?(youtube\.com|youtu\.be)/",
                url_atual,
                re.IGNORECASE,
            )
        ):
            nova_url = lives[chave]

            if url_atual != nova_url:
                partes[5] = nova_url
                linha = "|".join(partes)
                alteracoes += 1
                print(f"Atualizado: {nome} -> {nova_url}")

        resultado.append(linha)

    novo_texto = "\n".join(resultado)

    if texto.endswith("\n"):
        novo_texto += "\n"

    if novo_texto != texto:
        ARQUIVO_LISTA.write_text(novo_texto, encoding="utf-8")
        print(f"\nConcluído: {alteracoes} URL(s) alterada(s).")
    else:
        print("\nNenhuma alteração necessária.")
        print("As linhas existentes foram preservadas.")


if __name__ == "__main__":
    main()
