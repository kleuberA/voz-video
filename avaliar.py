"""Avaliação objetiva das vozes: inteligibilidade (WER via Whisper), F0, variação de entonação e ritmo."""
import sys, re, glob, numpy as np, librosa, jiwer
from faster_whisper import WhisperModel
ref = open("texto_teste.txt", encoding="utf-8").read()
norm = lambda s: re.sub(r"[^\wà-ú ]", " ", s.lower()).split()
asr = WhisperModel("small", device="cpu", compute_type="int8")
print(f"{'arquivo':34} {'WER%':>5} {'F0 med':>7} {'F0 sd(st)':>9} {'pal/min':>8}")
for f in sorted(sys.argv[1:] or glob.glob("amostras/*.wav")):
    y, sr = librosa.load(f, sr=16000)
    segs, _ = asr.transcribe(y, language="pt", beam_size=5)
    hip = " ".join(s.text for s in segs)
    wer = jiwer.wer(" ".join(norm(ref)), " ".join(norm(hip))) * 100
    f0, vo, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr)
    f0 = f0[vo & ~np.isnan(f0)]
    st = 12 * np.log2(f0 / np.median(f0))          # variação em semitons
    dur = len(y) / sr
    print(f"{f:34} {wer:5.1f} {np.median(f0):6.0f}Hz {st.std():9.2f} {len(norm(ref))/dur*60:8.0f}")
