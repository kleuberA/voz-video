"""
Monta a trilha de um episódio e o arquivo de tempos (timing.json) que comanda a animação.

    python montar_audio.py videos/short-ep05-restaurante
    python montar_audio.py ep05                                   # procura videos/*ep05*
    python montar_audio.py ep06 --variante B                      # gancho B (p1b.wav no lugar de p1.wav)
    python montar_audio.py ep06 --destino ../juris-app/video/shorts/ep06   # copia a saída para a animação

Lê `<episodio>/config.json` (pausas, contagem do quiz, eventos, efeitos) e as falas brutas
`narracao/p1.wav … pN.wav`, geradas com `gerar_clonada.py` (o preset padrão `shorts` já sai sem
pós-produção, que é feita aqui na voz inteira).

Saídas, na pasta do episódio (variante B: `timing-B.json` e `audio-B/`):
  timing.json                cenas, eventos (cues) e legenda palavra por palavra
  audio/voz.wav              só a voz tratada (para conferir)
  audio/mix.wav              voz + efeitos + trilha discreta (-14 LUFS)
  audio/mix_sem_trilha.wav   voz + efeitos (para pôr uma música do YouTube por cima)
Com --destino, timing e áudio são copiados para lá com os nomes de sempre (timing.json e audio/).

Requer: numpy, soundfile, librosa, scipy, faster-whisper e ffmpeg (o ambiente .venv-cb tem tudo).

Formato dos eventos em config.json (todos em segundos):
  {"seg": 2, "word": "Enquanto"}            início da palavra (a 1ª ocorrência na fala 2)
  {"seg": 2, "word": "prisão.", "campo": "e"}  fim da palavra
  {"inicio": 5, "offset": 0.9}              início da fala 5 + 0,9 s
  "timer" e "reveal" vêm do bloco "timer" (contagem sem fala depois de uma fala)
Efeitos: [tipo, alvo, deslocamento, ganho], com alvo "cue:nome" ou "cena:id".
"""
import argparse, difflib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

BASE = Path(__file__).parent
ap = argparse.ArgumentParser(description="Monta o áudio e o timing.json de um episódio.")
ap.add_argument("episodio", help="pasta do episódio (videos/short-epNN-tema) ou só 'epNN'")
ap.add_argument("--variante", default="A", choices=["A", "B"], help="B usa narracao/p1b.wav e p1b.txt como gancho")
ap.add_argument("--destino", type=Path, help="pasta da animação para onde copiar timing.json e audio/")
ARGS = ap.parse_args()


def achar_episodio(nome):
    p = Path(nome)
    if p.is_dir():
        return p
    achados = sorted(d for d in (BASE / "videos").glob(f"*{nome}*") if d.is_dir())
    if len(achados) != 1:
        sys.exit(f"Episódio '{nome}': {'nenhuma pasta' if not achados else 'mais de uma pasta'} em videos/ "
                 f"({', '.join(d.name for d in achados)}). Passe o caminho da pasta.")
    return achados[0]


EP = achar_episodio(ARGS.episodio)
CFG = json.loads((EP / "config.json").read_text(encoding="utf-8"))
NARR = EP / "narracao"
SUFIXO = "" if ARGS.variante == "A" else f"-{ARGS.variante}"
SAIDA = EP / f"audio{SUFIXO}"
SR = 48000
N = CFG["falas"]


def arquivo_fala(n, ext):
    """Fala n; na variante B, a fala 1 (o gancho) vem de p1b."""
    if n == 1 and ARGS.variante == "B":
        return NARR / f"p1b.{ext}"
    return NARR / f"p{n}.{ext}"


faltando = [str(arquivo_fala(n, e)) for n in range(1, N + 1) for e in ("wav", "txt") if not arquivo_fala(n, e).exists()]
if faltando:
    sys.exit("Faltam falas (gere com gerar_clonada.py):\n  " + "\n  ".join(faltando))

# ── 1. Falas: carrega, acelera, apara e posiciona ────────────────────────────────────────────

# Velocidade da fala (atempo do ffmpeg, que preserva o tom). Padrão 1.0: no #4, acelerar 10% sobre
# uma fala que já saía a 170–200 palavras/min deixou a voz atropelada e artificial.
VELOCIDADE = float(os.environ.get("VELOCIDADE", CFG.get("velocidade", 1.0)))
# Silêncio interno máximo dentro de uma fala: a IA às vezes para 1 a 2 s no meio da frase; o que
# passar disto vira uma pausa natural de fim de frase.
PAUSA_MAX, PAUSA_NOVA = 0.40, 0.30


