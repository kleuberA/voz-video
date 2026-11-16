"""Confere se o áudio gerado diz exatamente o texto pedido (Whisper) e mede fluidez."""
import re, numpy as np, jiwer, librosa

_asr = None
# equivalências que o Whisper escreve diferente mas que NÃO são erro de fala
NUM = {"quarenta e nove": "49", "sete": "7", "vinte": "20", "cível": "civil", "sível": "civil"}


def _norm(s):
    s = s.lower()
    s = re.sub(r"[^\wà-úç ]", " ", s)
    return " ".join(s.split())


def _num(s):
    for k, v in NUM.items():
        s = s.replace(k, v)
    return s


def transcrever(audio, sr):
    global _asr
    if _asr is None:
        from faster_whisper import WhisperModel
        _asr = WhisperModel("small", device="cpu", compute_type="int8")
    y = librosa.resample(np.asarray(audio, dtype=np.float32), orig_sr=sr, target_sr=16000)
    return " ".join(s.text for s in _asr.transcribe(y, language="pt", beam_size=5)[0])


def erro(texto, audio, sr):
    """Taxa de erro de palavras (0 = perfeito). Ignora número escrito vs. por extenso."""
    hip = transcrever(audio, sr)
    return jiwer.wer(_num(_norm(texto)), _num(_norm(hip))), hip


def fluidez(audio, sr):
    """Pausas internas longas (> 250 ms) por minuto e variação de entonação (semitons)."""
    y = np.asarray(audio, dtype=np.float32)
    iv = librosa.effects.split(y, top_db=35, frame_length=1024, hop_length=256)
    gaps = [(b[0] - a[1]) / sr for a, b in zip(iv[:-1], iv[1:])]
    dur = len(y) / sr
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    f0, v, _ = librosa.pyin(y16, fmin=60, fmax=350, sr=16000)
    f0 = f0[v & ~np.isnan(f0)]
    st = float((12 * np.log2(f0 / np.median(f0))).std()) if len(f0) else 0.0
    return {"pausas_longas_min": sum(g > 0.25 for g in gaps) / dur * 60, "entonacao_st": st}
