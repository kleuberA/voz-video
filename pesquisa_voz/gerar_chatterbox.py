"""
Gera o texto de teste com o Chatterbox, para comparar modelos e configurações de voz.

    python pesquisa_voz/gerar_chatterbox.py --modelo ptbr --modo continuo --saida pesquisa_voz/amostras/ptbr.wav
    python pesquisa_voz/gerar_chatterbox.py --modelo mtl --modo frases --saida pesquisa_voz/amostras/atual.wav

--modelo mtl   Chatterbox Multilingual (23 idiomas), o usado nos episódios #1–#7.
--modelo ptbr  Chatterbox Multilingual V3 pt-BR, ajuste dedicado ao português do Brasil (MIT).
               Usa só os PESOS (modelos/chatterbox-ptbr/, montada por preparar_ptbr.py) com o pacote
               chatterbox já instalado: nenhum código baixado é executado.
--modo frases    uma geração por frase, coladas com 0,3 s (como a produção fazia por fala).
--modo continuo  o texto inteiro de uma vez: a entonação de uma frase prepara a seguinte.
"""
import argparse, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--modelo", choices=["mtl", "ptbr"], default="ptbr")
ap.add_argument("--modo", choices=["frases", "continuo"], default="continuo")
ap.add_argument("--texto", default=str(BASE / "pesquisa_voz" / "texto_teste.txt"))
ap.add_argument("--ref", default=str(BASE / "referencias" / "cv_131_longa.wav"))
ap.add_argument("--exagero", type=float, default=0.5)
ap.add_argument("--cfg", type=float, default=0.5)
ap.add_argument("--temperatura", type=float, default=0.8)
ap.add_argument("--semente", type=int, default=7)
ap.add_argument("--saida", required=True)
a = ap.parse_args()

import numpy as np, soundfile as sf, torch  # noqa: E402
from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: E402

if a.modelo == "ptbr":
    m = ChatterboxMultilingualTTS.from_local(BASE / "modelos" / "chatterbox-ptbr", "cpu")
else:
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")

texto = " ".join(Path(a.texto).read_text(encoding="utf-8").split())
partes = [texto] if a.modo == "continuo" else re.split(r"(?<=[.!?])\s+", texto)
sr = m.sr
saida = []
for i, p in enumerate(partes):
    torch.manual_seed(a.semente + i)
    w = m.generate(p, language_id="pt", audio_prompt_path=a.ref, exaggeration=a.exagero,
                   cfg_weight=a.cfg, temperature=a.temperatura)
    y = w.squeeze(0).numpy()
    idx = np.where(np.abs(y) > 0.003)[0]
    y = y[max(idx[0] - int(0.05 * sr), 0): idx[-1] + int(0.12 * sr)] if len(idx) else y
    saida += [y, np.zeros(int(0.3 * sr), np.float32)]
Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
sf.write(a.saida, np.concatenate(saida[:-1]), sr)
print("ok ->", a.saida)
