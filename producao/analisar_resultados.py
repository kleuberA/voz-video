"""
Lê producao/resultados.csv e diz, para cada vídeo, qual parte falhou e o que mudar no próximo.

    python producao/analisar_resultados.py
    python producao/analisar_resultados.py --plataforma instagram

Metas (as mesmas do ESTRATEGIA.md): continuou assistindo > 60%, duração média > 70% do vídeo,
> 5 comentários por mil views. A ordem do diagnóstico segue o funil: primeiro o gancho (se a pessoa
desliza, nada mais importa), depois o miolo, depois a conversa, depois o clique.
"""
import argparse, csv
from collections import defaultdict
from pathlib import Path

ARQ = Path(__file__).parent / "resultados.csv"
META_CONTINUOU = 60.0
META_MEDIA = 0.70
META_COMENT = 5.0


def num(x):
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


def diagnostico(r):
    out = []
    views, cont = num(r["views"]), num(r["pct_continuou"])
    dur, media = num(r["duracao_s"]), num(r["media_s"])
    com, cad = num(r["comentarios"]), num(r["cadastros_ga4"])
    if not views:
        return ["sem dados: preencha em 48 h e em 7 dias"]
    if cont is not None and cont < META_CONTINUOU:
        out.append(f"GANCHO: só {cont:.0f}% continuaram (meta {META_CONTINUOU:.0f}%). Troque os 2 primeiros segundos: texto grande e inteiro no quadro 0, afirmação contraintuitiva, algo se mexendo já no 1º segundo.")
    if dur and media is not None and media / dur < META_MEDIA:
        out.append(f"MIOLO: média {media:.0f} s de {dur:.0f} s ({media / dur:.0%}). Corte o trecho mais longo sem novidade e encurte a chamada final.")
    if com is not None and views and com / views * 1000 < META_COMENT:
        out.append(f"CONVERSA: {com / views * 1000:.1f} comentários por mil views. Comentário fixado com opinião (\"você paga ou não?\") e palavra-chave de DM.")
    if views < 300:
        out.append("ALCANCE: o algoritmo parou cedo. Tema com procura (notícia, situação do dia a dia) pesa mais que o formato.")
    if cad is not None and views:
        out.append(f"FUNIL: {cad:.0f} cadastro(s), {cad / views * 1000:.1f} por mil views.")
    return out or ["dentro das metas: faça uma variação do mesmo tema/formato"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plataforma")
    a = ap.parse_args()
    linhas = [r for r in csv.DictReader(ARQ.open(encoding="utf-8")) if not a.plataforma or r["plataforma"] == a.plataforma]
    por_formato = defaultdict(list)
    for r in linhas:
        print(f"\n{r['ep']}{r['variante']} · {r['plataforma']} · {r['formato']} · {r['tema']}")
        print(f"  views {r['views'] or '—'} · continuou {r['pct_continuou'] or '—'}% · média {r['media_s'] or '—'}/{r['duracao_s'] or '—'} s · comentários {r['comentarios'] or '—'} · cadastros {r['cadastros_ga4'] or '—'}")
        for d in diagnostico(r):
            print(f"  → {d}")
        if num(r["views"]):
            por_formato[r["formato"]].append(r)
    if por_formato:
        print("\nPor formato (só vídeos com dados):")
        for fmt, rs in sorted(por_formato.items()):
            v = [num(r["views"]) for r in rs]
            c = [num(r["pct_continuou"]) for r in rs if num(r["pct_continuou"]) is not None]
            print(f"  {fmt:13} {len(rs)} vídeo(s) · views médias {sum(v) / len(v):.0f}" + (f" · continuou {sum(c) / len(c):.0f}%" if c else ""))
