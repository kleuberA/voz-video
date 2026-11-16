import pandas as pd, numpy as np, io, soundfile as sf, librosa, torch, re, sys
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
mid="facebook/wav2vec2-xlsr-53-espeak-cv-ft"
proc=Wav2Vec2Processor.from_pretrained(mid); m=Wav2Vec2ForCTC.from_pretrained(mid).eval()
d=pd.read_parquet('dados/mls/mls_pt_1h.parquet')
for spk in sys.argv[1:]:
    g=d[d.speaker_id==spk].head(6); ph=""; txt=""
    for _,r in g.iterrows():
        y,sr=sf.read(io.BytesIO(r['audio']['bytes'])); y=librosa.resample(y.astype(np.float32),orig_sr=sr,target_sr=16000)
        with torch.no_grad(): ids=m(proc(y,sampling_rate=16000,return_tensors="pt").input_values).logits.argmax(-1)
        ph+=" "+proc.batch_decode(ids)[0]; txt+=" "+r.transcript
    alvo=len(re.findall(r"(?:t|d)(?:i|e)\b|\bt?i", txt.replace(" ","  ")))
    alvo=len(re.findall(r"(?:t|d)(?:e\b|i)", txt))
    afric=len(re.findall(r"t\s?ʃ|d\s?ʒ", ph))
    n=len(ph.split()); eu=ph.count("ɨ")+len(re.findall(r"ʃ (?=[ptkbdgfvmnlr])",ph)); print(f"{spk:6} fonemas={n:4} marcadores_PT_europeu={eu:3} ({1000*eu/n:.1f} por mil) afric_BR={afric}", flush=True)
