"""
Normalização de volume (EBU R128) para os montadores de áudio: −14 LUFS e pico real ≤ −1,5 dBTP.

A passada única do loudnorm do ffmpeg erra o alvo quando o áudio tem trechos longos de silêncio
(contagens de quiz, vídeo sem voz): no #8 saiu −16,5 LUFS no lugar de −14 e, no #9, pico de
−0,5 dBTP. O modo linear de duas passadas também não resolve: recusa subir o volume quando um
efeito (som de acerto) passaria do pico. Aqui: mede, aplica o ganho que falta com um limitador de
picos superamostrado (4×, controla o pico real entre amostras) e corrige o ganho numa 2ª iteração.
"""
import re, subprocess


def medir(arquivo):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(arquivo), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    resumo = err[err.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", resumo).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", resumo).group(1))


def normalizar(entrada, saida, sr=48000, alvo=-14.0, pico=-1.5):
    limite = 10 ** ((pico - 0.3) / 20)  # margem de 0,3 dB para o pico real depois de voltar a 48 kHz
    integrado, _ = medir(entrada)
    ganho = alvo - integrado
    for _ in range(2):
        filtro = (f"volume={ganho:.2f}dB,aresample={sr * 4},alimiter=limit={limite:.4f}:attack=1:release=50:level=false,"
                  f"aresample={sr}")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(entrada), "-af", filtro, "-ar", str(sr), str(saida)], check=True)
        integrado, _ = medir(saida)
        if abs(alvo - integrado) <= 0.3:
            break
        ganho += alvo - integrado
