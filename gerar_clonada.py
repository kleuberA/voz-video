"""
Narração com voz clonada (Chatterbox Multilingual, licença MIT).

    python gerar_clonada.py roteiro.txt saida.wav referencias/cv_193.wav [--tentativas 3]

- Gera um PARÁGRAFO inteiro por vez -> entonação contínua, sem o "fala travada".
- Clona o timbre de uma gravação real de um brasileiro (6-10 s).
- Cada parágrafo é conferido pelo Whisper; se houver palavra errada/inventada,
  regera e fica com a melhor tentativa.
"""
import argparse, re, sys, numpy as np, torch, soundfile as sf
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from verificador import erro

ap = argparse.ArgumentParser()
ap.add_argument("texto"); ap.add_argument("saida"); ap.add_argument("referencia")
ap.add_argument("--tentativas", type=int, default=3)
ap.add_argument("--exagero", type=float, default=0.5)      # expressividade
ap.add_argument("--cfg", type=float, default=0.4)          # menor = mais solto/natural
ap.add_argument("--temperatura", type=float, default=0.75)
ap.add_argument("--pausa_ms", type=int, default=280)
ap.add_argument("--sem_pos", action="store_true")
a = ap.parse_args()

from chatterbox.mtl_tts import ChatterboxMultilingualTTS
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
sr = m.sr

texto = Path(a.texto).read_text(encoding="utf-8")
paragrafos = [" ".join(p.split()) for p in re.split(r"\n\s*\n", texto) if p.strip()]


def aparar(y, lim=0.003):
    # corte conservador: fricativas ("s", "f", "x") têm pouca energia e
    # sumiriam com um limiar alto; deixa 60 ms antes e 120 ms depois
    i = np.where(np.abs(y) > lim)[0]
    return y[max(i[0] - int(0.06 * sr), 0): i[-1] + int(0.12 * sr)] if len(i) else y


saida = [np.zeros(int(sr * 0.2), np.float32)]
for n, p in enumerate(paragrafos, 1):
    melhor = None
    for t in range(a.tentativas):
        torch.manual_seed(1000 * n + t)
        w = m.generate(p, language_id="pt", audio_prompt_path=a.referencia,
                       exaggeration=a.exagero, cfg_weight=a.cfg, temperature=a.temperatura)
        y = aparar(w.squeeze(0).numpy())
        e, hip = erro(p, y, sr)
        print(f"  §{n} tentativa {t+1}: erro {e*100:.0f}%", flush=True)
        if melhor is None or e < melhor[0]:
            melhor = (e, y, hip)
        if e <= 0.02:
            break
    if melhor[0] > 0.02:
        print(f"  ⚠ §{n} ficou com {melhor[0]*100:.0f}% -> ouviu: {melhor[2]}", flush=True)
    saida += [melhor[1], np.zeros(int(sr * a.pausa_ms / 1000), np.float32)]

bruto = np.concatenate(saida)
if a.sem_pos:
    sf.write(a.saida, bruto, sr)
else:
    import tempfile, voz
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, bruto, sr)
        voz.pos_producao(tmp.name, a.saida)
print("ok ->", a.saida)
