from pathlib import Path
from datetime import datetime
import subprocess
import sys


ROOT = Path.cwd()


def log(mensagem: str):
    horario = datetime.now().strftime("%H:%M:%S")
    print(f"[{horario}] {mensagem}")


def selecionar_origem():
    diretorios = sorted(
        [
            pasta for pasta in ROOT.iterdir()
            if pasta.is_dir() and not pasta.name.startswith(".")
        ],
        key=lambda p: p.name.lower()
    )

    arquivos = sorted(
        [
            arquivo for arquivo in ROOT.glob("*.mp4")
            if not arquivo.stem.endswith("_editavel")
        ],
        key=lambda p: p.name.lower()
    )

    opcoes = []

    print("\nOpções disponíveis:\n")

    # Arquivos individuais na raiz
    for arquivo in arquivos:
        opcoes.append({
            "tipo": "arquivo",
            "caminho": arquivo
        })

        print(
            f"[{len(opcoes):02d}] "
            f"📄 {arquivo.name} (conversão única)"
        )

    # Diretórios para conversão em lote
    for pasta in diretorios:
        quantidade = len(
            [
                video for video in pasta.glob("*.mp4")
                if not video.stem.endswith("_editavel")
            ]
        )

        opcoes.append({
            "tipo": "diretorio",
            "caminho": pasta
        })

        print(
            f"[{len(opcoes):02d}] "
            f"📁 {pasta.name} ({quantidade} vídeos)"
        )

    if not opcoes:
        log("Nenhum arquivo MP4 ou diretório encontrado.")
        sys.exit(1)

    while True:
        try:
            escolha = int(input("\nSelecione uma opção: "))

            if 1 <= escolha <= len(opcoes):
                return opcoes[escolha - 1]

            log("Índice inválido.")

        except ValueError:
            log("Digite apenas números.")


# ============================================================
# SELEÇÃO
# ============================================================

selecao = selecionar_origem()

tipo = selecao["tipo"]
origem = selecao["caminho"]


# ============================================================
# CONVERSÃO ÚNICA
# ============================================================

if tipo == "arquivo":

    video = origem

    # Salva o convertido na raiz
    PASTA_ORIGEM = ROOT
    PASTA_DESTINO = ROOT

    videos = [video]

    log("Modo: CONVERSÃO ÚNICA")


# ============================================================
# CONVERSÃO EM LOTE
# ============================================================

else:

    PASTA_ORIGEM = origem

    PASTA_DESTINO = (
        PASTA_ORIGEM.parent
        / f"{PASTA_ORIGEM.name}_convert"
    )

    PASTA_DESTINO.mkdir(exist_ok=True)

    videos = sorted(
        [
            video for video in PASTA_ORIGEM.glob("*.mp4")
            if not video.stem.endswith("_editavel")
        ]
    )

    log("Modo: CONVERSÃO EM LOTE")


# ============================================================
# VALIDAÇÃO
# ============================================================

if not videos:
    log("Nenhum arquivo MP4 encontrado.")
    sys.exit(0)


log(f"Origem : {origem}")
log(f"Destino: {PASTA_DESTINO}")
log(f"Vídeos encontrados: {len(videos)}")


# ============================================================
# CONVERSÃO
# ============================================================

for indice, video in enumerate(videos, start=1):

    saida = PASTA_DESTINO / f"{video.stem}_editavel.mp4"

    if saida.exists():
        log(
            f"[{indice}/{len(videos)}] "
            f"Ignorando '{saida.name}' (já existe)."
        )
        continue

    comando = [
        "ffmpeg",

        "-hwaccel", "cuda",

        "-i", str(video),

        "-map", "0:v:0",
        "-map", "0:a:0",

        "-c:v", "h264_nvenc",

        "-preset", "p7",
        "-tune", "hq",

        "-rc", "vbr",
        "-cq", "18",

        "-b:v", "20M",
        "-maxrate", "30M",
        "-bufsize", "60M",

        "-c:a", "aac",
        "-b:a", "320k",

        "-movflags", "+faststart",

        "-y",
        str(saida)
    ]

    log(
        f"[{indice}/{len(videos)}] "
        f"Convertendo '{video.name}'..."
    )

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    if resultado.returncode == 0:

        tamanho_mb = saida.stat().st_size / (1024 * 1024)

        log(
            f"Concluído: '{saida.name}' "
            f"({tamanho_mb:.2f} MB)"
        )

    else:

        log(f"Erro ao converter '{video.name}'")

        print("\n===== LOG DO FFMPEG =====")
        print(resultado.stderr)
        print("=========================\n")


log("Conversão finalizada.")