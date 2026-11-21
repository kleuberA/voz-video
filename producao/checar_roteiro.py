"""
Confere a ficha de um episódio ANTES de gerar a voz e a animação.

    python producao/checar_roteiro.py producao/episodios/ep06.json
    python producao/checar_roteiro.py producao/episodios/ep06.json --gerar-falas videos/short-ep06-x/narracao

Bloqueia (sai com código 1) quando falta o que não pode faltar:
  - fonte oficial de cada dispositivo citado (link de órgão oficial, texto literal copiado da
    fonte, quem conferiu e quando). Sem isso o episódio vai para revisão humana;
  - origem da questão (banca, ano e link) quando a questão é atribuída a uma prova;
  - dois ganchos (A e B), para testar o começo do vídeo;
  - promessa proibida (oferta.json) ou prazo de teste diferente da oferta atual.

Avisa (não bloqueia) sobre ritmo e pronúncia: gancho longo, vídeo fora de 20–35 s, chamada final
longa demais, frase com mais de 20 palavras, número em algarismo, sigla e as palavras que a voz já
errou (pronuncia.json).

Com --gerar-falas, grava p1.txt (gancho A), p1b.txt (gancho B), p2.txt… e roteiro.txt, prontos
para gerar_clonada.py. Só grava se não houver bloqueio.
"""
import argparse, json, re, sys
from pathlib import Path
from urllib.parse import urlparse

AQUI = Path(__file__).parent
OFERTA = json.loads((AQUI / "oferta.json").read_text(encoding="utf-8"))
PRONUNCIA = json.loads((AQUI / "pronuncia.json").read_text(encoding="utf-8"))["trocas"]

PPM = 165            # palavras por minuto da voz v2 (medido)
PAUSA_FALAS = 0.30   # segundos entre falas na montagem
FORMATOS = {"dia_a_dia", "pegadinha", "tecnica", "demonstracao"}
# formatos em que a chamada pode ser mais longa (o produto é o assunto)
CTA_MAX = {"demonstracao": 0.25}
CTA_MAX_PADRAO = 0.15



def palavras(texto):
    return [p for p in re.split(r"\s+", texto.strip()) if p]


def segundos(texto):
    return len(palavras(texto)) / PPM * 60


def frases(texto):
    return [f for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f]


class Relatorio:
    def __init__(self):
        self.erros, self.avisos, self.info = [], [], []

    def erro(self, msg):
        self.erros.append(msg)

    def aviso(self, msg):
        self.avisos.append(msg)

    def dado(self, msg):
        self.info.append(msg)

    def imprimir(self):
        for m in self.info:
            print(f"  · {m}")
        for m in self.avisos:
            print(f"  ⚠ {m}")
        for m in self.erros:
            print(f"  ✗ {m}")
        if self.erros:
            print(f"\nBLOQUEADO: {len(self.erros)} problema(s). Corrija a ficha ou peça revisão humana antes de narrar.")
        else:
            print(f"\nOK para narrar ({len(self.avisos)} aviso(s)).")


def checar_fontes(f, r):
    fontes = f.get("fontes") or []
    if not fontes:
        if f.get("formato") == "tecnica" and not f.get("cita_lei", False):
            r.dado("Sem dispositivo citado (técnica de estudo): nenhuma fonte exigida.")
            return
        r.erro("Nenhuma fonte jurídica. Todo dispositivo citado precisa de fonte oficial conferida.")
        return
    oficiais = OFERTA["fontes_oficiais"]
    for i, fonte in enumerate(fontes, 1):
        nome = f"fonte {i} ({fonte.get('norma', '?')}, {fonte.get('dispositivo', '?')})"
        for campo in ("norma", "dispositivo", "url", "texto_literal", "conferido_por", "conferido_em"):
            if not str(fonte.get(campo, "")).strip():
                r.erro(f"{nome}: falta '{campo}'.")
        url = fonte.get("url", "")
        if url:
            host = urlparse(url).hostname or ""
            if not any(host == d or host.endswith("." + d) for d in oficiais):
                r.erro(f"{nome}: '{host}' não é fonte oficial (use Planalto, DOU, Câmara, Senado ou tribunal).")
        data = str(fonte.get("conferido_em", ""))
        if data and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
            r.erro(f"{nome}: 'conferido_em' deve ser AAAA-MM-DD.")
        if fonte.get("vigencia_futura"):
            r.aviso(f"{nome}: dispositivo com vigência futura. O roteiro precisa dizer a partir de quando vale.")