# Redutor de "s" sob medida (aplicado na voz já tratada, ver o fim do arquivo). A voz da IA prolonga o "s" do fim das palavras ("cobranças", "três",
# "opcionais") como um chiado agudo quase no volume da voz, que a compressão ainda realça; o
# deesser do ffmpeg reage devagar e não pega isso (medido no #5). Aqui, quadro a quadro: se a energia
# acima de 4,5 kHz passar de LIMITE_S dB abaixo do nível típico da voz, só os agudos daquele quadro
# são abaixados até o limite. Vogais e corpo da voz não mudam.
LIMITE_S = float(CFG.get("limite_s_db", -12))


def suavizar_s(y, sr=None):
    import librosa
    from scipy.ndimage import minimum_filter1d
    sr = sr or SR
    S = librosa.stft(y, n_fft=2048, hop_length=256)
    fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
    pot = np.abs(S) ** 2
    agudo = fr > 4500
    corpo = (fr > 150) & (fr <= 3500)
    e_agudo = pot[agudo].sum(0)
    e_corpo = pot[corpo].sum(0)
    falando = e_corpo > np.percentile(e_corpo, 50)
    ref = np.percentile(e_corpo[falando], 75) if falando.any() else e_corpo.max()
    permitido = ref * 10 ** (LIMITE_S / 10)
    ganho = np.minimum(1.0, np.sqrt(permitido / (e_agudo + 1e-12)))
    # espalha a redução para os quadros vizinhos (mínimo) e só então suaviza: uma média simples
    # diluía o corte de um "s" curto pela metade
    ganho = np.convolve(minimum_filter1d(ganho, size=7), np.ones(5) / 5, mode="same")
    ganho = np.clip(ganho, 0.08, 1.0)
    S[agudo] *= ganho
    return librosa.istft(S, hop_length=256, length=len(y)).astype(np.float32)


def encurtar_pausas(y):
    import librosa
    trechos = librosa.effects.split(y, top_db=35, frame_length=2048, hop_length=512)
    if len(trechos) < 2:
        return y
    partes = [y[: trechos[0][0]]]
    for i, (a, b) in enumerate(trechos):
        partes.append(y[a:b])
        if i + 1 < len(trechos):
            prox = trechos[i + 1][0]
            gap = y[b:prox]
            if len(gap) > PAUSA_MAX * SR:
                meio = int(PAUSA_NOVA * SR / 2)
                gap = np.concatenate([gap[:meio], gap[-meio:]])
            partes.append(gap)
    partes.append(y[trechos[-1][1]:])
    return np.concatenate(partes)


# Ajuste fino por fala (ex.: {"2": 0.88} desacelera só a fala 2, que saiu correndo).
VEL_FALA = {int(k): v for k, v in CFG.get("velocidade_fala", {}).items()}


