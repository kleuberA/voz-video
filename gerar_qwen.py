"""
Narração de produção com Qwen3-TTS (Apache-2.0), aprovada em 23/11/2026 (pesquisa_voz/RESULTADOS.md).

    python gerar_qwen.py videos/short-ep08-desafio/narracao
    python gerar_qwen.py videos/short-ep08-desafio/narracao --variante B

Diferença para o gerar_clonada.py: o roteiro inteiro é gerado DE UMA VEZ (a entonação de uma frase
prepara a seguinte, sem as "travadas" de gerar fala por fala) e depois cortado nas falas pelo
alinhamento das palavras (Whisper). Saída igual à de antes, então o montar_audio.py não muda:
narracao/p1.wav … pN.wav (variante B: só p1b.wav) e pN.json com a verificação.

Cada tentativa é conferida: palavras (Whisper), maior pausa interna, variação de tom e ritmo. Fica a
melhor; se nenhuma passar, a melhor sai com aviso ⚠. Ambiente: .venv-qwen (Python 3.12).
"""
import argparse, difflib, json, re, sys, time
from pathlib import Path

BASE = Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("narracao", type=Path, help="pasta com p1.txt … pN.txt (e p1b.txt)")
ap.add_argument("--variante", choices=["A", "B"], default="A")
ap.add_argument("--ref", default=str(BASE / "referencias" / "mls_12428.wav"))
ap.add_argument("--modelo", default="Qwen/Qwen3-TTS-12Hz-1.7B-Base")
ap.add_argument("--tentativas", type=int, default=3)
ap.add_argument("--temperatura", type=float, default=0.9)
ap.add_argument("--semente", type=int, default=7)
a = ap.parse_args()

import jiwer, librosa, numpy as np, soundfile as sf, torch  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402
from qwen_tts import Qwen3TTSModel  # noqa: E402

sys.path.insert(0, str(BASE))
from verificador import IGUAIS, NUM  # noqa: E402

pasta = a.narracao
arquivos = sorted((p for p in pasta.glob("p*.txt") if re.fullmatch(r"p\d+", p.stem)), key=lambda p: int(p.stem[1:]))
falas = [p.read_text(encoding="utf-8").strip() for p in arquivos]
if a.variante == "B":
    falas[0] = (pasta / "p1b.txt").read_text(encoding="utf-8").strip()
texto = " ".join(falas)
contagem = [len(f.split()) for f in falas]


def norm(s):
    s = re.sub(r"[^\wà-úç ]", " ", s.lower())
    s = " ".join(IGUAIS.get(w, w) for w in s.split())
    for k, v in NUM.items():
        s = s.replace(k, v)
    return s


torch.set_num_threads(4)
ini = time.time()
tts = Qwen3TTSModel.from_pretrained(a.modelo, dtype=torch.float32, device_map="cpu")
asr = WhisperModel("small", device="cpu", compute_type="int8")
ref_texto = Path(a.ref).with_suffix(".txt").read_text(encoding="utf-8").strip()


def palavras_ouvidas(y, sr):
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    segs, _ = asr.transcribe(y16, language="pt", word_timestamps=True, beam_size=5)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def avaliar(y, sr):
    ouvidas = palavras_ouvidas(y, sr)
    hip = " ".join(w for w, _, _ in ouvidas)
    erro = jiwer.wer(norm(texto), norm(hip))
    iv = librosa.effects.split(y, top_db=35, frame_length=1024, hop_length=256)
    gaps = [(b[0] - c[1]) / sr for c, b in zip(iv[:-1], iv[1:])]
    falando = sum(b - c for c, b in iv) / sr or 1e-6
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    f0, v, _ = librosa.pyin(y16, fmin=60, fmax=350, sr=16000)
    f0 = f0[v & ~np.isnan(f0)]
    tom = float((12 * np.log2(f0 / np.median(f0))).std()) if len(f0) else 0.0
    nat = {"pausa_max": max(gaps) if gaps else 0.0, "tom_st": tom, "ppm": len(texto.split()) / falando * 60}
    pen = max(0.0, nat["pausa_max"] - 0.8) * 0.5 + max(0.0, 2.5 - tom) * 0.05 + max(0.0, tom - 6.5) * 0.05
    pen += max(0.0, 145 - nat["ppm"], nat["ppm"] - 200) * 0.002
    return erro + pen, erro, nat, ouvidas, hip