def checar_questao(f, r):
    q = f.get("questao")
    if not q:
        return
    origem = q.get("origem")
    if origem not in ("banca", "adaptada", "app"):
        r.erro("questao.origem deve ser 'banca', 'adaptada' ou 'app' (gerada pelo treino de literalidade).")
    if origem == "banca":
        for campo in ("banca", "ano", "cargo", "fonte_url"):
            if not str(q.get(campo, "")).strip():
                r.erro(f"Questão atribuída a banca sem '{campo}'. Sem a prova em mãos, use origem 'adaptada'.")
    if origem == "adaptada" and not re.search(r"adaptad", json.dumps(f, ensure_ascii=False), re.I):
        r.aviso("Questão adaptada: diga 'questão adaptada' na tela ou na legenda, nunca o nome de uma banca.")


def checar_textos(f, r, todas_falas):
    tudo = " ".join(todas_falas + [c.get("texto_tela", "") for c in f.get("cenas", [])]
                    + [f.get("cta", {}).get("tela", "")]
                    + [str(v) for v in (f.get("publicacao") or {}).values()]).lower()
    for proibida in OFERTA["promessas_proibidas"]:
        if proibida.lower() in tudo:
            r.erro(f"Promessa proibida: '{proibida}'.")
    dias = OFERTA["oferta"]["dias_teste"]
    for m in re.finditer(r"(\d+|sete|catorze|quatorze|trinta)\s+dias\s+de\s+(premium|acesso)", tudo):
        n = {"sete": 7, "catorze": 14, "quatorze": 14, "trinta": 30}.get(m.group(1), m.group(1))
        if int(n) != dias:
            r.erro(f"Oferta diferente da atual: '{m.group(0)}' (oferta.json diz {dias} dias).")


def checar_pronuncia(nome, texto, r):
    for t in PRONUNCIA:
        alvo = t["escrito"]
        padrao = re.escape(alvo) if not alvo.isalpha() else rf"\b{re.escape(alvo)}\b"
        if re.search(padrao, texto):
            r.aviso(f"{nome}: '{alvo}' → escreva '{t['falar']}' ({t['motivo']}).")
    if re.search(r"\d", texto):
        r.aviso(f"{nome}: número em algarismo. Escreva por extenso (a legenda volta para algarismo pelo config.json).")
    for fr in frases(texto):
        if len(palavras(fr)) > 20:
            r.aviso(f"{nome}: frase com {len(palavras(fr))} palavras. Quebre em frases de até 20.")


