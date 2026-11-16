"""
Monta a trilha do Short e o arquivo de tempos (timing.json) que comanda a animação.

    python video/shorts/montar_audio.py

Entradas: video/shorts/narracao/p1.wav … p6.wav (falas brutas, sem pós-produção, geradas com a
voz v2 do projeto voz-video: `gerar_clonada.py pN.txt pN.wav --preset v2 --sem_pos`).

Saídas:
  video/shorts/timing.json            cenas, eventos (cues) e legenda palavra por palavra
  video/shorts/audio/mix.wav          voz + efeitos + trilha discreta (-14 LUFS)
  video/shorts/audio/mix_sem_trilha.wav  voz + efeitos (para pôr uma música do YouTube por cima)

Requer: numpy, soundfile, faster-whisper e ffmpeg. VOZ_DIR aponta para o projeto voz-video
(pós-produção da voz igual à dos outros vídeos).
"""
import difflib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

AQUI = Path(__file__).parent
NARR = AQUI / "narracao"
SAIDA = AQUI / "audio"
SR = 48000
VOZ_DIR = Path(os.environ.get("VOZ_DIR", "/home/user/voz-video"))

# ── 1. Falas: carrega, apara e posiciona ─────────────────────────────────────────────────────

# Ritmo de Shorts: a fala é acelerada sem mudar o tom (atempo do ffmpeg, que preserva a altura).
VELOCIDADE = float(os.environ.get("VELOCIDADE", "1.08"))


def carregar(n):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(NARR / f"p{n}.wav"),
                        "-af", f"atempo={VELOCIDADE}", tmp.name], check=True)
        y, sr = sf.read(tmp.name, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr != SR:
        import librosa
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    i = np.where(np.abs(y) > 0.004)[0]
    return y[max(i[0] - int(0.04 * SR), 0): i[-1] + int(0.08 * SR)]


TEXTOS = {n: (NARR / f"p{n}.txt").read_text(encoding="utf-8").strip() for n in range(1, 7)}
FALAS = {n: carregar(n) for n in range(1, 7)}

# Pausas entre as falas (s). O quiz tem a contagem de 2,4 s sem fala: é o "tempo de responder".
LEAD = 0.10
GAP = {2: 0.22, 3: 0.32, 5: 0.32, 6: 0.30}
TIMER = 2.4

inicio = {}
t = LEAD
for n in range(1, 7):
    if n == 4:
        t = inicio[3] + len(FALAS[3]) / SR + 0.15 + TIMER + 0.05
    elif n > 1:
        t = inicio[n - 1] + len(FALAS[n - 1]) / SR + GAP[n]
    inicio[n] = t
fim6 = inicio[6] + len(FALAS[6]) / SR
DURACAO = round(fim6 + 1.4, 2)

voz = np.zeros(int(DURACAO * SR) + SR, np.float32)
for n, y in FALAS.items():
    a = int(inicio[n] * SR)
    voz[a: a + len(y)] += y

# ── 2. Tempo de cada palavra (Whisper) alinhado ao texto do roteiro ──────────────────────────

from faster_whisper import WhisperModel

asr = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^\wà-úç]", "", s.lower())


def palavras(n):
    import librosa
    y16 = librosa.resample(FALAS[n], orig_sr=SR, target_sr=16000)
    segs, _ = asr.transcribe(y16, language="pt", word_timestamps=True, beam_size=5,
                             initial_prompt=TEXTOS[n])
    hip = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    ref = TEXTOS[n].split()
    sm = difflib.SequenceMatcher(a=[norm(r) for r in ref], b=[norm(h[0]) for h in hip], autojunk=False)
    tempos = [None] * len(ref)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            tempos[a + k] = (hip[b + k][1], hip[b + k][2])
    # palavras sem par (ex.: "oitenta e seis" x "86"): interpola entre as vizinhas
    for i in range(len(ref)):
        if tempos[i] is None:
            j = i
            while j < len(ref) and tempos[j] is None:
                j += 1
            ini = tempos[i - 1][1] if i > 0 else 0.0
            fim = tempos[j][0] if j < len(ref) else len(FALAS[n]) / SR
            passo = (fim - ini) / (j - i)
            for k in range(i, j):
                tempos[k] = (ini + passo * (k - i), ini + passo * (k - i + 1))
    off = inicio[n]
    return [{"w": r, "s": round(off + a, 3), "e": round(off + b, 3), "seg": n} for r, (a, b) in zip(ref, tempos)]


PALAVRAS = [w for n in range(1, 7) for w in palavras(n)]


