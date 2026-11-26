"""
Gera o texto de teste com o Qwen3-TTS (Apache-2.0), clonando a voz de uma referência.

    python pesquisa_voz/gerar_qwen.py --modelo 1.7B --saida pesquisa_voz/amostras/q-qwen17.wav

Usa o modelo Base (clonagem por referência: áudio + transcrição do áudio). Ambiente: .venv-qwen
(Python 3.12, pacote qwen-tts). Roda em CPU, devagar: é para comparar, não para produção em massa.
"""
import argparse, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--modelo", choices=["0.6B", "1.7B"], default="1.7B")
ap.add_argument("--texto", default=str(BASE / "pesquisa_voz" / "texto_teste.txt"))
ap.add_argument("--ref", default=str(BASE / "referencias" / "cv_131_longa.wav"))
ap.add_argument("--ref_texto", help="transcrição da referência (padrão: o .txt ao lado do .wav)")
ap.add_argument("--temperatura", type=float, default=0.9)
ap.add_argument("--semente", type=int, default=7)
ap.add_argument("--saida", required=True)
a = ap.parse_args()

import soundfile as sf, torch  # noqa: E402
from qwen_tts import Qwen3TTSModel  # noqa: E402

torch.manual_seed(a.semente)
torch.set_num_threads(4)
ini = time.time()
m = Qwen3TTSModel.from_pretrained(f"Qwen/Qwen3-TTS-12Hz-{a.modelo}-Base", dtype=torch.float32, device_map="cpu")
ref_texto = a.ref_texto or Path(a.ref).with_suffix(".txt").read_text(encoding="utf-8").strip()
texto = " ".join(Path(a.texto).read_text(encoding="utf-8").split())
wavs, sr = m.generate_voice_clone(text=texto, language="Portuguese", ref_audio=a.ref, ref_text=ref_texto,
                                  temperature=a.temperatura)
Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
sf.write(a.saida, wavs[0], sr)
print(f"ok -> {a.saida} ({time.time() - ini:.0f} s)")
