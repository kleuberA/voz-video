"""
Mede o quanto cada áudio soa como fala humana. Roda no ambiente .venv-cb.

    python pesquisa_voz/avaliar.py pesquisa_voz/amostras/*.wav
    python pesquisa_voz/avaliar.py pesquisa_voz/amostras/*.wav --md pesquisa_voz/RESULTADOS.md

Métricas (e o que a literatura considera fala humana natural):
  mos        DNSMOS P.808 (Microsoft, ONNX): nota 1–5 prevista a partir de avaliações humanas de
             qualidade de fala. O UTMOS22 foi descartado: o checkpoint só carrega em modo inseguro
             do PyTorch (permite executar código). Preditores de MOS acompanham bem a qualidade do
             som, mas são pouco sensíveis a erros de prosódia (Takagi et al., 2026); por isso os
             alertas de prosódia pesam tanto quanto a nota.
  erro       palavras erradas ou inventadas (Whisper).
  tom_st     desvio do tom em semitons. Fala monótona < 2; narração expressiva 3–5; > 6 soa "quebrado".
  faixa_st   faixa de tom (percentis 5–95) em semitons. Leitura plana < 6; fala viva 8–12.
  ppm        palavras por minuto falando. Conversa 150–180.
  pausas     pausas internas > 150 ms por frase e a maior delas. Humano: pausa em vírgula e ponto
             (0,2–0,6 s); TTS "robótico" emenda tudo ou para no meio da frase.
  jitter/shimmer/hnr  microvariação de período e amplitude e relação harmônico-ruído (Praat). Os
             valores de literatura (jitter < 1 %, HNR > 15 dB) são de vogal sustentada; em fala corrida
             os números sobem. Compare com as referências humanas medidas do mesmo jeito.
  alertas    monótona (tom < 2,5 st ou faixa < 8), quebrada (tom > 6 ou faixa > 22), ritmo fora
             de 145–195, emendada (< 0,5 pausa por frase), travada (pausa > 0,8 s). 0 = melhor.
"""
import argparse, re, sys
from pathlib import Path

import librosa, numpy as np, parselmouth
from parselmouth.praat import call

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from verificador import erro  # noqa: E402

TEXTO = " ".join((BASE / "pesquisa_voz" / "texto_teste.txt").read_text(encoding="utf-8").split())
def mos(arquivos):
    from speechmos import dnsmos
    notas = {}
    for f in arquivos:
        y, _ = librosa.load(f, sr=16000)
        r = dnsmos.run(np.clip(y, -1, 1), sr=16000, return_df=False)
        notas[f] = float(r["p808_mos"])
    return notas


def prosodia(arq, texto):
    y, sr = librosa.load(arq, sr=16000)
    iv = librosa.effects.split(y, top_db=35, frame_length=1024, hop_length=256)
    gaps = [(b[0] - a[1]) / sr for a, b in zip(iv[:-1], iv[1:])]
    pausas = [g for g in gaps if g > 0.15]
    falando = sum(b - a for a, b in iv) / sr or 1e-6
    f0, v, _ = librosa.pyin(y, fmin=60, fmax=350, sr=sr)
    f0 = f0[v & ~np.isnan(f0)]
    st = 12 * np.log2(f0 / np.median(f0)) if len(f0) else np.array([0.0])
    snd = parselmouth.Sound(str(arq))
    pp = call(snd, "To PointProcess (periodic, cc)", 60, 350)
    jitter = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100
    shimmer = call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
    hnr = call(call(snd, "To Harmonicity (cc)", 0.01, 60, 0.1, 1.0), "Get mean", 0, 0)
    frases = max(1, len(re.findall(r"[.!?]", texto)))
    return {
        "dur": len(y) / sr, "tom_hz": float(np.median(f0)) if len(f0) else 0.0, "tom_st": float(st.std()),
        "faixa_st": float(np.percentile(st, 95) - np.percentile(st, 5)),
        "ppm": len(texto.split()) / falando * 60, "pausas_frase": len(pausas) / frases,
        "pausa_max": max(gaps) if gaps else 0.0, "jitter": jitter, "shimmer": shimmer, "hnr": hnr,
    }


def alertas(m):
    a = []
    if m["tom_st"] < 2.5 or m["faixa_st"] < 8:
        a.append("monótona")
    if m["tom_st"] > 6 or m["faixa_st"] > 22:
        a.append("quebrada")
    if not 145 <= m["ppm"] <= 195:
        a.append("lenta" if m["ppm"] < 145 else "corrida")
    if m["pausas_frase"] < 0.5:
        a.append("emendada")
    if m["pausa_max"] > 0.8:
        a.append("travada")
    return a


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--md", type=Path)
    ap.add_argument("--texto", help="texto falado, se não for o texto_teste (ex.: referências humanas)")
    a = ap.parse_args()
    notas = mos(a.arquivos)
    linhas = []
    for f in a.arquivos:
        y, sr = librosa.load(f, sr=24000)
        texto = a.texto or TEXTO
        e, _ = erro(texto, y, sr)
        m = prosodia(f, texto)
        m.update({"arquivo": Path(f).stem, "erro": e, "mos": notas.get(f), "alertas": alertas(m)})
        linhas.append(m)
    cab = "| amostra | MOS (DNSMOS) | erro | tom (st) | faixa (st) | pal/min | pausas/frase | maior pausa | jitter % | shimmer % | HNR dB | alertas |"
    print(cab)
    print("|" + "---|" * 12)
    tabela = []
    for m in sorted(linhas, key=lambda x: (len(x["alertas"]) + 2 * (x["erro"] > 0.1), -(x["mos"] or 0))):
        u = f"{m['mos']:.2f}" if m["mos"] is not None else "—"
        l = (f"| {m['arquivo']} | {u} | {m['erro'] * 100:.0f}% | {m['tom_st']:.1f} | {m['faixa_st']:.1f} | {m['ppm']:.0f} | "
             f"{m['pausas_frase']:.1f} | {m['pausa_max']:.2f} s | {m['jitter']:.2f} | {m['shimmer']:.1f} | {m['hnr']:.1f} | {', '.join(m['alertas']) or '✅ nenhum'} |")
        print(l)
        tabela.append(l)
    if a.md:
        a.md.write_text("\n".join([cab, "|" + "---|" * 12] + tabela) + "\n", encoding="utf-8")