def carregar(n):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(arquivo_fala(n, "wav")),
                        "-af", f"atempo={VEL_FALA.get(n, VELOCIDADE)}", tmp.name], check=True)
        y, sr = sf.read(tmp.name, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr != SR:
        import librosa
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    i = np.where(np.abs(y) > 0.004)[0]
    return encurtar_pausas(y[max(i[0] - int(0.04 * SR), 0): i[-1] + int(0.08 * SR)])


TEXTOS = {n: arquivo_fala(n, "txt").read_text(encoding="utf-8").strip() for n in range(1, N + 1)}
FALAS = {n: carregar(n) for n in range(1, N + 1)}
dur = lambda n: len(FALAS[n]) / SR

# Pausas entre as falas. A contagem do quiz é um silêncio depois da fala `timer.after`:
# é o "tempo de responder"; a fala `timer.after + 1` começa logo depois da revelação.
GAP = {int(k): v for k, v in CFG["gaps"].items()}
# Sem bloco "timer" (episódio sem quiz), nenhuma fala é seguida de contagem.
TM = CFG.get("timer") or {"after": -1, "dur": 0}
inicio = {1: CFG.get("lead", 0.10)}
timer = reveal = None
for n in range(2, N + 1):
    if n == TM["after"] + 1:
        timer = inicio[n - 1] + dur(n - 1) + TM["pre"]
        reveal = timer + TM["dur"]
        inicio[n] = reveal + TM["post"]
    else:
        inicio[n] = inicio[n - 1] + dur(n - 1) + GAP[n]
DURACAO = round(inicio[N] + dur(N) + CFG.get("cauda", 1.4), 2)

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
    segs, _ = asr.transcribe(y16, language="pt", word_timestamps=True, beam_size=5, initial_prompt=TEXTOS[n])
    hip = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    ref = TEXTOS[n].split()
    sm = difflib.SequenceMatcher(a=[norm(r) for r in ref], b=[norm(h[0]) for h in hip], autojunk=False)
    tempos = [None] * len(ref)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            tempos[a + k] = (hip[b + k][1], hip[b + k][2])
    # palavras sem par (ex.: "oitenta e seis" × "86"): interpola entre as vizinhas
    for i in range(len(ref)):
        if tempos[i] is None:
            j = i
            while j < len(ref) and tempos[j] is None:
                j += 1
            ini = tempos[i - 1][1] if i > 0 else 0.0
            fim = tempos[j][0] if j < len(ref) else dur(n)
            passo = (fim - ini) / (j - i)
            for k in range(i, j):
                tempos[k] = (ini + passo * (k - i), ini + passo * (k - i + 1))
    off = inicio[n]
    return [{"w": r, "s": round(off + a, 3), "e": round(off + b, 3), "seg": n} for r, (a, b) in zip(ref, tempos)]


PALAVRAS = [w for n in range(1, N + 1) for w in palavras(n)]


def resolver(spec):
    if "word" in spec:
        hits = [w for w in PALAVRAS if w["seg"] == spec["seg"] and norm(w["w"]) == norm(spec["word"])]
        if not hits:
            sys.exit(f"Evento sem palavra: {spec}")
        base = hits[spec.get("ordem", 0)][spec.get("campo", "s")]
    elif "inicio" in spec:
        base = inicio[spec["inicio"]]
    elif spec.get("ref") == "timer":
        base = timer
    elif spec.get("ref") == "reveal":
        base = reveal
    else:
        sys.exit(f"Evento inválido: {spec}")
    return base + spec.get("offset", 0)


# ── 3. Cenas e eventos ───────────────────────────────────────────────────────────────────────

CUES = {**({"timer": timer, "reveal": reveal} if timer is not None else {}), **{k: resolver(v) for k, v in CFG["cues"].items()}}
inicios = [(cid, 0.0 if i == 0 else resolver(spec)) for i, (cid, spec) in enumerate(CFG["cenas"])]
CENAS = {cid: {"start": round(s, 3), "end": round(inicios[i + 1][1] if i + 1 < len(inicios) else DURACAO, 3)} for i, (cid, s) in enumerate(inicios)}

# Exibição na legenda: troca expressões faladas por extenso pela forma curta ("seis por um" → "6x1",
# "quarenta e quatro" → "44"). Só muda o texto mostrado; o tempo é o da 1ª à última palavra trocada.
LEGENDA = []
trocas = sorted(CFG.get("legenda", {}).items(), key=lambda kv: -len(kv[0].split()))
i = 0
while i < len(PALAVRAS):
    for falado, mostrado in trocas:
        partes = falado.split()
        bloco = PALAVRAS[i: i + len(partes)]
        if len(bloco) == len(partes) and all(b["seg"] == bloco[0]["seg"] for b in bloco) and [norm(b["w"]) for b in bloco] == [norm(x) for x in partes]:
            pont = re.search(r"[.,?!:;]+$", bloco[-1]["w"])
            LEGENDA.append({**bloco[0], "w": mostrado + (pont.group(0) if pont else ""), "e": bloco[-1]["e"]})
            i += len(partes)
            break
    else:
        LEGENDA.append(PALAVRAS[i])
        i += 1

# Legendas: blocos de até 3 palavras, quebrando na pontuação e em pausas
QUENTES = {norm(w) for w in CFG.get("quentes", [])}
chunks, atual = [], []
for i, w in enumerate(LEGENDA):
    atual.append({"w": w["w"], "s": w["s"], "e": w["e"], **({"hot": True} if norm(w["w"]) in QUENTES else {})})
    prox = LEGENDA[i + 1] if i + 1 < len(LEGENDA) else None
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


SONS = {
    "whoosh": lambda: whoosh(),
    "boom": lambda: boom(),
    "acerto": lambda: chime((659.3, 987.8)),
    "brilho": lambda: chime(),
    "acerto_app": lambda: chime((1318.5, 1760.0), d=0.8, vol=0.25),
    "click": lambda: click(),
}


def som(tipo):
    if tipo.startswith("pluck:"):
        return pluck(float(tipo.split(":")[1]))
    if tipo.startswith("tick:"):
        return tick(float(tipo.split(":")[1]))
    return SONS[tipo]()


for tipo, alvo, desloc, ganho in CFG["sfx"]:
    tipo_alvo, nome = alvo.split(":")
    if tipo_alvo == "contagem":  # um tique por segundo da contagem; o último mais agudo
        passos = int(nome)
        for i in range(passos):
            put(tick(1500 if i < passos - 1 else 2000), timer + i * TM["dur"] / passos, ganho)
        continue
    quando = CUES[nome] if tipo_alvo == "cue" else CENAS[nome]["start"]
    put(som(tipo), quando + desloc, ganho)

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
ultima = list(CENAS.values())[-1]["end"]
for b in range(int(DURACAO / batida) + 1):
    quando = b * batida
    if ultima - 0.5 < quando:
        break
    x = tt(0.25)
    kick = np.sin(2 * np.pi * (55 + 60 * np.exp(-x * 30)) * x) * env(0.25, 0.002, 0.08) * 0.22
    p = int(quando * SR)
    trilha[p: p + len(kick)] += kick[: max(0, min(len(kick), len(trilha) - p))]
# batimento acelerado durante a contagem
for i in range(6 if timer is not None else 0):
    q = timer + i * TM["dur"] / 6
    x = tt(0.18)
    hb = np.sin(2 * np.pi * 48 * x) * env(0.18, 0.003, 0.05) * 0.35
    a = int(q * SR)
    trilha[a: a + len(hb)] += hb
trilha *= np.minimum(1, x_all / 0.4) * np.clip((DURACAO - x_all) / 1.0, 0, 1)

# ── 6. Pós-produção e mixagem ────────────────────────────────────────────────────────────────

SAIDA.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE))
import voz as voz_mod  # noqa: E402  (pós-produção da voz v2: EQ, de-esser, compressão)

