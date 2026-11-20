"""Confere se o áudio gerado diz exatamente o texto pedido (Whisper) e mede fluidez."""
import re, numpy as np, jiwer, librosa

_asr = None
# equivalências que o Whisper escreve diferente mas que NÃO são erro de fala
NUM = {"quarenta e nove": "49", "sete": "7", "vinte": "20", "cível": "civil", "sível": "civil", "oitenta e seis": "86", "três quintos": "3/5", "dois terços": "2/3", "cinquenta e três": "53", "cento e quarenta e um": "141", "quarenta e quatro": "44", "quarenta e duas": "42", "quarenta": "40", "seis por um": "6x1", "6 por 1": "6x1", "vinte": "20", "quinze": "15", "sete": "7", "seis": "6", "dez por cento": "10%", "trinta e nove": "39", "três": "3", "um": "1", "dois": "2"}


# Palavras que o Whisper escreve de outro jeito sem que a fala esteja errada (troca palavra a
# palavra, para não mexer em "prazo" ao trocar "pra"). "Legis" é como se pronuncia "Leges".
IGUAIS = {"pra": "para", "pro": "para o", "tá": "está", "legis": "leges", "légis": "leges"}


def _norm(s):
    s = s.lower()
    s = re.sub(r"[^\wà-úç ]", " ", s)
    return " ".join(IGUAIS.get(w, w) for w in s.split())


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


def naturalidade(audio, sr, texto):
    """
    Sinais de voz "quebrada" que a contagem de palavras não pega (medidos no episódio #4):
    - pausa_max: maior silêncio dentro da fala (a IA às vezes para 1 a 2 s no meio da frase);
    - entonacao: desvio do tom em semitons (fala humana: ~2 a 5; acima de 6 o tom "quebra");
    - f0: tom mediano em Hz (para manter a mesma voz entre as falas de um vídeo);
    - ritmo: palavras por minuto falando (a v2 aprovada fala ~165).
    """
    y = np.asarray(audio, dtype=np.float32)
    iv = librosa.effects.split(y, top_db=35, frame_length=1024, hop_length=256)
    gaps = [(b[0] - a[1]) / sr for a, b in zip(iv[:-1], iv[1:])]
    falando = sum(b - a for a, b in iv) / sr or 1e-6
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    f0, v, _ = librosa.pyin(y16, fmin=60, fmax=350, sr=16000)
    f0 = f0[v & ~np.isnan(f0)]
    med = float(np.median(f0)) if len(f0) else 0.0
    st = float((12 * np.log2(f0 / med)).std()) if len(f0) else 0.0
    return {"pausa_max": max(gaps) if gaps else 0.0, "entonacao": st, "f0": med, "ritmo": len(texto.split()) / falando * 60}


def penalidade(nat, f0_alvo):
    """Quanto a tentativa foge de uma fala natural (0 = dentro de todos os limites)."""
    p = max(0.0, nat["pausa_max"] - 0.45) * 0.5
    p += max(0.0, nat["entonacao"] - 5.0) * 0.05 + max(0.0, 1.8 - nat["entonacao"]) * 0.08
    p += max(0.0, abs(nat["f0"] / f0_alvo - 1) - 0.06) * 1.0
    p += max(0.0, 150 - nat["ritmo"], nat["ritmo"] - 195) * 0.002
    return p
