
import json
import re
import subprocess
import time
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARQUIVO_CANAIS = BASE / "canais.txt"
ARQUIVO_LISTA = BASE / "youtube.txt"

PADROES_CLIENTE = [
    "tv,web_safari",
    "web_safari,tv",
    "default,-android_sdkless",
]


def normalizar_nome(nome):
    """Compara nomes ignorando maiúsculas, acentos e espaços extras."""
    nome = unicodedata.normalize("NFKD", nome.casefold())
    nome = "".join(
        c for c in nome
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", nome).strip()


def ler_canais():
    """Lê os canais cadastrados em canais.txt."""
    canais = {}

    for numero, linha in enumerate(
        ARQUIVO_CANAIS.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue

        if "|" not in linha:
            print(f"Linha inválida em canais.txt: {numero}")
            continue

        nome, url = linha.split("|", 1)
        nome = nome.strip()
        url = url.strip()

        if not nome or not url.startswith("https://"):
            print(f"Nome ou URL inválidos na linha {numero}.")
            continue

        chave = normalizar_nome(nome)

        if chave in canais:
            print(f"Canal duplicado em canais.txt: {nome}")
            continue

        canais[chave] = {
            "nome": nome,
            "url": url,
        }

    return canais


def obter_live(url):
    """Retorna a URL de uma transmissão ao vivo confirmada."""

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

                if (
                    "Sign in to confirm" in erro
                    or "confirm you're not a bot" in erro.lower()
                ):
                    print("YouTube exige confirmação contra bots.")
                elif erro:
                    print(f"Falha de consulta: {erro[-300:]}")

                time.sleep(2)
                continue

            dados = json.loads(proc.stdout)
            entradas = dados.get("entries")
            candidatos = entradas if entradas else [dados]

            for item in candidatos:
                if not isinstance(item, dict):
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
                    nova_url = (
                        "https://www.youtube.com/watch?v=" + video_id
                    )
                    print(f"Live ativa encontrada: {nova_url}")
                    return nova_url

            print("Nenhuma transmissão ao vivo ativa encontrada.")

        except subprocess.TimeoutExpired:
            print(f"Tempo esgotado: {url}")
        except (json.JSONDecodeError, OSError) as erro:
            print(f"Erro na consulta: {erro}")

        time.sleep(2)

    print(f"Não foi possível confirmar uma live ativa: {url}")
    return None


def main():
    if not ARQUIVO_CANAIS.exists():
        raise FileNotFoundError("canais.txt não foi encontrado.")

    if not ARQUIVO_LISTA.exists():
        raise FileNotFoundError("youtube.txt não foi encontrado.")

    canais = ler_canais()

    if not canais:
        raise RuntimeError("Nenhum canal válido em canais.txt.")

    texto = ARQUIVO_LISTA.read_text(encoding="utf-8-sig")
    linhas = texto.splitlines()

    # Consulta cada canal cadastrado, sem nomes fixos no código.
    lives = {}

    for chave, canal in canais.items():
        print(f"\nConsultando canal: {canal['nome']}")
        lives[chave] = obter_live(canal["url"])

    resultado = []
    alteracoes = 0
    canais_encontrados = set()

    for linha in linhas:
        if not linha.strip() or linha.lstrip().startswith("#"):
            resultado.append(linha)
            continue

        partes = linha.split("|")

        # Formato: Tema|Categoria|Classificação|Título|URL
        if len(partes) != 5:
            resultado.append(linha)
            continue

        nome = partes[3].strip()
        url_atual = partes[4].strip()
        chave = normalizar_nome(nome)

        # Só processa canais cadastrados em canais.txt.
        if chave not in canais:
            resultado.append(linha)
            continue

        # Evita modificar links externos ou outras fontes.
        if not re.match(
            r"^https?://(www\.)?(youtube\.com|youtu\.be)/",
            url_atual,
            re.IGNORECASE,
        ):
            resultado.append(linha)
            print(f"Preservado: {nome} — URL não é do YouTube.")
            continue

        canais_encontrados.add(chave)
        nova_url = lives.get(chave)

        if not nova_url:
            print(f"Preservado: {nome} — live não confirmada.")
            resultado.append(linha)
            continue

        if url_atual != nova_url:
            partes[4] = nova_url
            linha = "|".join(partes)
            alteracoes += 1
            print(f"Atualizado: {nome} -> {nova_url}")
        else:
            print(f"Já atualizado: {nome}")

        resultado.append(linha)

    # Avisa quando há canal cadastrado sem linha correspondente.
    for chave, canal in canais.items():
        if chave not in canais_encontrados:
            print(
                f"ATENÇÃO: '{canal['nome']}' está em canais.txt, "
                "mas não tem linha correspondente válida em youtube.txt."
            )

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
