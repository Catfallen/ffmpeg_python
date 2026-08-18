from pathlib import Path
from datetime import datetime
import subprocess
import sys
import re


ROOT = Path.cwd()


def log(mensagem: str):
    horario = datetime.now().strftime("%H:%M:%S")
    print(f"[{horario}] {mensagem}")


# ============================================================
# IDENTIFICAR TAG DE CORTE (segundos dinâmicos)
# ============================================================

def identificar_corte(video: Path):

    nome = video.stem.lower()

    # Padrão "jogadaXXs" ou "jogada-XXs" (qualquer número, em qualquer posição)
    match = re.search(r"jogada-?(\d+)s", nome)
    if match:
        return int(match.group(1))

    # Tag de segundos no final do nome, com ou sem separador:
    # "first25s", "existe30s", "pobre 15s", "video_15s", "video-90s"
    match = re.search(r"(\d+)s\s*$", nome)
    if match:
        return int(match.group(1))

    # Tag de minutos no final do nome, com ou sem separador:
    # "video1m", "video_2m", "video 5m"
    match = re.search(r"(\d+)m\s*$", nome)
    if match:
        return int(match.group(1)) * 60

    return None


# ============================================================
# REMOVER TAG DO NOME FINAL
# ============================================================

def gerar_nome_saida(video: Path):

    nome = video.stem

    # Remove tag "jogadaXXs" / "jogada-XXs" (em qualquer posição)
    nome = re.sub(
        r"[_\s-]?jogada-?\d+s",
        "",
        nome,
        flags=re.IGNORECASE
    )

    # Remove tag de segundos/minutos no final, com ou sem separador
    # (espaço, underscore, hífen, ou colada na palavra anterior)
    nome = re.sub(
        r"[\s_-]*\d+[sm]\s*$",
        "",
        nome,
        flags=re.IGNORECASE
    )

    # Remove separadores/espaços residuais no final
    nome = nome.rstrip("_- ")

    return video.with_name(
        f"{nome}{video.suffix}"
    )


# ============================================================
# PROCURAR ARQUIVOS
# ============================================================

def selecionar_origem():

    diretorios = sorted(
        [
            pasta for pasta in ROOT.iterdir()
            if pasta.is_dir()
            and not pasta.name.startswith(".")
            and not pasta.name.endswith("_cut")
        ],
        key=lambda p: p.name.lower()
    )

    arquivos = sorted(
        [
            arquivo for arquivo in ROOT.glob("*.mp4")
            if identificar_corte(arquivo) is not None
        ],
        key=lambda p: p.name.lower()
    )

    opcoes = []

    print("\nOpções disponíveis:\n")

    # Arquivos individuais
    for arquivo in arquivos:

        segundos = identificar_corte(arquivo)

        opcoes.append({
            "tipo": "arquivo",
            "caminho": arquivo
        })

        print(
            f"[{len(opcoes):02d}] "
            f"📄 {arquivo.name} "
            f"({segundos}s)"
        )

    # Diretórios
    for pasta in diretorios:

        quantidade = len(
            [
                video
                for video in pasta.glob("*.mp4")
                if identificar_corte(video) is not None
            ]
        )

        opcoes.append({
            "tipo": "diretorio",
            "caminho": pasta
        })

        print(
            f"[{len(opcoes):02d}] "
            f"📁 {pasta.name} "
            f"({quantidade} vídeos para cortar)"
        )

    if not opcoes:
        log(
            "Nenhum vídeo com _editavel e tag "
            "de corte encontrado."
        )
        sys.exit(0)

    while True:

        try:

            escolha = int(
                input("\nSelecione uma opção: ")
            )

            if 1 <= escolha <= len(opcoes):
                return opcoes[escolha - 1]

            log("Índice inválido.")

        except ValueError:
            log("Digite apenas números.")


# ============================================================
# ESCOLHER MODO
# ============================================================

