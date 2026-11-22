"""
Gera o PUBLICACAO.md de um episódio a partir da ficha, com os links rastreados (UTM) de todos os
canais montados do mesmo jeito em todo episódio.

    python producao/publicacao.py producao/episodios/ep06.json                  # mostra na tela
    python producao/publicacao.py producao/episodios/ep06.json -o videos/short-ep06-x/PUBLICACAO.md

A oferta, o domínio e o padrão do link vêm de oferta.json. Nada de link escrito à mão.
"""
import argparse, json
from pathlib import Path
from urllib.parse import urlencode

AQUI = Path(__file__).parent
OFERTA = json.loads((AQUI / "oferta.json").read_text(encoding="utf-8"))


def link(f, canal):
    lk = f.get("link", {})
    base = OFERTA["link_artigo"].format(lei=lk["lei"], artigo=lk["artigo"]) if lk.get("lei") else OFERTA["link_inicio"]
    u = dict(OFERTA["utm"][canal])
    conteudo = u.pop("conteudo").format(ep=f["id"])
    u["utm_campaign"] = f.get("campanha", f.get("formato", "shorts"))
    u["utm_content"] = conteudo
    return f"{base}?{urlencode(u)}"


def gerar(f):
    p = f.get("publicacao", {})
    of = OFERTA["oferta"]
    tags = " ".join(p.get("hashtags", []))
    titulo = p.get("titulo_youtube", f.get("titulo_interno", ""))
    dm = p.get("palavra_dm")
    fontes = f.get("fontes", [])
    L = []
    add = L.append
    add(f"# {f['id']}: {f.get('titulo_interno', '')} — publicação\n")
    add(f"Formato: **{f.get('formato')}** · campanha `{f.get('campanha', '')}`. "
        "O mesmo vídeo serve para Shorts, Reels e TikTok.\n")

    ep = f["id"]
    add("## Arquivos\n")
    add(f"| Arquivo | Uso |\n|---|---|")
    add(f"| `estuda-leges-{ep}.mp4` | Gancho A, com trilha: Shorts, Reels e TikTok. |")
    add(f"| `estuda-leges-{ep}-sem-trilha.mp4` | Gancho A só com voz e efeitos, para pôr uma música em alta no app. |")
    add(f"| `estuda-leges-{ep}-B.mp4` | Gancho B: trial reel do Instagram (só para não seguidores). |")
    add(f"| `estuda-leges-{ep}-capa.png` (e `-B-capa.png`) | Capa do Reels. No Shorts, escolha o quadro de ~2 s no app. |")
    add("\nEnquanto os arquivos tiverem `-rascunho` no nome, **não publique**: falta conferir as fontes.\n")
    add("## ✅ Antes de publicar\n")
    add(f"- [ ] `python producao/qa_video.py <pasta do episódio>` sem ❌.")
    add(f"- [ ] O link abre o artigo certo: {link(f, 'youtube_descricao').split('?')[0]}")
    add(f"- [ ] A oferta continua \"{of['teste']}\" no site (oferta.json conferida em {OFERTA['conferida_em']}).")
    add("- [ ] Cada fonte abaixo conferida no site oficial, com o texto em vigor hoje.")
    add("- [ ] Vídeo A (gancho A) e vídeo B (gancho B) exportados. Publique o A; o B vai como trial reel no Instagram.")
    add("- [ ] Linha nova em `producao/resultados.csv` com data e hora da publicação.\n")

    if fontes:
        add("## Base legal (para responder nos comentários)\n")
        for fo in fontes:
            conf = f"conferido por {fo.get('conferido_por') or '—'} em {fo.get('conferido_em') or '—'}"
            add(f"- **{fo.get('norma')}, {fo.get('dispositivo')}**: \"{fo.get('texto_literal', '')}\" ({fo.get('url')}; {conf})")
        add("")

    add("## YouTube Shorts\n")
    add(f"**Título** ({len(titulo)} caracteres; ~40 aparecem no feed): `{titulo} #shorts`\n")
    for alt in p.get("titulos_alternativos", []):
        add(f"- Alternativa para o próximo teste: `{alt}`")
    add("\n**Descrição:**\n```")
    add(p.get("descricao", "").strip())
    if f.get("objetivo") == "cadastro":
        # vídeo de conversão: a chamada é a conta, não a leitura grátis (que dispensa o cadastro)
        add(f"\n✅ Treine este artigo: crie sua conta grátis ({of['teste']}):")
    else:
        add(f"\n📖 {of['gratis'].capitalize()}, e {of['teste']}:")
    add(link(f, "youtube_descricao"))
    add(f"\n{tags} #shorts\n```\n")
    add("**Comentário fixado:**\n```")
    add(p.get("comentario_fixado", "").strip())
    add(f"\n👉 {link(f, 'youtube_comentario')}\n```\n")
    add(f"**Link do perfil do canal:** `{link(f, 'youtube_perfil')}`\n")
    add("Ligue o Short a um vídeo do canal no campo \"Vídeo relacionado\" (é o único link clicável do Shorts).\n")

    add("## Instagram Reels\n")
    add(f"**Link da bio:** `{link(f, 'instagram_bio')}`\n")
    add("**Legenda:**\n```")
    add(p.get("legenda_instagram", "").strip())
    if dm:
        alvo = "o link pra treinar esse artigo" if f.get("objetivo") == "cadastro" else "o link do artigo"
        add(f"\nComenta {dm} que eu te mando {alvo} 📩")
    else:
        add("\nLink na bio.")
    add(f"\n{tags}\n```\n")
    if dm:
        add(f"**Resposta por DM** (automação de palavra-chave, ex.: ManyChat, ou à mão nas primeiras horas): "
            f"quem comentar **{dm}** recebe `{link(f, 'instagram_dm')}`. Cada comentário conta para a distribuição, "
            "e o link chega clicável na conversa.\n")
    add("**Trial reel:** publique o vídeo B (gancho B) como teste para não seguidores. "
        "Depois de 72 h compare a % que continuou assistindo com a do A.\n")
    if p.get("enquete_story"):
        add(f"**Story do mesmo dia:** repost do Reels + enquete \"{p['enquete_story']}\" + sticker de link `{link(f, 'instagram_stories')}`.\n")

    add("## TikTok\n")
    add(f"Mesma legenda do Instagram. Link da bio: `{link(f, 'tiktok_bio')}`.\n")

    if p.get("melhor_horario"):
        add(f"## Quando postar\n\n{p['melhor_horario']}.\n")

    add("## No GA4\n")
    add(f"Aquisição de tráfego → Campanha da sessão `{f.get('campanha', '')}`; conteúdo `{f['id']}_*`. "
        "Conversão: evento `sign_up`. Copie os números para `producao/resultados.csv` em 48 h e em 7 dias.\n")
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ficha")
    ap.add_argument("-o", "--saida", type=Path)
    a = ap.parse_args()
    ficha = json.loads(Path(a.ficha).read_text(encoding="utf-8"))
    texto = gerar(ficha)
    if a.saida:
        a.saida.write_text(texto, encoding="utf-8")
        print("gravado:", a.saida)
    else:
        print(texto)
