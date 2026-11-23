"""
Sotaque de uma gravação: brasileiro × europeu, pela transcrição em fonemas (wav2vec2 XLSR-53 espeak).
Mesmo critério de ferramentas/sotaque.py, mas lendo .wav: marcas do português europeu (vogal átona
reduzida "ɨ", "ʃ" antes de consoante) por mil fonemas × africadas brasileiras ("tʃ", "dʒ" em ti/di).

    python pesquisa_voz/sotaque_wav.py dados/mls/spk2959.wav referencias/cv_131_longa.wav
"""
import re, sys
import json, librosa, torch
from huggingface_hub import hf_hub_download
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

mid = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
proc = Wav2Vec2FeatureExtractor.from_pretrained(mid)
m = Wav2Vec2ForCTC.from_pretrained(mid).eval()
# decodificação CTC direto pelo vocabulário (dispensa o phonemizer, que só converte texto em fonema)
vocab = {v: k for k, v in json.load(open(hf_hub_download(mid, "vocab.json"))).items()}


def decodificar(ids):
    out, ant = [], None
    for i in ids:
        if i != ant and vocab.get(i, "<pad>") not in ("<pad>", "<s>", "</s>", "<unk>"):
            out.append(vocab[i])
        ant = i
    return " ".join(out)
print(f"{'arquivo':38} {'fonemas':>7} {'europeu/mil':>11} {'africadas BR':>12}  veredito")
for f in sys.argv[1:]:
    y, _ = librosa.load(f, sr=16000)
    ph = ""
    for i in range(0, len(y), 16000 * 20):
        with torch.no_grad():
            ids = m(proc(y[i:i + 16000 * 20], sampling_rate=16000, return_tensors="pt").input_values).logits.argmax(-1)
        ph += " " + decodificar(ids[0].tolist())
    n = len(ph.split()) or 1
    eu = ph.count("ɨ") + len(re.findall(r"ʃ (?=[ptkbdgfvmnlr])", ph))
    af = len(re.findall(r"t\s?ʃ|d\s?ʒ", ph))
    por_mil = 1000 * eu / n
    veredito = "brasileiro" if af >= 3 and por_mil < 15 else "europeu?" if por_mil >= 15 else "incerto"
    print(f"{f:38} {n:7} {por_mil:11.1f} {af:12}  {veredito}", flush=True)