def checar(f):
    r = Relatorio()
    formato = f.get("formato")
    if formato not in FORMATOS:
        r.erro(f"formato deve ser um de {sorted(FORMATOS)}.")
    for campo in ("id", "problema", "ganchos", "falas", "cta"):
        if not f.get(campo):
            r.erro(f"Falta '{campo}'.")
    if r.erros:
        return r

    ganchos = f["ganchos"]
    if len(ganchos) < 2:
        r.erro("Escreva dois ganchos (A e B). O começo é o que decide se a pessoa desliza.")
    for g in ganchos:
        nome = f"gancho {g.get('id', '?')}"
        primeira = (frases(g.get("fala", "")) or [""])[0]
        s = segundos(primeira)
        if s > 3.0:
            r.aviso(f"{nome}: a 1ª frase leva {s:.1f} s. A ideia central precisa caber nos 2 primeiros segundos (≈ 6 palavras).")
        tela = g.get("tela", "")
        if not tela:
            r.erro(f"{nome}: falta 'tela' (o texto que aparece INTEIRO no quadro 0).")
        elif len(palavras(tela)) > 9:
            r.aviso(f"{nome}: texto de tela com {len(palavras(tela))} palavras. Até 8 cabem em letra grande no celular.")
        checar_pronuncia(nome, g.get("fala", ""), r)

    falas = f["falas"]
    cta = f["cta"].get("fala", "")
    for i, fala in enumerate(falas, 2):
        checar_pronuncia(f"fala {i}", fala, r)
    checar_pronuncia("chamada", cta, r)

    gancho = ganchos[0].get("fala", "")
    corpo = sum(segundos(x) for x in falas)
    s_cta = segundos(cta)
    total = segundos(gancho) + corpo + s_cta + PAUSA_FALAS * (len(falas) + 1) + f.get("extra_s", 0) + 1.2
    r.dado(f"Duração estimada: {total:.1f} s (gancho {segundos(gancho):.1f} s, miolo {corpo:.1f} s, chamada {s_cta:.1f} s; +{f.get('extra_s', 0)} s de contagem/efeitos).")
    if total < 20:
        r.aviso("Abaixo de 20 s: falta desenvolvimento ou a revelação vem cedo demais.")
    elif total > 35:
        r.aviso(f"Acima de 35 s. Corte {total - 32:.0f} s do miolo: cada segundo a mais derruba a % assistida.")
    limite = CTA_MAX.get(formato, CTA_MAX_PADRAO)
    if s_cta / total > limite:
        r.aviso(f"Chamada final com {s_cta:.1f} s ({s_cta / total:.0%} do vídeo; limite {limite:.0%}). Deixe a oferta em uma frase e ponha o resto na tela.")
    if not re.search(r"perfil|bio|link|comenta|salva", cta, re.I):
        r.aviso("A chamada não diz o que fazer (link no perfil, comentar, salvar).")

    checar_fontes(f, r)
    checar_questao(f, r)
    checar_textos(f, r, [g.get("fala", "") for g in ganchos] + falas + [cta])

    pub = f.get("publicacao") or {}
    titulo = pub.get("titulo_youtube", "")
    if not titulo:
        r.aviso("Sem título do YouTube (publicacao.titulo_youtube).")
    elif len(titulo) > 60:
        r.aviso(f"Título com {len(titulo)} caracteres. No feed aparecem ~40.")
    if not pub.get("comentario_fixado"):
        r.aviso("Sem comentário fixado: ele puxa os comentários que dão distribuição.")
    if not f.get("link", {}).get("lei"):
        r.aviso("Sem link.lei/link.artigo: o link vai para a página inicial, não para o artigo do vídeo.")
    return r


def gerar_falas(f, destino):
    destino.mkdir(parents=True, exist_ok=True)
    a, b = f["ganchos"][0]["fala"], f["ganchos"][1]["fala"]
    (destino / "p1.txt").write_text(a + "\n", encoding="utf-8")
    (destino / "p1b.txt").write_text(b + "\n", encoding="utf-8")
    textos = f["falas"] + [f["cta"]["fala"]]
    for i, t in enumerate(textos, 2):
        (destino / f"p{i}.txt").write_text(t + "\n", encoding="utf-8")
    (destino / "roteiro.txt").write_text("\n\n".join([a] + textos) + "\n", encoding="utf-8")
    print(f"Falas gravadas em {destino}: p1 (gancho A), p1b (gancho B), p2…p{len(textos) + 1}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ficha")
    ap.add_argument("--gerar-falas", type=Path)
    # --rascunho: grava as falas mesmo com a CONFERÊNCIA das fontes pendente (link e texto literal
    # continuam obrigatórios). O vídeo sai marcado "FONTES NÃO CONFERIDAS" e não pode ser publicado.
    ap.add_argument("--rascunho", action="store_true")
    a = ap.parse_args()
    ficha = json.loads(Path(a.ficha).read_text(encoding="utf-8"))
    print(f"{ficha.get('id', '?')} · {ficha.get('titulo_interno', '')}")
    rel = checar(ficha)
    rel.imprimir()
    pendencia = lambda m: re.search(r"falta '(conferido_por|conferido_em)'", m)
    if rel.erros and not (a.rascunho and all(pendencia(m) for m in rel.erros)):
        sys.exit(1)
    if a.gerar_falas:
        gerar_falas(ficha, a.gerar_falas)
        marca = a.gerar_falas / "RASCUNHO.txt"
        if rel.erros:
            marca.write_text("Falas gravadas com a conferência das fontes pendente. O vídeo sai marcado e não pode ser publicado.\n", encoding="utf-8")
            print("\nRASCUNHO: conferência das fontes pendente. O vídeo sai marcado e não pode ser publicado.")
        elif marca.exists():
            marca.unlink()
