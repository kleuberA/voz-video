"""
Narração com voz clonada (Chatterbox Multilingual, licença MIT).

    python gerar_clonada.py roteiro.txt saida.wav                 # usa o preset padrão
    python gerar_clonada.py roteiro.txt saida.wav --preset v1     # regera a versão v1 aprovada
    python gerar_clonada.py --listar                              # mostra os presets

Os presets ficam em presets.json. Cada versão aprovada é congelada lá e nunca
é alterada; refinamentos viram presets novos (v2, v3...).

- Gera um PARÁGRAFO inteiro por vez -> entonação contínua, sem o "fala travada".
- Clona o timbre de uma gravação real de um brasileiro.
- Cada parágrafo é conferido pelo Whisper; se houver palavra errada/inventada,
  regera e fica com a melhor tentativa.
"""
import argparse, json, re, sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
PRESETS = json.loads((BASE / "presets.json").read_text(encoding="utf-8"))

ap = argparse.ArgumentParser()
ap.add_argument("texto", nargs="?"); ap.add_argument("saida", nargs="?")
ap.add_argument("--preset", default=PRESETS["padrao"])
ap.add_argument("--listar", action="store_true")
# qualquer campo do preset pode ser sobrescrito na linha de comando
ap.add_argument("--referencia"); ap.add_argument("--tentativas", type=int)
ap.add_argument("--exagero", type=float); ap.add_argument("--cfg", type=float)
ap.add_argument("--temperatura", type=float); ap.add_argument("--pausa_ms", type=int)
ap.add_argument("--corte", choices=["legado", "conservador"])
ap.add_argument("--sem_pos", action="store_true")
# --natural: além das palavras, exige pausas curtas, entonação humana e o mesmo tom entre as falas
# (verificador.naturalidade). Desligado por padrão para as versões antigas saírem iguais.
ap.add_argument("--natural", action="store_true")
ap.add_argument("--f0_alvo", type=float, default=108.0)
a = ap.parse_args()

if a.listar or not a.saida:
    for k, v in PRESETS["presets"].items():
        marca = " (padrão)" if k == PRESETS["padrao"] else ""
        print(f"{k}{marca}: {v['descricao']}")
    sys.exit(0)

cfg = dict(PRESETS["presets"][a.preset])
for k in ["referencia", "tentativas", "exagero", "cfg", "temperatura", "pausa_ms", "corte"]:
    if getattr(a, k) is not None:
        cfg[k] = getattr(a, k)
print(f"preset {a.preset}: {cfg['descricao']}")

import numpy as np, torch, soundfile as sf
from verificador import erro, naturalidade, penalidade
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
sr = m.sr

texto = Path(a.texto).read_text(encoding="utf-8")
paragrafos = [" ".join(p.split()) for p in re.split(r"\n\s*\n", texto) if p.strip()]


def aparar(y):
    if cfg["corte"] == "legado":
        # corte usado na v1 (limiar 0.008, margens de 10/20 ms)
        i = np.where(np.abs(y) > 0.008)[0]
        return y[max(i[0] - 240, 0): i[-1] + 480] if len(i) else y
    # corte conservador: fricativas ("s", "f", "x") têm pouca energia e
    # sumiriam com um limiar alto; deixa 60 ms antes e 120 ms depois
    i = np.where(np.abs(y) > 0.003)[0]
    return y[max(i[0] - int(0.06 * sr), 0): i[-1] + int(0.12 * sr)] if len(i) else y


ref = str(BASE / cfg["referencia"])
saida = [np.zeros(int(sr * 0.2), np.float32)]
relatorio = []
for n, p in enumerate(paragrafos, 1):
    melhor = None
    for t in range(cfg["tentativas"]):
        torch.manual_seed(1000 * n + t)
        w = m.generate(p, language_id="pt", audio_prompt_path=ref,
                       exaggeration=cfg["exagero"], cfg_weight=cfg["cfg"],
                       temperature=cfg["temperatura"])
        y = aparar(w.squeeze(0).numpy())
        e, hip = erro(p, y, sr)
        nota, extra = e, ""
        if a.natural:
            nat = naturalidade(y, sr, p)
            pen = penalidade(nat, a.f0_alvo)
            nota = e + pen
            extra = f" | pausa {nat['pausa_max']:.2f}s, entonação {nat['entonacao']:.1f}st, tom {nat['f0']:.0f}Hz, {nat['ritmo']:.0f} pal/min{' ✗' if pen > 0 else ''}"
        print(f"  §{n} tentativa {t+1}: erro {e*100:.0f}%{extra}", flush=True)
        if melhor is None or nota < melhor[0]:
            melhor = (nota, y, hip, e)
        if nota <= 0.02:
            break
    if melhor[0] > 0.02:
        print(f"  ⚠ §{n} ficou com nota {melhor[0]:.3f} (erro {melhor[3]*100:.0f}%) -> ouviu: {melhor[2]}", flush=True)
    relatorio.append({"paragrafo": n, "erro": round(melhor[3], 3), "nota": round(melhor[0], 3), "ouvido": melhor[2].strip()})
    saida += [melhor[1], np.zeros(int(sr * cfg["pausa_ms"] / 1000), np.float32)]

bruto = np.concatenate(saida)
if a.sem_pos:
    sf.write(a.saida, bruto, sr)
else:
    import tempfile, voz
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, bruto, sr)
        voz.pos_producao(tmp.name, a.saida, pp=cfg.get("pos_producao"))
# guarda junto do áudio exatamente o que foi usado (para refazer depois)
Path(a.saida).with_suffix(".json").write_text(json.dumps(
    {"preset": a.preset, "config": cfg, "verificacao": relatorio}, indent=2, ensure_ascii=False),
    encoding="utf-8")
print("ok ->", a.saida)