def selecionar_modo():

    print("\nModo de operação:\n")

    print("[1] CUT")
    print("    Corta e mantém o original.")

    print("\n[2] CUT E DELETE")
    print("    Corta e apaga o original após sucesso.")

    while True:

        try:

            escolha = int(
                input("\nSelecione o modo: ")
            )

            if escolha == 1:
                return False

            if escolha == 2:
                return True

            log("Opção inválida.")

        except ValueError:
            log("Digite apenas números.")


# ============================================================
# SELEÇÃO
# ============================================================

selecao = selecionar_origem()

deletar_original = selecionar_modo()

tipo = selecao["tipo"]
origem = selecao["caminho"]


# ============================================================
# DEFINIR VÍDEOS
# ============================================================

if tipo == "arquivo":

    videos = [origem]

    PASTA_ORIGEM = ROOT
    PASTA_DESTINO = ROOT

    log("Modo: CORTE ÚNICO")

else:

    PASTA_ORIGEM = origem

    PASTA_DESTINO = (
        PASTA_ORIGEM.parent
        / f"{PASTA_ORIGEM.name}_cut"
    )

    PASTA_DESTINO.mkdir(exist_ok=True)

    videos = sorted(
        [
            video
            for video in PASTA_ORIGEM.glob("*.mp4")
            if identificar_corte(video) is not None
        ]
    )

    log("Modo: CORTE EM LOTE")


# ============================================================
# LOG INICIAL
# ============================================================

log(f"Origem : {origem}")
log(f"Destino: {PASTA_DESTINO}")
log(f"Vídeos encontrados: {len(videos)}")

if deletar_original:
    log("Operação: CUT E DELETE")
else:
    log("Operação: CUT")


# ============================================================
# PROCESSAMENTO
# ============================================================

for indice, video in enumerate(videos, start=1):

    segundos = identificar_corte(video)

    if segundos is None:
        continue

    nome_saida = gerar_nome_saida(video)

    saida = PASTA_DESTINO / nome_saida.name

    if saida.exists():

        log(
            f"[{indice}/{len(videos)}] "
            f"Ignorando '{saida.name}' "
            f"(já existe)."
        )

        continue


    log(
        f"[{indice}/{len(videos)}] "
        f"Cortando últimos {segundos}s: "
        f"'{video.name}'..."
    )


    # ========================================================
    # PEGAR DURAÇÃO DO VÍDEO
    # ========================================================

    comando_probe = [
        "ffprobe",

        "-v", "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(video)
    ]


    resultado_probe = subprocess.run(
        comando_probe,
        capture_output=True,
        text=True
    )


    if resultado_probe.returncode != 0:

        log(
            f"Erro ao obter duração de "
            f"'{video.name}'."
        )

        continue


    try:

        duracao = float(
            resultado_probe.stdout.strip()
        )

    except ValueError:

        log(
            f"Não foi possível determinar "
            f"a duração de '{video.name}'."
        )

        continue


    # Se o vídeo tiver menos que o tempo solicitado,
    # começa do início
    inicio = max(0, duracao - segundos)


    # ========================================================
    # FFMPEG
    # ========================================================

    comando = [

        "ffmpeg",

        "-ss",
        str(inicio),

        "-i",
        str(video),

        "-map",
        "0:v:0",

        "-map",
        "0:a?",

        "-c:v",
        "copy",

        "-c:a",
        "copy",

        "-movflags",
        "+faststart",

        "-y",

        str(saida)
    ]


    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )


    # ========================================================
    # RESULTADO
    # ========================================================

    if resultado.returncode == 0:

        tamanho_mb = (
            saida.stat().st_size
            / (1024 * 1024)
        )

        log(
            f"Concluído: '{saida.name}' "
            f"({tamanho_mb:.2f} MB)"
        )


        # ====================================================
        # DELETE
        # ====================================================

        if deletar_original:

            try:

                video.unlink()

                log(
                    f"Original removido: "
                    f"'{video.name}'"
                )

            except OSError as erro:

                log(
                    f"Não foi possível apagar "
                    f"'{video.name}': {erro}"
                )

    else:

        log(
            f"Erro ao cortar '{video.name}'"
        )

        print(
            "\n===== LOG DO FFMPEG ====="
        )

        print(resultado.stderr)

        print(
            "=========================\n"
        )


log("Processamento finalizado.")