def achar(seg, palavra, campo="s", ordem=0):
    hits = [w for w in PALAVRAS if w["seg"] == seg and norm(w["w"]) == norm(palavra)]
    return hits[ordem][campo]


# ── 3. Cenas e eventos ───────────────────────────────────────────────────────────────────────

timer = inicio[3] + len(FALAS[3]) / SR + 0.15
reveal = timer + TIMER
CUES = {
    "nao": achar(1, "não"),
    "stamp": achar(1, "Nem"),
    "mark": achar(2, "Enquanto"),
    "markEnd": achar(2, "prisão.", "e"),
    "optA": achar(3, "Maioria"),
    "optB": achar(3, "Três"),
    "optC": achar(3, "dois"),
    "timer": timer,
    "reveal": reveal,
    "verdict": achar(4, "Uma"),
    "literalTap": inicio[5] + 0.9,
    "pick": achar(5, "troca") + 0.25,
    "ctaButton": achar(6, "Busca"),
    "comment": achar(6, "comenta"),
}
CENAS = {
    "gancho": {"start": 0.0, "end": inicio[2] - 0.12},
    "lei": {"start": inicio[2] - 0.12, "end": inicio[3] - 0.15},
    "quiz": {"start": inicio[3] - 0.15, "end": inicio[5] - 0.2},
    "app": {"start": inicio[5] - 0.2, "end": inicio[6] - 0.2},
    "cta": {"start": inicio[6] - 0.2, "end": DURACAO},
}

# Legendas: blocos de até 3 palavras, quebrando na pontuação e em pausas
QUENTES = {"preso", "flagrante", "prisão", "dois", "terços", "graça", "estuda", "leges", "acertou"}
chunks, atual = [], []
for i, w in enumerate(PALAVRAS):
    atual.append({"w": w["w"], "s": w["s"], "e": w["e"], **({"hot": True} if norm(w["w"]) in QUENTES else {})})
    prox = PALAVRAS[i + 1] if i + 1 < len(PALAVRAS) else None
    quebra = (len(atual) >= 3 or re.search(r"[.,?!:]$", w["w"]) or prox is None
              or prox["seg"] != w["seg"] or prox["s"] - w["e"] > 0.35)
    if quebra:
        chunks.append({"s": atual[0]["s"], "e": atual[-1]["e"], "words": atual})
        atual = []

# ── 4. Efeitos sonoros (sintetizados, sem direitos de terceiros) ─────────────────────────────

rng = np.random.default_rng(7)
tt = lambda d: np.arange(int(d * SR)) / SR


def env(d, a=0.005, r=0.2):
    x = tt(d)
    return np.minimum(1, x / a) * np.exp(-x / r)


def whoosh(d=0.38):
    n = rng.standard_normal(int(d * SR)).astype(np.float32)
    x = tt(d)
    # filtro passa-banda que sobe: média móvel com janela que diminui
    out = np.zeros_like(n)
    for k, w in enumerate(np.linspace(40, 4, 8)):
        a, b = int(k * len(n) / 8), int((k + 1) * len(n) / 8)
        out[a:b] = np.convolve(n, np.ones(int(w)) / w, mode="same")[a:b]
    return out * np.sin(np.pi * x / d) ** 2 * 0.35


def boom():
    x = tt(0.7)
    f = 95 * np.exp(-x * 6) + 40
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.7, 0.002, 0.18) * 0.9
            + rng.standard_normal(len(x)) * env(0.7, 0.001, 0.02) * 0.25)


def tick(freq=1500):
    x = tt(0.09)
    return np.sin(2 * np.pi * freq * x) * env(0.09, 0.001, 0.018) * 0.5


def chime(notas=(1046.5, 1318.5, 1568.0), d=1.1, vol=0.35, atraso=0.06):
    out = np.zeros(int((d + atraso * len(notas)) * SR), np.float32)
    for i, f in enumerate(notas):
        x = tt(d)
        tom = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * env(d, 0.004, 0.35)
        a = int(i * atraso * SR)
        out[a: a + len(tom)] += tom
    return out * vol


def click():
    x = tt(0.05)
    return (rng.standard_normal(len(x)) * env(0.05, 0.0005, 0.006) * 0.35
            + np.sin(2 * np.pi * 2200 * x) * env(0.05, 0.0005, 0.01) * 0.2)


def pluck(f=660):
    x = tt(0.25)
    return np.sin(2 * np.pi * f * x) * env(0.25, 0.002, 0.07) * 0.18


