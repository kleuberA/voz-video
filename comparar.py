import sys, soundfile as sf, librosa
from pathlib import Path
from verificador import erro, fluidez
ref = Path("texto_teste.txt").read_text(encoding="utf-8")
print(f"{'arquivo':42} {'erro%':>6} {'pausas/min':>10} {'entonação':>9} {'pal/min':>8}")
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=24000)
    e, _ = erro(ref, y, sr); fl = fluidez(y, sr)
    print(f"{f:42} {e*100:6.1f} {fl['pausas_longas_min']:10.1f} {fl['entonacao_st']:9.2f} {len(ref.split())/(len(y)/sr)*60:8.0f}", flush=True)