melhor = None
for t in range(a.tentativas):
    torch.manual_seed(a.semente + t)
    wavs, sr = tts.generate_voice_clone(text=texto, language="Portuguese", ref_audio=a.ref, ref_text=ref_texto,
                                        temperature=a.temperatura)
    y = np.asarray(wavs[0], dtype=np.float32)
    nota, erro, nat, ouvidas, hip = avaliar(y, sr)
    print(f"  tentativa {t + 1}: erro {erro * 100:.0f}% | maior pausa {nat['pausa_max']:.2f}s, tom {nat['tom_st']:.1f}st, "
          f"{nat['ppm']:.0f} pal/min | nota {nota:.3f}", flush=True)
    if melhor is None or nota < melhor[0]:
        melhor = (nota, y, sr, erro, nat, ouvidas, hip)
    if nota <= 0.02:
        break
nota, y, sr, erro, nat, ouvidas, hip = melhor
if nota > 0.02:
    print(f"  ⚠ melhor tentativa com nota {nota:.3f} (erro {erro * 100:.0f}%) -> ouviu: {hip}")

# ── corte nas falas: alinha as palavras do roteiro às ouvidas e corta no ponto mais silencioso entre elas
ref = texto.split()
sm = difflib.SequenceMatcher(a=[norm(w) for w in ref], b=[norm(w) for w, _, _ in ouvidas], autojunk=False)
tempos = [None] * len(ref)
for i, j, n in sm.get_matching_blocks():
    for k in range(n):
        tempos[i + k] = (ouvidas[j + k][1], ouvidas[j + k][2])


def tempo(i, campo):
    """Início (0) ou fim (1) da palavra i; sem par, usa a vizinha mais próxima que tem."""
    for d in range(len(ref)):
        for k in (i - d, i + d):
            if 0 <= k < len(ref) and tempos[k] is not None:
                return tempos[k][campo]
    return 0.0


energia = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
cortes, acum = [0], 0
for c in contagem[:-1]:
    acum += c
    fim_ant, ini_prox = tempo(acum - 1, 1), tempo(acum, 0)
    a0, a1 = int(fim_ant * sr / 256), max(int(fim_ant * sr / 256) + 1, int(ini_prox * sr / 256))
    quadro = a0 + int(np.argmin(energia[a0:a1 + 1])) if a1 > a0 else a0
    cortes.append(quadro * 256)
cortes.append(len(y))

saidas = range(len(falas)) if a.variante == "A" else [0]
for n in saidas:
    trecho = y[cortes[n]:cortes[n + 1]]
    nome = f"p{n + 1}" if not (a.variante == "B" and n == 0) else "p1b"
    sf.write(pasta / f"{nome}.wav", trecho, sr)
    ouvido = " ".join(w for w, s0, _ in ouvidas if cortes[n] / sr - 0.05 <= s0 < cortes[n + 1] / sr)
    e_fala = jiwer.wer(norm(falas[n]), norm(ouvido)) if ouvido else 1.0
    (pasta / f"{nome}.json").write_text(json.dumps({
        "motor": a.modelo, "referencia": str(Path(a.ref).relative_to(BASE)), "variante": a.variante,
        "geracao": "roteiro inteiro de uma vez, cortado nas falas pelo alinhamento",
        "verificacao": {"erro_fala": round(e_fala, 3), "erro_roteiro": round(erro, 3), "ouvido": ouvido,
                        "maior_pausa_s": round(nat["pausa_max"], 2), "tom_st": round(nat["tom_st"], 2), "ppm": round(nat["ppm"])},
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    marca = " ⚠" if e_fala > 0.1 else ""
    print(f"  {nome}: {len(trecho) / sr:.2f} s, erro {e_fala * 100:.0f}%{marca} | {ouvido}")
print(f"ok ({time.time() - ini:.0f} s)")
