"""
Trilha e tempos de um episódio SEM narração (formato "Estude comigo": tela + texto + música).

    python montar_sem_voz.py videos/short-ep09-estude-comigo

Lê <episodio>/config.json com "sem_narracao": true:
  "duracao": 30,
  "cenas": [["abre", 0], ["grifa", 6.5], ...]        início de cada cena (s)
  "cues":  {"seleciona": 7.2, ...}                    eventos (s)
  "textos": [[0.3, 5.8, "Abrindo o art. 5º"], ...]    letreiros (s inicial, s final, texto)
  "sfx":   [["click", "cue:seleciona", 0, 0.8], ...]  como no montar_audio.py
  "bpm": 78,
  "estilo": "lofi" | "energetico"   (energetico: pop eletrônico com riser e impacto nas trocas de cena)
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


def pop_():
    """Pop curto (bolha): seno que sobe rápido, para letreiros e chips entrando."""
    x = tt(0.12)
    f = 380 + 900 * (1 - np.exp(-x * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.12, 0.001, 0.035) * 0.45


def impacto():
    """Batida grave de entrada de cena (o 'drop')."""
    x = tt(0.6)
    f = 120 * np.exp(-x * 9) + 38
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.6, 0.002, 0.2) * 0.9
            + rng.standard_normal(len(x)) * env(0.6, 0.0005, 0.015) * 0.3)


def riser(d=1.0):
    """Subida de ruído filtrado e tom antes da troca de cena: cria expectativa."""
    x = tt(d)
    n = rng.standard_normal(len(x)).astype(np.float32)
    k = x / d
    out = np.zeros_like(n)
    for i, w in enumerate(np.linspace(30, 2, 10)):
        a, b = int(i * len(n) / 10), int((i + 1) * len(n) / 10)
        out[a:b] = np.convolve(n, np.ones(int(w)) / w, mode="same")[a:b]
    tom = np.sin(2 * np.pi * np.cumsum(300 + 900 * k ** 2) / SR) * 0.15
    return (out * 0.25 + tom) * k ** 2


def confete():
    """Brilho de recompensa: arpejo rápido e agudo com cintilação."""
    out = chime((1046.5, 1318.5, 1568.0, 2093.0), d=0.9, vol=0.28, atraso=0.045)
    x = tt(len(out) / SR)
    return out + rng.standard_normal(len(out)) * env(len(out) / SR, 0.005, 0.25) * 0.03 * (np.sin(2 * np.pi * 30 * x) > 0)


SONS = {"click": click, "whoosh": whoosh, "marca": marca, "acerto": lambda: chime((659.3, 987.8)), "brilho": chime,
        "pop": pop_, "impacto": impacto, "riser": riser, "confete": confete}

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

# ── trilha ──────────────────────────────────────────────────────────────────────────────────────
bpm = CFG.get("bpm", 78)
bt = 60 / bpm
trilha = np.zeros_like(sfx)
x_all = np.arange(len(trilha)) / SR


def soma(som, quando, ganho=1.0):
    p = int(max(0, quando) * SR)
    q = min(len(trilha), p + len(som))
    if q > p:
        trilha[p:q] += som[: q - p].astype(np.float32) * ganho


if CFG.get("estilo", "lofi") == "energetico":
    # Pop eletrônico a ~120 BPM: bumbo em todos os tempos, palma no 2 e no 4, chimbal em colcheias,
    # baixo com "pump" (abaixa no bumbo), acordes em stab e arpejo em semicolcheias.
    # Progressão vi–IV–I–V (Lá menor): animada e sem tensão.
    prog_ = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    baixos = [55.0, 43.65, 65.41, 49.0]
    compassos = int(DUR / (4 * bt)) + 1
    pump = np.ones(len(trilha), np.float32)
    for b in range(int(DUR / bt) + 1):
        q = b * bt
        x = tt(0.3)
        soma(np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-x * 35)) / SR) * env(0.3, 0.002, 0.09), q, 0.30)  # bumbo
        # "pump": desce em 8 ms (sem rampa, a queda instantânea estalava em toda batida) e volta em 250 ms
        p0, p1 = int(q * SR), min(len(pump), int((q + 0.25) * SR))
        curva = 0.35 + 0.65 * np.linspace(0, 1, p1 - p0) ** 0.7
        desce = min(len(curva), int(0.008 * SR))
        curva[:desce] = np.linspace(1.0, curva[desce - 1] if desce else 1.0, desce)
        pump[p0:p1] = np.minimum(pump[p0:p1], curva)
        if b % 4 in (1, 3):  # palma
            xc = tt(0.18)
            palma = rng.standard_normal(len(xc)) * (env(0.18, 0.001, 0.05) + 0.6 * env(0.18, 0.012, 0.04))
            soma(np.convolve(palma, [1, -0.85], mode="same"), q, 0.22)
        for h in (0.5, ):  # chimbal no contratempo
            xh = tt(0.06)
            soma(np.diff(np.concatenate([[0], rng.standard_normal(len(xh))])) * env(0.06, 0.0005, 0.010), q + h * bt, 0.035)
    for c in range(compassos):
        acorde, f_b, ini = prog_[c % 4], baixos[c % 4], c * 4 * bt
        d = 4 * bt
        x = tt(d)
        baixo = (np.sin(2 * np.pi * f_b * x) + 0.6 * np.sin(2 * np.pi * 2 * f_b * x) + 0.3 * np.sin(2 * np.pi * 3 * f_b * x)) * 0.09
        soma(baixo * np.minimum(1, x / 0.02) * np.minimum(1, (d - x) / 0.05), ini)
        for k in range(8):  # stabs nos contratempos
            xs = tt(0.16)
            stab = sum(np.sin(2 * np.pi * f * xs) + 0.45 * np.sin(4 * np.pi * f * xs) + 0.2 * np.sin(6 * np.pi * f * xs) for f in acorde)
            soma(stab * env(0.16, 0.003, 0.07), ini + (k + 0.5) * bt / 2, 0.11)
        notas = [acorde[0] * 4, acorde[1] * 4, acorde[2] * 4, acorde[1] * 4]
        for k in range(16):  # arpejo
            xa = tt(0.14)
            f = notas[k % 4]
            nota = (np.sin(2 * np.pi * f * xa) + 0.4 * np.sin(2 * np.pi * 2 * f * xa) + 0.2 * np.sin(2 * np.pi * 3 * f * xa)) * env(0.14, 0.002, 0.05)
            soma(nota, ini + k * bt / 4, 0.17)
    trilha *= pump
    # subida antes de cada troca de cena e batida grave na entrada (as duas no tempo da música)
    for nome, c in list(cenas.items())[1:]:
        soma(riser(1.0), c["start"] - 1.0, 0.8)
        soma(impacto(), c["start"], 0.7)
    trilha *= np.minimum(1, x_all / 0.08) * np.clip((DUR - x_all) / 0.8, 0, 1)
else:
    # lofi: acordes com sétima, baixo, bumbo e caixa suaves, chiado de vinil
    acordes = [(174.6, 220.0, 261.6, 329.6), (146.8, 174.6, 220.0, 261.6), (164.8, 196.0, 246.9, 293.7), (130.8, 164.8, 196.0, 246.9)]
    for c in range(int(DUR / (4 * bt)) + 1):
        notas, d = acordes[c % 4], 4 * bt
        x = tt(d)
        pad = sum(np.sin(2 * np.pi * f * x) * (0.6 if i else 1.0) for i, f in enumerate(notas))
        pad += 0.5 * np.sin(2 * np.pi * notas[0] / 2 * x)
        soma(pad * np.minimum(1, x / 0.25) * np.minimum(1, (d - x) / 0.4) * 0.035, c * d)
    for b in range(int(DUR / bt) + 1):
        x = tt(0.22)
        som = (np.sin(2 * np.pi * (50 + 50 * np.exp(-x * 30)) * x) * env(0.22, 0.002, 0.07) * 0.2 if b % 2 == 0
               else rng.standard_normal(len(x)) * env(0.22, 0.001, 0.04) * 0.05)
        soma(som, b * bt)
    vinil = rng.standard_normal(len(trilha)).astype(np.float32)
    trilha += np.convolve(vinil, np.ones(20) / 20, mode="same") * 0.004
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