with tempfile.TemporaryDirectory() as tmp:
    bruto, tratado = Path(tmp) / "voz.wav", Path(tmp) / "voz_pp.wav"
    sf.write(bruto, voz, SR)
    # Shorts: menos realce de agudos que o padrão da v2 (+2,5 dB em 3 kHz; aqui +1,8), para não acentuar o "s".
    voz_mod.pos_producao(bruto, tratado, pp={"ganho_presenca_db": 1.8, **CFG.get("pos_producao", {})})
    voz_pp, _ = sf.read(tratado, dtype="float32")
voz_pp = np.pad(voz_pp, (0, max(0, len(voz) - len(voz_pp))))[: len(voz)]
# Último passo da voz: o redutor de "s" depois da compressão (antes dela, a compressão fazia o "s"
# crescer de novo em relação ao corpo da voz).
voz_pp = suavizar_s(voz_pp)
total = int(DURACAO * SR)


def exportar(nome, partes):
    mix = sum(partes)[:total]
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, mix / max(1.0, np.abs(mix).max()), SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), str(SAIDA / nome)], check=True)


exportar("voz.wav", [voz_pp])  # só a voz tratada (para conferir a voz sem efeitos e trilha)
exportar("mix.wav", [voz_pp, sfx * 0.55, trilha * 0.5])
exportar("mix_sem_trilha.wav", [voz_pp, sfx * 0.55])

TIMING = EP / f"timing{SUFIXO}.json"
TIMING.write_text(json.dumps(
    {"duration": DURACAO, "scenes": CENAS, "cues": {k: round(v, 3) for k, v in CUES.items()},
     "chunks": chunks, "words": PALAVRAS}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"ok: {DURACAO:.1f} s, {len(PALAVRAS)} palavras, {len(chunks)} blocos de legenda")
for k, v in CUES.items():
    print(f"  {k:12} {v:6.2f}")

# ── 7. Avisos de ritmo (as regras do producao/DIAGNOSTICO.md; não bloqueiam) ─────────────────

avisos = []
if DURACAO > 35:
    avisos.append(f"{DURACAO:.1f} s: acima de 35 s.")
for n in range(2, N + 1):
    if n == TM["after"] + 1:
        continue  # a contagem do quiz é silêncio de propósito
    pausa = inicio[n] - (inicio[n - 1] + dur(n - 1))
    if pausa > 0.35 + 1e-3:
        avisos.append(f"pausa de {pausa:.2f} s antes da fala {n} (gaps['{n}'] no config.json; meta ≤ 0,35 s).")
if "cta" in CENAS:
    c = CENAS["cta"]["end"] - CENAS["cta"]["start"]
    if c / DURACAO > 0.15:
        avisos.append(f"chamada final com {c:.1f} s ({c / DURACAO:.0%} do vídeo; meta ≤ 15%).")
for a in avisos:
    print(f"  ⚠ {a}")

if ARGS.destino:
    ARGS.destino.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TIMING, ARGS.destino / "timing.json")
    shutil.copytree(SAIDA, ARGS.destino / "audio", dirs_exist_ok=True)
    print(f"copiado para {ARGS.destino}: timing.json e audio/")
