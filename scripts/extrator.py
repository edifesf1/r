
import re
import html
import time
import os
import unicodedata
from urllib.request import Request, urlopen
from urllib.parse import urlparse, unquote

BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "linksm3u8"
)

ENTRADA = os.path.join(BASE, "links.txt")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9"
}


def baixar(url):
    req = Request(url, headers=HEADERS)

    with urlopen(req, timeout=30) as resposta:
        return resposta.read().decode("utf-8", errors="replace")


def normalizar(codigo):
    codigo = html.unescape(codigo)

    substituicoes = {
        r"\/": "/",
        r"\u0026": "&",
        r"\u003d": "=",
        r"\u003f": "?",
        r"\x26": "&",
        r"\x3d": "=",
        r"\x3f": "?"
    }

    for antigo, novo in substituicoes.items():
        codigo = codigo.replace(antigo, novo)

    return codigo


def extrair_m3u8(codigo):
    codigo = normalizar(codigo)
    encontrados = []

    # Procura URLs M3U8 diretamente no HTML
    padrao = re.compile(
        r"""https?://[^\s"'<>\\]+?\.m3u8(?:\?[^\s"'<>\\]*)?""",
        re.IGNORECASE
    )

    for endereco in padrao.findall(codigo):
        endereco = endereco.rstrip("),;]}")

        if endereco not in encontrados:
            encontrados.append(endereco)

    # Procura URLs dentro de propriedades comuns de players
    padroes_player = [
        r"""data-stream-url\s*=\s*["']([^"']+)["']""",
        r"""["']hls["']\s*:\s*["']([^"']+)["']""",
        r"""\bhls\s*:\s*["']([^"']+)["']"""
    ]

    for padrao_player in padroes_player:
        for endereco in re.findall(
            padrao_player, codigo, re.IGNORECASE
        ):
            endereco = html.unescape(endereco.strip())
            endereco = endereco.replace(r"\/", "/")

            if endereco.startswith(("http://", "https://")):
                if ".m3u8" in endereco.lower():
                    if endereco not in encontrados:
                        encontrados.append(endereco)

    # Tenta decodificar URLs que estejam codificadas
    for endereco in list(encontrados):
        decodificado = unquote(endereco)

        if decodificado.startswith(("http://", "https://")):
            if ".m3u8" in decodificado.lower():
                if decodificado not in encontrados:
                    encontrados.append(decodificado)

    return encontrados


def nome_arquivo(nome):
    nome = unicodedata.normalize("NFKD", nome)
    nome = nome.encode("ascii", "ignore").decode("ascii")
    nome = nome.lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    return nome.strip("_") or "canal"


def salvar_playlist(canal, grupo, endereco):
    arquivo = nome_arquivo(canal) + ".m3u8"
    destino = os.path.join(BASE, arquivo)

    conteudo = (
        "#EXTM3U\n"
        f'#EXTINF:-1 tvg-name="{canal}" group-title="{grupo}",{canal}\n'
        f"{endereco}\n"
    )

    with open(destino, "w", encoding="utf-8") as f:
        f.write(conteudo)

    return arquivo


def processar():
    if not os.path.exists(ENTRADA):
        print("Arquivo links.txt não encontrado.")
        return

    with open(ENTRADA, "r", encoding="utf-8-sig") as f:
        linhas = [
            linha.strip()
            for linha in f
            if linha.strip() and not linha.strip().startswith("#")
        ]

    total = 0
    erros = 0

    for linha in linhas:
        partes = linha.split("|", 2)

        if len(partes) < 2:
            print("Cadastro inválido. Linha ignorada.")
            erros += 1
            continue

        canal = partes[0].strip()
        pagina = partes[1].strip()
        grupo = partes[2].strip() if len(partes) > 2 else "Canais"

        if not canal or not pagina:
            print("Nome ou endereço vazio. Linha ignorada.")
            erros += 1
            continue

        if "COLOQUE_AQUI" in pagina:
            print(f"{canal}: falta configurar o endereço.")
            continue

        print(f"\nVerificando: {canal}")

        try:
            time.sleep(2)

            # Também aceita um endereço M3U8 direto
            if ".m3u8" in pagina.lower():
                enderecos = [pagina]
            else:
                codigo = baixar(pagina)
                enderecos = extrair_m3u8(codigo)

            if not enderecos:
                print(f"{canal}: nenhum M3U8 encontrado.")
                erros += 1
                continue

            # Salva o primeiro endereço encontrado
            arquivo = salvar_playlist(
                canal, grupo, enderecos[0]
            )

            host = urlparse(enderecos[0]).netloc
            print(f"{canal}: atualizado em {arquivo} ({host})")
            total += 1

        except Exception as erro:
            # Não imprime a URL completa, que pode conter token
            print(f"{canal}: erro na consulta: {type(erro).__name__}")
            erros += 1

    print("\n------------------------------")
    print("PROCESSAMENTO CONCLUÍDO")
    print("Canais atualizados:", total)
    print("Canais com erro:", erros)
    print("------------------------------")


if __name__ == "__main__":
    processar()
