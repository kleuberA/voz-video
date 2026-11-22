"""
Tempos PROVISÓRIOS de um episódio, estimados pelo texto da ficha, no mesmo formato do timing.json
que o montar_audio.py gera a partir da narração. Serve para começar a animação (e revisar o ritmo)
antes de a voz existir. Quando a narração sair, `montar_audio.py` grava o timing.json de verdade e a
animação passa a usá-lo sem mudar nada.

    python producao/tempo_provisorio.py videos/short-ep06-black-friday
    python producao/tempo_provisorio.py videos/short-ep06-black-friday --variante B

Saída: <episodio>/timing-provisorio.json (variante B: timing-provisorio-B.json), com "provisorio": true.
Os textos vêm da ficha indicada em config.json ("ficha"): fala 1 = gancho, depois as falas e a chamada.
Ritmo estimado: 165 palavras/min (o da voz v2), com pausas em vírgula e ponto.
"""
import argparse, json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
norm = lambda s: re.sub(r"[^\wà-úç]", "", s.lower())


def duracao_palavra(w):
    letras = len(re.sub(r"[^\wà-úç]", "", w.lower()))
    d = 0.10 + 0.052 * letras
    return d


def pausa_depois(w):
    if re.search(r"[.?!]$", w):
        return 0.22
    if re.search(r"[,:;]$", w):
        return 0.10
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodio", type=Path)
    ap.add_argument("--variante", default="A", choices=["A", "B"])
    a = ap.parse_args()
    ep = a.episodio
    cfg = json.loads((ep / "config.json").read_text(encoding="utf-8"))
    ficha = json.loads((BASE / cfg["ficha"]).read_text(encoding="utf-8"))
    gancho = next(g for g in ficha["ganchos"] if g["id"] == a.variante)
    textos = [gancho["fala"]] + ficha["falas"] + [ficha["cta"]["fala"]]
    if len(textos) != cfg["falas"]:
        sys.exit(f"config.json diz {cfg['falas']} falas, a ficha tem {len(textos)}.")

    gaps = {int(k): v for k, v in cfg["gaps"].items()}
    palavras, inicio, t = [], {}, cfg.get("lead", 0.1)
    for n, texto in enumerate(textos, 1):
        if n > 1:
            t += gaps.get(n, 0.3)
        inicio[n] = t
        ws = texto.split()
        for i, w in enumerate(ws):
            d = duracao_palavra(w)
            palavras.append({"w": w, "s": round(t, 3), "e": round(t + d, 3), "seg": n})
            t += d + (pausa_depois(w) if i < len(ws) - 1 else 0)
    duracao = round(t + cfg.get("cauda", 1.4), 2)

    def resolver(spec):
        if "word" in spec:
            hits = [w for w in palavras if w["seg"] == spec["seg"] and norm(w["w"]) == norm(spec["word"])]
            if not hits:
                sys.exit(f"Evento sem palavra: {spec}")
            base = hits[spec.get("ordem", 0)][spec.get("campo", "s")]
        elif "inicio" in spec:
            base = inicio[spec["inicio"]]
        else:
            sys.exit(f"Evento inválido (o provisório não tem contagem de quiz): {spec}")
        return base + spec.get("offset", 0)

    cues = {k: round(resolver(v), 3) for k, v in cfg["cues"].items()}
    ini = [(cid, 0.0 if i == 0 else resolver(spec)) for i, (cid, spec) in enumerate(cfg["cenas"])]
    cenas = {cid: {"start": round(s, 3), "end": round(ini[i + 1][1] if i + 1 < len(ini) else duracao, 3)} for i, (cid, s) in enumerate(ini)}

    # legenda: mesma regra do montar_audio.py (trocas, blocos de até 3 palavras)
    trocas = sorted(cfg.get("legenda", {}).items(), key=lambda kv: -len(kv[0].split()))
    legenda, i = [], 0
    while i < len(palavras):
        for falado, mostrado in trocas:
            partes = falado.split()
            bloco = palavras[i: i + len(partes)]
            if len(bloco) == len(partes) and all(b["seg"] == bloco[0]["seg"] for b in bloco) and [norm(b["w"]) for b in bloco] == [norm(x) for x in partes]:
                pont = re.search(r"[.,?!:;]+$", bloco[-1]["w"])
                legenda.append({**bloco[0], "w": mostrado + (pont.group(0) if pont else ""), "e": bloco[-1]["e"]})
                i += len(partes)
                break
        else:
            legenda.append(palavras[i])
            i += 1
    quentes = {norm(w) for w in cfg.get("quentes", [])}
    chunks, atual = [], []
    for i, w in enumerate(legenda):
        atual.append({"w": w["w"], "s": w["s"], "e": w["e"], **({"hot": True} if norm(w["w"]) in quentes else {})})
        prox = legenda[i + 1] if i + 1 < len(legenda) else None
        if len(atual) >= 3 or re.search(r"[.,?!:]$", w["w"]) or prox is None or prox["seg"] != w["seg"] or prox["s"] - w["e"] > 0.35:
            chunks.append({"s": atual[0]["s"], "e": atual[-1]["e"], "words": atual})
            atual = []

    sufixo = "" if a.variante == "A" else f"-{a.variante}"
    saida = ep / f"timing-provisorio{sufixo}.json"
    saida.write_text(json.dumps({"provisorio": True, "duration": duracao, "scenes": cenas, "cues": cues,
                                 "chunks": chunks, "words": palavras}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{saida}: {duracao:.1f} s, {len(palavras)} palavras, cenas " + ", ".join(f"{k} {v['end'] - v['start']:.1f}s" for k, v in cenas.items()))


if __name__ == "__main__":
    main()
