"""
Gerador de narração pt-BR para Reels jurídicos — 100% open-source e offline.

Uso:
    python voz.py texto.txt saida.wav                 # usa a voz padrão (config.json)
    python voz.py texto.txt saida.wav --motor piper --voz faber-medium
    python voz.py texto.txt saida.wav --motor kokoro --voz pm_alex --velocidade 0.95

Pipeline (cada etapa tem base em acústica/percepção da fala):
  1. Divide o texto em parágrafos e frases (grupos respiratórios).
  2. Sintetiza frase a frase (evita a prosódia "achatada" de blocos longos).
  3. Insere pausas: ~320 ms entre frases, ~650 ms entre parágrafos.
  4. Pós-produção com ffmpeg: filtro passa-alta, EQ de presença,
     de-esser, compressão leve e normalização para -14 LUFS (padrão Instagram).
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- texto
def dividir(texto: str):
    """Retorna lista de parágrafos; cada parágrafo é uma lista de frases."""
    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    return [
        [f.strip() for f in re.split(r"(?<=[.!?])\s+", p.replace("\n", " ")) if f.strip()]
        for p in paragrafos
    ]


# ---------------------------------------------------------------- motores
class Kokoro:
    sr = 24000

    def __init__(self, voz, velocidade):
        from kokoro import KPipeline
        self.p = KPipeline(lang_code="p", repo_id="hexgrad/Kokoro-82M")
        self.voz, self.vel = voz, velocidade

    def falar(self, frase):
        partes = [a.numpy() if hasattr(a, "numpy") else a
                  for _, _, a in self.p(frase, voice=self.voz, speed=self.vel)]
        return np.concatenate(partes)


class Piper:
    sr = 22050

    def __init__(self, voz, velocidade):
        from piper import PiperVoice, SynthesisConfig
        self.v = PiperVoice.load(str(BASE / "modelos/piper" / f"pt_BR-{voz}.onnx"))
        self.sr = self.v.config.sample_rate
        # length_scale > 1 = mais lento; noise_w controla variação de ritmo
        self.cfg = SynthesisConfig(length_scale=1 / velocidade,
                                   noise_scale=0.667, noise_w_scale=0.9)

    def falar(self, frase):
        # Piper devolve uma frase por pedaço; o corte já deixa ~150 ms de respiro
        gap = np.zeros(int(self.sr * 0.04), np.float32)
        pedacos = []
        for c in self.v.synthesize(frase, self.cfg):
            pedacos += [aparar(c.audio_float_array), gap]
        return np.concatenate(pedacos[:-1])


MOTORES = {"kokoro": Kokoro, "piper": Piper}


# ---------------------------------------------------------------- áudio
def aparar(a, limiar=0.003, sr=24000):
    """Remove silêncio do começo/fim sem comer fricativas ("s", "f") de baixa energia."""
    idx = np.where(np.abs(a) > limiar)[0]
    return a[max(idx[0] - int(0.04 * sr), 0): idx[-1] + int(0.06 * sr)] if len(idx) else a


def pos_producao(entrada, saida, voz_grave=True):
    pp = CONFIG["pos_producao"]
    filtros = [
        f"highpass=f={pp['passa_alta_hz']}",                        # tira ronco/sub-grave
        # corpo/calor: região da F0 masculina (85–180 Hz) e 1º harmônico
        f"equalizer=f={150 if voz_grave else 220}:t=q:w=1:g={pp['ganho_corpo_db']}",
        "equalizer=f=350:t=q:w=1.2:g=-1.5",                          # tira "som de caixa"
        # presença: 2–4 kHz é onde o ouvido humano é mais sensível (curvas
        # isofônicas) e onde estão as pistas das consoantes -> inteligibilidade
        f"equalizer=f=3000:t=q:w=1:g={pp['ganho_presenca_db']}",
        "deesser=i=0.4:m=0.5:f=0.5",                                 # suaviza "s" e "x"
        "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2",
        f"loudnorm=I={pp['lufs']}:TP=-1.5:LRA=7",                    # -14 LUFS (Instagram)
        "aresample=48000",                                           # padrão de vídeo
    ]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(entrada),
                    "-af", ",".join(filtros), "-ar", "48000", str(saida)], check=True)


def gerar(texto, saida, motor, voz, velocidade):
    m = MOTORES[motor](voz, velocidade)
    pf = CONFIG["pausas_ms"]
    sil = lambda ms: np.zeros(int(m.sr * ms / 1000), dtype=np.float32)

    blocos = [sil(200)]
    for paragrafo in dividir(texto):
        # parágrafo INTEIRO numa chamada: o modelo planeja a melodia da frase
        # seguinte e encadeia as frases como um humano (sem "fala travada")
        blocos.append(aparar(m.falar(" ".join(paragrafo))).astype(np.float32))
        blocos.append(sil(pf["paragrafo"]))
    blocos.append(sil(300))

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, np.concatenate(blocos), m.sr)
        pos_producao(tmp.name, saida, voz_grave=not voz.startswith(("pf_", "if_")))
    print(f"ok -> {saida}")


if __name__ == "__main__":
    pad = CONFIG["voz_padrao"]
    ap = argparse.ArgumentParser()
    ap.add_argument("texto"); ap.add_argument("saida")
    ap.add_argument("--motor", default=pad["motor"], choices=MOTORES)
    ap.add_argument("--voz", default=pad["voz"])
    ap.add_argument("--velocidade", type=float, default=pad["velocidade"])
    a = ap.parse_args()
    gerar(Path(a.texto).read_text(encoding="utf-8"), a.saida, a.motor, a.voz, a.velocidade)
