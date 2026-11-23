"""
Mede o quanto cada áudio soa como fala humana. Roda no ambiente .venv-cb.

    python pesquisa_voz/avaliar.py pesquisa_voz/amostras/*.wav
    python pesquisa_voz/avaliar.py pesquisa_voz/amostras/*.wav --md pesquisa_voz/RESULTADOS.md

Métricas (e o que a literatura considera fala humana natural):
  utmos      nota de naturalidade prevista pelo UTMOS22 (1–5; gravação humana limpa ≈ 4+). Roda no
             ambiente .venv-mos (fairseq exige Python 3.10). Os preditores de MOS acompanham bem a
             qualidade do som, mas são pouco sensíveis a erros de prosódia (Takagi et al., 2026);
             por isso as medidas de prosódia abaixo pesam tanto quanto a nota.
  erro       palavras erradas ou inventadas (Whisper).
  tom_st     desvio do tom em semitons. Fala monótona < 2; narração expressiva 3–5; > 6 soa "quebrado".
  faixa_st   faixa de tom (percentis 5–95) em semitons. Leitura plana < 6; fala viva 8–12.
  ppm        palavras por minuto falando. Conversa 150–180.
  pausas     pausas internas > 150 ms por frase e a maior delas. Humano: pausa em vírgula e ponto
             (0,2–0,6 s); TTS "robótico" emenda tudo ou para no meio da frase.
  jitter/shimmer  microvariação de período e amplitude (Praat). Voz humana: jitter 0,5–1,5 %,
             shimmer 3–7 %. Lisa demais (abaixo) soa sintética; muito acima, rouca ou com artefato.
  hnr        relação harmônico-ruído em dB. Voz limpa 15–25.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

import librosa, numpy as np, parselmouth
from parselmouth.praat import call

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from verificador import erro  # noqa: E402

TEXTO = " ".join((BASE / "pesquisa_voz" / "texto_teste.txt").read_text(encoding="utf-8").split())
MOS_PY = BASE / ".venv-mos" / "bin" / "python"


def utmos(arquivos):
    if not MOS_PY.exists():
        return {}
    codigo = ("import json,sys,utmos,warnings;warnings.filterwarnings('ignore');m=utmos.Score();"
              "print(json.dumps({f: float(m.calculate_wav_file(f)) for f in sys.argv[1:]}))")
    r = subprocess.run([str(MOS_PY), "-c", codigo, *map(str, arquivos)], capture_output=True, text=True)
    linha = [l for l in r.stdout.splitlines() if l.startswith("{")]
    return json.loads(linha[-1]) if linha else {}


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


def nota_humana(m):
    """Quantas medidas de prosódia caem na faixa humana (de 6)."""
    return sum([2.5 <= m["tom_st"] <= 5.5, 7 <= m["faixa_st"] <= 13, 145 <= m["ppm"] <= 190,
                0.3 <= m["pausas_frase"] <= 1.6 and m["pausa_max"] <= 0.7,
                0.5 <= m["jitter"] <= 1.8 and 3 <= m["shimmer"] <= 8, 13 <= m["hnr"] <= 26])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--md", type=Path)
    ap.add_argument("--texto", help="texto falado, se não for o texto_teste (ex.: referências humanas)")
    a = ap.parse_args()
    mos = utmos(a.arquivos)
    linhas = []
    for f in a.arquivos:
        y, sr = librosa.load(f, sr=24000)
        texto = a.texto or TEXTO
        e, _ = erro(texto, y, sr)
        m = prosodia(f, texto)
        m.update({"arquivo": Path(f).stem, "erro": e, "utmos": mos.get(f), "humano": nota_humana(m)})
        linhas.append(m)
    cab = "| amostra | UTMOS | erro | tom (st) | faixa (st) | pal/min | pausas/frase | maior pausa | jitter % | shimmer % | HNR dB | prosódia humana |"
    print(cab)
    print("|" + "---|" * 12)
    tabela = []
    for m in sorted(linhas, key=lambda x: -(x["utmos"] or 0)):
        u = f"{m['utmos']:.2f}" if m["utmos"] is not None else "—"
        l = (f"| {m['arquivo']} | {u} | {m['erro'] * 100:.0f}% | {m['tom_st']:.1f} | {m['faixa_st']:.1f} | {m['ppm']:.0f} | "
             f"{m['pausas_frase']:.1f} | {m['pausa_max']:.2f} s | {m['jitter']:.2f} | {m['shimmer']:.1f} | {m['hnr']:.1f} | {m['humano']}/6 |")
        print(l)
        tabela.append(l)
    if a.md:
        a.md.write_text("\n".join([cab, "|" + "---|" * 12] + tabela) + "\n", encoding="utf-8")
