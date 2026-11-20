"""
Controle de qualidade do vídeo final, antes de publicar.

    python producao/qa_video.py videos/short-ep05-restaurante
    python producao/qa_video.py videos/short-ep05-restaurante --salvar      # grava QA.md e qa-folha.jpg na pasta
    python producao/qa_video.py videos/*/ --resumo                          # uma linha por episódio

Mede o que decide a retenção e o que o olho deixa passar:
  - formato: 1080×1920, 30 fps, H.264 + AAC;
  - duração (meta 20–35 s) e parte do vídeo gasta com a chamada final (timing.json);
  - áudio: −14 LUFS, pico real ≤ −1 dBTP, voz começando em até 0,3 s, nenhum silêncio > 0,6 s;
  - quadro 0: tem conteúdo de verdade? (é o que aparece enquanto a pessoa decide se desliza);
  - metade de baixo vazia no quadro 0 (texto concentrado no topo, centro da tela sem nada);
  - áreas cobertas pelos botões e pela legenda do Shorts/Reels;
  - trechos parados (nada muda na tela por mais de 2,5 s).
Requer ffmpeg/ffprobe, numpy e Pillow.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 270, 480          # resolução de análise (1/4 de 1080×1920)
FPS_ANALISE = 4
# Áreas que a interface cobre no celular (fração da tela). Shorts e Reels: legenda/canal embaixo,
# botões (curtir, comentar, compartilhar) na coluna direita da metade de baixo.
ZONA_BAIXO = 0.20
ZONA_DIREITA = 0.12


def sh(args):
    return subprocess.run(args, capture_output=True, text=True)


def achar_video(alvo: Path):
    if alvo.is_file():
        return alvo, alvo.parent
    mp4 = [p for p in sorted(alvo.glob("*.mp4")) if "sem-trilha" not in p.name]
    if not mp4:
        sys.exit(f"Nenhum .mp4 em {alvo}")
    return mp4[0], alvo


def sondar(f):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_entries",
                       "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
                       "-of", "json", str(f)]).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = v["r_frame_rate"].split("/")
    return {"largura": v["width"], "altura": v["height"], "fps": float(num) / float(den),
            "vcodec": v["codec_name"], "acodec": a["codec_name"] if a else None,
            "duracao": float(j["format"]["duration"])}


def audio(f, duracao):
    err = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    resumo = err[err.rfind("Summary:"):]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", resumo).group(1))
    pico = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", resumo)
    pico = float(pico.group(1)) if pico and pico.group(1) != "-inf" else None
    err = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-af", "silencedetect=n=-38dB:d=0.25", "-f", "null", "-"]).stderr
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    inicio_voz = 0.0
    silencios = []
    for i, s in enumerate(ini):
        e = fim[i] if i < len(fim) else duracao
        if s <= 0.05:
            inicio_voz = e
            continue
        if e >= duracao - 0.05:      # cauda do vídeo
            continue
        if e - s > 0.6:
            silencios.append((round(s, 2), round(e - s, 2)))
    return {"lufs": lufs, "pico": pico, "inicio_voz": inicio_voz, "silencios": silencios}


def quadros(f):
    out = sh_bytes(["ffmpeg", "-v", "error", "-i", str(f), "-vf",
                    f"fps={FPS_ANALISE},scale={W}:{H},format=gray", "-f", "rawvideo", "-"])
    return np.frombuffer(out, np.uint8).reshape(-1, H, W).astype(np.int16)


def sh_bytes(args):
    return subprocess.run(args, capture_output=True).stdout


def bordas(q):
    """Fração de pixels com borda (texto, cartões, ícones): mede 'tem coisa na tela'."""
    gx = np.abs(np.diff(q, axis=1))[:-1, :]
    gy = np.abs(np.diff(q, axis=0))[:, :-1]
    return (gx + gy) > 28


def imagem(q):
    b = bordas(q)
    h = b.shape[0]
    terco = [b[i * h // 3:(i + 1) * h // 3].mean() for i in range(3)]
    baixo = b[int(h * (1 - ZONA_BAIXO)):].mean()
    direita = b[h // 2:, int(b.shape[1] * (1 - ZONA_DIREITA)):].mean()
    return b.mean(), terco, baixo, direita


def video(f):
    qs = quadros(f)
    dens, baixo, direita = [], [], []
    for q in qs:
        d, _, b, r = imagem(q)
        dens.append(d)
        baixo.append(b)
        direita.append(r)
    d0, tercos0, _, _ = imagem(qs[0])
    mediana = float(np.median(dens))
    # quadros parados: menos de 0,15% dos pixels mudam mais de 10 níveis
    mudou = [(np.abs(qs[i] - qs[i - 1]) > 10).mean() > 0.0015 for i in range(1, len(qs))]
    maior, corrida, inicio, ini_maior = 0, 0, 0, 0
    for i, m in enumerate(mudou):
        if m:
            corrida = 0
        else:
            if corrida == 0:
                inicio = i
            corrida += 1
            if corrida > maior:
                maior, ini_maior = corrida, inicio
    return {"densidade_q0": d0, "densidade_mediana": mediana, "tercos_q0": tercos0,
            "pct_baixo": float(np.mean(np.array(baixo) > 0.02)), "pct_direita": float(np.mean(np.array(direita) > 0.03)),
            "parado_s": maior / FPS_ANALISE, "parado_em": ini_maior / FPS_ANALISE}


def tempos(pasta, duracao):
    t = pasta / "timing.json"
    if not t.exists():
        return None
    j = json.loads(t.read_text(encoding="utf-8"))
    cenas = j.get("scenes", {})
    cta = cenas.get("cta")
    palavras = [w for c in j.get("chunks", []) for w in c.get("words", [])]
    falando = sum(w["e"] - w["s"] for w in palavras) or 1
    # a contagem do quiz é silêncio de propósito: não conta como pausa
    timer = j.get("cues", {}).get("timer")
    lacunas = [(round(a["e"], 2), round(b["s"] - a["e"], 2)) for a, b in zip(palavras, palavras[1:])
               if b["s"] - a["e"] > 0.6 and not (timer is not None and a["e"] - 0.5 <= timer <= b["s"])]
    return {"cta_s": (cta["end"] - cta["start"]) if cta else None,
            "cta_pct": (cta["end"] - cta["start"]) / duracao if cta else None,
            "ppm": len(palavras) / falando * 60 if palavras else None,
            "lacunas_fala": lacunas, "cenas": {k: round(v["end"] - v["start"], 1) for k, v in cenas.items()}}


def avaliar(info, au, vi, ti):
    """Lista de (nivel, mensagem). nivel: ok / aviso / erro."""
    r = []
    add = lambda n, m: r.append((n, m))
    if (info["largura"], info["altura"]) != (1080, 1920):
        add("erro", f"Resolução {info['largura']}×{info['altura']} (precisa 1080×1920).")
    if round(info["fps"]) not in (30, 60):
        add("aviso", f"{info['fps']:.2f} fps (use 30).")
    if info["vcodec"] != "h264" or info["acodec"] != "aac":
        add("aviso", f"Codecs {info['vcodec']}/{info['acodec']} (use h264/aac).")
    d = info["duracao"]
    if d > 60:
        add("erro", f"{d:.1f} s: longo demais para o formato.")
    elif d > 35:
        add("aviso", f"{d:.1f} s: acima de 35 s. Vídeo mais curto = maior % assistida.")
    elif d < 20:
        add("aviso", f"{d:.1f} s: abaixo de 20 s.")
    else:
        add("ok", f"{d:.1f} s.")
    if abs(au["lufs"] + 14) > 1:
        add("aviso", f"Volume {au['lufs']:.1f} LUFS (alvo −14).")
    else:
        add("ok", f"Volume {au['lufs']:.1f} LUFS.")
    if au["pico"] is not None and au["pico"] > -1.0:
        add("aviso", f"Pico real {au['pico']:.1f} dBTP (máx. −1): pode distorcer no celular.")
    if au["inicio_voz"] > 0.3:
        add("aviso", f"O som começa em {au['inicio_voz']:.2f} s. O gancho falado precisa começar no 1º quadro.")
    for s, dur in au["silencios"]:
        add("aviso", f"Silêncio de {dur:.1f} s em {s:.1f} s.")
    razao = vi["densidade_q0"] / vi["densidade_mediana"] if vi["densidade_mediana"] else 1
    if razao < 0.6:
        add("erro", f"Quadro 0 quase vazio ({razao:.0%} do conteúdo de um quadro típico). É o quadro que decide o deslize.")
    elif razao < 0.85:
        add("aviso", f"Quadro 0 com pouco conteúdo ({razao:.0%} de um quadro típico).")
    else:
        add("ok", f"Quadro 0 cheio ({razao:.0%} de um quadro típico).")
    alto, meio, baixo = vi["tercos_q0"]
    if alto > 0 and (meio + baixo) / 2 < alto * 0.25:
        add("aviso", "Quadro 0 com tudo no terço de cima e o centro da tela vazio. Traga o gancho para o meio e aumente a letra.")
    if vi["pct_baixo"] > 0.15:
        add("aviso", f"Conteúdo nos {ZONA_BAIXO:.0%} de baixo em {vi['pct_baixo']:.0%} do vídeo (área da legenda e do nome do canal).")
    if vi["pct_direita"] > 0.15:
        add("aviso", f"Conteúdo na coluna direita (botões) em {vi['pct_direita']:.0%} do vídeo.")
    if vi["parado_s"] > 2.5:
        add("aviso", f"Tela parada por {vi['parado_s']:.1f} s a partir de {vi['parado_em']:.1f} s.")
    if ti:
        if ti["cta_pct"] is not None:
            if ti["cta_pct"] > 0.15:
                add("aviso", f"Chamada final com {ti['cta_s']:.1f} s ({ti['cta_pct']:.0%} do vídeo). Meta: até 15% (≈ 5 s). Quem sai antes do fim derruba a retenção.")
            else:
                add("ok", f"Chamada final com {ti['cta_s']:.1f} s ({ti['cta_pct']:.0%}).")
        if ti["ppm"] and not 150 <= ti["ppm"] <= 200:
            add("aviso", f"Ritmo da fala {ti['ppm']:.0f} palavras/min (natural: 150–195).")
        for s, dur in ti["lacunas_fala"]:
            add("aviso", f"Pausa de {dur:.1f} s na fala em {s:.1f} s.")
    return r


def folha(f, destino):
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf", "fps=1,scale=216:-1,tile=8x5", "-frames:v", "1", "-q:v", "4", str(destino)])


def processar(alvo, salvar):
    f, pasta = achar_video(Path(alvo))
    info = sondar(f)
    au = audio(f, info["duracao"])
    vi = video(f)
    ti = tempos(pasta, info["duracao"])
    return f, pasta, info, au, vi, ti, avaliar(info, au, vi, ti)


def markdown(f, info, au, vi, ti, itens):
    simb = {"ok": "✅", "aviso": "⚠️", "erro": "❌"}
    linhas = [f"# QA de `{f.name}`", "",
              f"{info['largura']}×{info['altura']}, {info['fps']:.0f} fps, {info['duracao']:.1f} s, "
              f"{au['lufs']:.1f} LUFS" + (f", cenas: {ti['cenas']}" if ti else ""), ""]
    linhas += [f"- {simb[n]} {m}" for n, m in itens]
    linhas += ["", "Folha de quadros (1 por segundo): `qa-folha.jpg`.", ""]
    return "\n".join(linhas)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("alvos", nargs="+")
    ap.add_argument("--salvar", action="store_true")
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    pior = 0
    for alvo in a.alvos:
        f, pasta, info, au, vi, ti, itens = processar(alvo, a.salvar)
        erros = sum(n == "erro" for n, _ in itens)
        avisos = sum(n == "aviso" for n, _ in itens)
        pior = max(pior, 1 if erros else 0)
        if a.resumo:
            cta = f"{ti['cta_pct']:.0%}" if ti and ti["cta_pct"] is not None else "—"
            print(f"{pasta.name:34} {info['duracao']:5.1f}s  chamada {cta:>4}  quadro0 {vi['densidade_q0'] / vi['densidade_mediana']:4.0%}  "
                  f"parado {vi['parado_s']:3.1f}s  {au['lufs']:.1f} LUFS  → {erros} erro(s), {avisos} aviso(s)")
            continue
        print(markdown(f, info, au, vi, ti, itens))
        if a.salvar:
            (pasta / "QA.md").write_text(markdown(f, info, au, vi, ti, itens), encoding="utf-8")
            folha(f, pasta / "qa-folha.jpg")
            print(f"gravado: {pasta / 'QA.md'} e {pasta / 'qa-folha.jpg'}")
    sys.exit(pior)
