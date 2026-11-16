"""
Narração com F5-TTS treinado em ~200 h de português brasileiro (licença NÃO comercial, CC-BY-NC).

    python gerar_f5.py roteiro.txt saida.wav referencias/cv_191.wav
"""
import argparse, re, sys, numpy as np, soundfile as sf
from pathlib import Path
BASE = Path(__file__).parent; sys.path.insert(0, str(BASE))
from verificador import erro

ap = argparse.ArgumentParser()
ap.add_argument("texto"); ap.add_argument("saida"); ap.add_argument("referencia")
ap.add_argument("--tentativas", type=int, default=2)
ap.add_argument("--velocidade", type=float, default=1.0)
ap.add_argument("--nfe", type=int, default=32)
ap.add_argument("--pausa_ms", type=int, default=280)
a = ap.parse_args()

from f5_tts.api import F5TTS
tts = F5TTS(model="F5TTS_Base", ckpt_file=str(BASE / "modelos/f5/model_last.safetensors"), device="cpu")
ref_txt = Path(a.referencia).with_suffix(".txt").read_text(encoding="utf-8")

texto = Path(a.texto).read_text(encoding="utf-8")
# F5 rende melhor com trechos curtos: quebra o parágrafo em frases, mas junta
# frases curtas para manter o encadeamento
blocos = []
for p in [" ".join(x.split()) for x in re.split(r"\n\s*\n", texto) if x.strip()]:
    frases = re.split(r"(?<=[.!?])\s+", p); atual = ""
    for f in frases:
        if len((atual + " " + f).split()) <= 28: atual = (atual + " " + f).strip()
        else: blocos.append((atual, False)); atual = f
    blocos.append((atual, True))

saida = []
for n, (b, fim_par) in enumerate(blocos, 1):
    melhor = None
    for t in range(a.tentativas):
        y, sr, _ = tts.infer(ref_file=a.referencia, ref_text=ref_txt, gen_text=b,
                             nfe_step=a.nfe, speed=a.velocidade, seed=100 * n + t, remove_silence=False)
        e, hip = erro(b, y, sr)
        print(f"  trecho {n} tentativa {t+1}: erro {e*100:.0f}%", flush=True)
        if melhor is None or e < melhor[0]: melhor = (e, y, hip)
        if e <= 0.02: break
    if melhor[0] > 0.02: print(f"  ⚠ trecho {n}: {melhor[0]*100:.0f}% -> ouviu: {melhor[2]}", flush=True)
    saida += [melhor[1], np.zeros(int(sr * (a.pausa_ms if fim_par else 90) / 1000), np.float32)]

import tempfile, voz
with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
    sf.write(tmp.name, np.concatenate(saida), sr); voz.pos_producao(tmp.name, a.saida)
print("ok ->", a.saida)
