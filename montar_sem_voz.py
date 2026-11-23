"""
Trilha e tempos de um episódio SEM narração (formato "Estude comigo": tela + texto + música).

    python montar_sem_voz.py videos/short-ep09-estude-comigo

Lê <episodio>/config.json com "sem_narracao": true:
  "duracao": 30,
  "cenas": [["abre", 0], ["grifa", 6.5], ...]        início de cada cena (s)
  "cues":  {"seleciona": 7.2, ...}                    eventos (s)
  "textos": [[0.3, 5.8, "Abrindo o art. 5º"], ...]    letreiros (s inicial, s final, texto)
  "sfx":   [["click", "cue:seleciona", 0, 0.8], ...]  como no montar_audio.py
  "bpm": 78
Saídas: timing.json (cenas, eventos, letreiros; sem legenda de fala) e audio/mix.wav (trilha +
efeitos) e audio/mix_sem_trilha.wav (só efeitos, para pôr uma música do próprio app por cima).
Os sons são sintetizados (sem direitos de terceiros). Requer numpy, soundfile e ffmpeg.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from loudness import normalizar

if len(sys.argv) < 2:
    sys.exit("Uso: python montar_sem_voz.py <pasta do episódio>")
EP = Path(sys.argv[1])
CFG = json.loads((EP / "config.json").read_text(encoding="utf-8"))
if not CFG.get("sem_narracao"):
    sys.exit("config.json sem \"sem_narracao\": true — use o montar_audio.py.")
SR = 48000
DUR = float(CFG["duracao"])
rng = np.random.default_rng(11)
tt = lambda d: np.arange(int(d * SR)) / SR


def env(d, a=0.005, r=0.2):
    x = tt(d)
    return np.minimum(1, x / a) * np.exp(-x / r)


def click():
    x = tt(0.05)
    return rng.standard_normal(len(x)) * env(0.05, 0.0005, 0.006) * 0.35 + np.sin(2 * np.pi * 2200 * x) * env(0.05, 0.0005, 0.01) * 0.2


def pluck(f=660):
    x = tt(0.3)
    return np.sin(2 * np.pi * f * x) * env(0.3, 0.002, 0.08) * 0.2


def chime(notas=(1046.5, 1318.5, 1568.0), d=1.0, vol=0.3, atraso=0.06):
    out = np.zeros(int((d + atraso * len(notas)) * SR), np.float32)
    for i, f in enumerate(notas):
        x = tt(d)
        tom = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * env(d, 0.004, 0.35)
        out[int(i * atraso * SR): int(i * atraso * SR) + len(tom)] += tom
    return out * vol


def whoosh(d=0.38):
    n = rng.standard_normal(int(d * SR)).astype(np.float32)
    out = np.zeros_like(n)
    for k, w in enumerate(np.linspace(40, 4, 8)):
        a, b = int(k * len(n) / 8), int((k + 1) * len(n) / 8)
        out[a:b] = np.convolve(n, np.ones(int(w)) / w, mode="same")[a:b]
    return out * np.sin(np.pi * tt(d) / d) ** 2 * 0.3


def marca():
    """Marca-texto correndo: chiado curto e suave."""
    d = 0.45
    n = rng.standard_normal(int(d * SR)).astype(np.float32)
    n = np.convolve(n, np.ones(6) / 6, mode="same")
    return n * np.sin(np.pi * tt(d) / d) * 0.08


SONS = {"click": click, "whoosh": whoosh, "marca": marca, "acerto": lambda: chime((659.3, 987.8)), "brilho": chime}

cues = {k: float(v) for k, v in CFG.get("cues", {}).items()}
inicios = [(c, float(s)) for c, s in CFG["cenas"]]
cenas = {c: {"start": round(s, 3), "end": round(inicios[i + 1][1] if i + 1 < len(inicios) else DUR, 3)} for i, (c, s) in enumerate(inicios)}

sfx = np.zeros(int(DUR * SR) + SR, np.float32)
for tipo, alvo, desloc, ganho in CFG.get("sfx", []):
    t_alvo = cues[alvo.split(":")[1]] if alvo.startswith("cue:") else cenas[alvo.split(":")[1]]["start"]
    som = pluck(float(tipo.split(":")[1])) if tipo.startswith("pluck:") else SONS[tipo]()
    a = int(max(0, t_alvo + desloc) * SR)
    b = min(len(sfx), a + len(som))
    sfx[a:b] += som[: b - a].astype(np.float32) * ganho

# ── trilha lofi: acordes com sétima, baixo, bumbo e caixa suaves, chiado de vinil ───────────────
bpm = CFG.get("bpm", 78)
bt = 60 / bpm
trilha = np.zeros_like(sfx)
acordes = [(174.6, 220.0, 261.6, 329.6), (146.8, 174.6, 220.0, 261.6), (164.8, 196.0, 246.9, 293.7), (130.8, 164.8, 196.0, 246.9)]
for c in range(int(DUR / (4 * bt)) + 1):
    notas, a, d = acordes[c % 4], int(c * 4 * bt * SR), 4 * bt
    x = tt(d)
    pad = sum(np.sin(2 * np.pi * f * x) * (0.6 if i else 1.0) for i, f in enumerate(notas))
    pad += 0.5 * np.sin(2 * np.pi * notas[0] / 2 * x)  # baixo
    pad *= np.minimum(1, x / 0.25) * np.minimum(1, (d - x) / 0.4) * 0.035
    trilha[a: a + len(pad)] += pad[: max(0, min(len(pad), len(trilha) - a))]
for b in range(int(DUR / bt) + 1):
    p = int(b * bt * SR)
    x = tt(0.22)
    if b % 2 == 0:
        som = np.sin(2 * np.pi * (50 + 50 * np.exp(-x * 30)) * x) * env(0.22, 0.002, 0.07) * 0.2
    else:
        som = rng.standard_normal(len(x)) * env(0.22, 0.001, 0.04) * 0.05
    trilha[p: p + len(som)] += som[: max(0, min(len(som), len(trilha) - p))]
vinil = rng.standard_normal(len(trilha)).astype(np.float32)
trilha += np.convolve(vinil, np.ones(20) / 20, mode="same") * 0.004
x_all = np.arange(len(trilha)) / SR
trilha *= np.minimum(1, x_all / 0.6) * np.clip((DUR - x_all) / 1.2, 0, 1)

saida = EP / "audio"
saida.mkdir(exist_ok=True)
total = int(DUR * SR)


def exportar(nome, partes):
    mix = sum(partes)[:total]
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, mix / max(1.0, np.abs(mix).max()), SR)
        normalizar(tmp.name, saida / nome, SR)  # duas passadas (loudness.py)


exportar("mix.wav", [trilha, sfx * 0.6])
exportar("mix_sem_trilha.wav", [sfx * 0.6 + 1e-4 * rng.standard_normal(len(sfx))])
(EP / "timing.json").write_text(json.dumps({"duration": DUR, "scenes": cenas, "cues": cues, "textos": CFG.get("textos", []),
                                            "chunks": [], "words": []}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"ok: {DUR:.1f} s, {len(cenas)} cenas, {len(cues)} eventos")