sfx = np.zeros_like(voz)


def put(som, quando, ganho=1.0):
    a = int(max(0, quando) * SR)
    b = min(len(sfx), a + len(som))
    sfx[a:b] += som[: b - a].astype(np.float32) * ganho


for cena in ("lei", "quiz", "app", "cta"):
    put(whoosh(), CENAS[cena]["start"] - 0.2, 0.9)
put(boom(), CUES["stamp"] - 0.01)
for i, k in enumerate(("optA", "optB", "optC")):
    put(pluck(587 * 2 ** (i * 4 / 12)), CUES[k])
for i in range(3):
    put(tick(1500 if i < 2 else 2000), timer + i * TIMER / 3)
put(chime((659.3, 987.8)), reveal, 0.9)
put(chime(), reveal + 0.12, 0.6)
put(click(), CUES["literalTap"])
put(click(), CUES["pick"])
put(chime((1318.5, 1760.0), d=0.8, vol=0.25), CUES["pick"] + 0.12)
put(pluck(880), CUES["ctaButton"], 1.4)
put(pluck(1174.7), CUES["comment"], 1.2)

# ── 5. Trilha discreta (pulso grave + acordes), mais tensa na contagem ───────────────────────

BPM = 100
batida = 60 / BPM
trilha = np.zeros_like(voz)
acordes = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7), (164.8, 207.7, 246.9)]
x_all = np.arange(len(trilha)) / SR
for c in range(int(DURACAO / (4 * batida)) + 1):
    notas = acordes[c % 4]
    a = int(c * 4 * batida * SR)
    d = 4 * batida
    x = tt(d)
    pad = sum(np.sin(2 * np.pi * f * x) + 0.2 * np.sin(2 * np.pi * 2 * f * x) for f in notas)
    pad *= np.minimum(1, x / 0.6) * np.minimum(1, (d - x) / 0.6) * 0.05
    trilha[a: a + len(pad)] += pad[: max(0, min(len(pad), len(trilha) - a))]
for b in range(int(DURACAO / batida) + 1):
    quando = b * batida
    if CENAS["cta"]["end"] - 0.5 < quando:
        break
    x = tt(0.25)
    kick = np.sin(2 * np.pi * (55 + 60 * np.exp(-x * 30)) * x) * env(0.25, 0.002, 0.08) * 0.22
    put_t = int(quando * SR)
    trilha[put_t: put_t + len(kick)] += kick[: max(0, min(len(kick), len(trilha) - put_t))]
# batimento acelerado durante a contagem
for i in range(6):
    q = timer + i * TIMER / 6
    x = tt(0.18)
    hb = np.sin(2 * np.pi * 48 * x) * env(0.18, 0.003, 0.05) * 0.35
    a = int(q * SR)
    trilha[a: a + len(hb)] += hb
trilha *= np.minimum(1, x_all / 0.4) * np.clip((DURACAO - x_all) / 1.0, 0, 1)

# ── 6. Pós-produção e mixagem ────────────────────────────────────────────────────────────────

SAIDA.mkdir(exist_ok=True)
sys.path.insert(0, str(VOZ_DIR))
import voz as voz_mod  # noqa: E402  (pós-produção da voz v2: EQ, de-esser, compressão)

with tempfile.TemporaryDirectory() as tmp:
    bruto, tratado = Path(tmp) / "voz.wav", Path(tmp) / "voz_pp.wav"
    sf.write(bruto, voz, SR)
    voz_mod.pos_producao(bruto, tratado)
    voz_pp, _ = sf.read(tratado, dtype="float32")
voz_pp = np.pad(voz_pp, (0, max(0, len(voz) - len(voz_pp))))[: len(voz)]
n = int(DURACAO * SR)


def exportar(nome, partes):
    mix = sum(partes)[:n]
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, mix / max(1.0, np.abs(mix).max()), SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), str(SAIDA / nome)], check=True)


exportar("mix.wav", [voz_pp, sfx * 0.55, trilha * 0.5])
exportar("mix_sem_trilha.wav", [voz_pp, sfx * 0.55])

(AQUI / "timing.json").write_text(json.dumps(
    {"duration": DURACAO, "scenes": CENAS, "cues": {k: round(v, 3) for k, v in CUES.items()},
     "chunks": chunks, "words": PALAVRAS}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"ok: {DURACAO:.1f} s, {len(PALAVRAS)} palavras, {len(chunks)} blocos de legenda")
for k, v in CUES.items():
    print(f"  {k:10} {v:6.2f}")
