
import json
import subprocess
from pathlib import Path

ARQUIVO = Path("youtube.txt")

CANAIS = [
    {
        "chave": "cnn",
        "nome": "CNN Brasil Ao Vivo",
        "url": "https://www.youtube.com/@CNNbrasil/live",
    },
    {
        "chave": "bandnews",
        "nome": "BandNews Ao Vivo",
        "url": "https://www.youtube.com/@bandnewstv/live",
    },
    {
        "chave": "sbt news",
        "nome": "SBT News Ao Vivo",
        "url": "https://www.youtube.com/@sbtnews/live",
    },
]


def localizar_canal(nome):
    nome = nome.lower().strip()

    if "cnn" in nome:
        return CANAIS[0]

    if "bandnews" in nome:
        return CANAIS[1]

    if "sbt" in nome and "news" in nome:
        return CANAIS[2]

    return None


def obter_live(url):
    """Retorna o link do vídeo somente se houver live ativa."""

    try:
        resultado = subprocess.run(
            [
                "yt-dlp",
                "--dump-single-json",
                "--no-warnings",
                "--no-playlist",
                "--skip-download",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )

        if resultado.returncode != 0 or not resultado.stdout.strip():
            print(f"Não foi possível consultar: {url}")
            if resultado.stderr:
                print(resultado.stderr[-500:])
            return None

        dados = json.loads(resultado.stdout)

        # Alguns extratores podem devolver uma coleção de vídeos.
        entradas = dados.get("entries")
        if entradas:
            dados = next(
                (
                    item for item in entradas
                    if item
                    and (
                        item.get("is_live") is True
                        or item.get("live_status") == "is_live"
                    )
                ),
                {},
            )

        esta_ao_vivo = (
            dados.get("is_live") is True
            or dados.get("live_status") == "is_live"
        )

        video_id = dados.get("id")

        if esta_ao_vivo and video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

        print(f"Nenhuma transmissão ativa encontrada: {url}")
        return None

    except Exception as erro:
        print(f"Erro consultando {url}: {erro}")
        return None


def main():
    if not ARQUIVO.exists():
        raise FileNotFoundError("O arquivo youtube.txt não existe.")

    linhas = ARQUIVO.read_text(encoding="utf-8-sig").splitlines()
    novas_linhas = []
    encontrados = set()

    for linha in linhas:
        partes = linha.split("|")

        if len(partes) < 3 or linha.lstrip().startswith("#"):
            novas_linhas.append(linha)
            continue

        canal = localizar_canal(partes[1])

        if canal is None:
            novas_linhas.append(linha)
            continue

        encontrados.add(canal["chave"])

        # Se não houver live ativa, usa o endereço permanente /live.
        novo_link = obter_live(canal["url"])
        if not novo_link:
            novo_link = canal["url"]

        partes[2] = novo_link
        nova_linha = "|".join(partes)
        novas_linhas.append(nova_linha)

        print(f"{partes[1]} -> {novo_link}")

    # Adiciona os canais que ainda não estão no arquivo.
    for canal in CANAIS:
        if canal["chave"] not in encontrados:
            novo_link = obter_live(canal["url"]) or canal["url"]
            novas_linhas.append(
                f"Notícias|{canal['nome']}|{novo_link}"
            )
            print(f"Adicionado: {canal['nome']} -> {novo_link}")

    conteudo = "\n".join(novas_linhas) + "\n"
    ARQUIVO.write_text(conteudo, encoding="utf-8")

    print("Atualização de youtube.txt concluída.")


if __name__ == "__main__":
    main()
