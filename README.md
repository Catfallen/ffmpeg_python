# ffmpeg_python

Ferramenta de linha de comando (sem interface gráfica) para conversão e edição de vídeos, priorizando qualidade — já que softwares como o Medal costumam recodificar o arquivo original com perda perceptível de qualidade.

## Funcionalidades

- **Conversão de formato** priorizando qualidade sobre tamanho de arquivo
- **Processamento em lote**, convertendo pastas inteiras de uma vez
- **Corte dinâmico** dos segundos/minutos finais do vídeo, via tags no nome do arquivo (ex: `video_30s.mp4`, `clip 15s.mp4`, `jogada-1m.mp4`)

## Requisitos

- Python 3.x
- [ffmpeg](https://ffmpeg.org/download.html) instalado e com o executável disponível no `PATH` do sistema

Verifique se o ffmpeg está acessível rodando:

```bash
ffmpeg -version
```

## Instalação

O projeto usa apenas bibliotecas nativas do Python (`pathlib`, `subprocess`, `re`, etc.) — não há dependências externas para instalar via pip. Basta ter o Python 3 e o ffmpeg configurados:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux/macOS
```

## Uso

### Corte dinâmico por tag

Renomeie o arquivo com uma tag de tempo no final do nome (`Xs` para segundos, `Xm` para minutos) e rode:

```bash
python cut.py
```

O script varre a pasta atual em busca de vídeos com tag reconhecível, lista as opções (arquivo único ou pasta inteira) e pergunta se o original deve ser mantido (`CUT`) ou apagado após o corte (`CUT E DELETE`).

Exemplos de nomes aceitos:

| Nome do arquivo         | Corte aplicado      |
|--------------------------|---------------------|
| `melhor jogada 30s.mp4`  | últimos 30 segundos |
| `gol incrivel_1m.mp4`    | último 1 minuto     |
| `highlight90s.mp4`       | últimos 90 segundos |

Os vídeos processados em lote são salvos em uma subpasta `<nome_da_pasta>_cut`.

## Observações

- Nenhuma biblioteca externa de vídeo é usada diretamente em Python — todo o processamento pesado é delegado ao `ffmpeg`/`ffprobe` via `subprocess`.
- O corte usa `-c:v copy` e `-c:a copy` (sem recodificação), o que torna o processo rápido e sem perda de qualidade.
