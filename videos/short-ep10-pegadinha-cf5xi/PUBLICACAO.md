# ep10: Pegadinha da CF, art. 5º, XI: ordem judicial só durante o dia — publicação

Formato: **pegadinha** · campanha `pegadinha_cf5xi`. O mesmo vídeo serve para Shorts, Reels e TikTok.

## Arquivos

| Arquivo | Uso |
|---|---|
| `estuda-leges-ep10.mp4` | Gancho A, com trilha: Shorts, Reels e TikTok. |
| `estuda-leges-ep10-sem-trilha.mp4` | Gancho A só com voz e efeitos, para pôr uma música em alta no app. |
| `estuda-leges-ep10-B.mp4` | Gancho B: trial reel do Instagram (só para não seguidores). |
| `estuda-leges-ep10-capa.png` (e `-B-capa.png`) | Capa do Reels. No Shorts, escolha o quadro de ~2 s no app. |

Enquanto os arquivos tiverem `-rascunho` no nome, **não publique**: falta conferir as fontes.

## ✅ Antes de publicar

- [ ] `python producao/qa_video.py <pasta do episódio>` sem ❌.
- [ ] O link abre o artigo certo: https://estudaleges.com.br
- [ ] A oferta continua "7 dias de Premium grátis, sem cartão" no site (oferta.json conferida em 2026-11-20).
- [ ] Cada fonte abaixo conferida no site oficial, com o texto em vigor hoje.
- [ ] Vídeo A (gancho A) e vídeo B (gancho B) exportados. Publique o A; o B vai como trial reel no Instagram.
- [ ] Linha nova em `producao/resultados.csv` com data e hora da publicação.

## Base legal (para responder nos comentários)

- **Constituição Federal de 1988, art. 5º, XI**: "XI - a casa é asilo inviolável do indivíduo, ninguém nela podendo penetrar sem consentimento do morador, salvo em caso de flagrante delito ou desastre, ou para prestar socorro, ou, durante o dia, por determinação judicial;" (https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm; conferido por — em —)

## YouTube Shorts

**Título** (59 caracteres; ~40 aparecem no feed): `Polícia entra à noite com ordem judicial? (CF, art. 5º, XI) #shorts`

- Alternativa para o próximo teste: `Pegadinha da CF: casa inviolável (Art. 5º, XI) #concursos`
- Alternativa para o próximo teste: `A banca trocou UMA palavra. Você perceberia? (Art. 5º, XI)`

**Descrição:**
```
A banca troca uma palavra e você perde o ponto.

CF, art. 5º, XI: com ordem judicial, só DURANTE O DIA. Sem consentimento do morador, a qualquer hora, só em flagrante, desastre ou para prestar socorro.

Treine a lei seca no Estuda Leges: 7 dias grátis, sem cartão.

✅ Treine este artigo: crie sua conta grátis (7 dias de Premium grátis, sem cartão):
https://estudaleges.com.br?utm_source=youtube&utm_medium=shorts&utm_campaign=pegadinha_cf5xi&utm_content=ep10_descricao

#concursos #leiseca #cebraspe #oab #direitoconstitucional #shorts
```

**Comentário fixado:**
```
Acertou? Comenta CERTO ou ERRADO 👇 Tem muito mais dessas no link do perfil.

👉 https://estudaleges.com.br?utm_source=youtube&utm_medium=shorts&utm_campaign=pegadinha_cf5xi&utm_content=ep10_comentario
```

**Link do perfil do canal:** `https://estudaleges.com.br?utm_source=youtube&utm_medium=perfil&utm_campaign=pegadinha_cf5xi&utm_content=ep10`

Ligue o Short a um vídeo do canal no campo "Vídeo relacionado" (é o único link clicável do Shorts).

## Instagram Reels

**Link da bio:** `https://estudaleges.com.br?utm_source=instagram&utm_medium=bio&utm_campaign=pegadinha_cf5xi&utm_content=ep10`

**Legenda:**
```
Certo ou errado? 🤔 A banca troca uma palavra e você perde o ponto.

Treine a lei seca no Estuda Leges: 7 dias grátis, sem cartão.

Comenta TREINO que eu te mando o link pra treinar esse artigo 📩

#concursos #leiseca #cebraspe #oab #direitoconstitucional
```

**Resposta por DM** (automação de palavra-chave, ex.: ManyChat, ou à mão nas primeiras horas): quem comentar **TREINO** recebe `https://estudaleges.com.br?utm_source=instagram&utm_medium=dm&utm_campaign=pegadinha_cf5xi&utm_content=ep10`. Cada comentário conta para a distribuição, e o link chega clicável na conversa.

**Trial reel:** publique o vídeo B (gancho B) como teste para não seguidores. Depois de 72 h compare a % que continuou assistindo com a do A.

**Story do mesmo dia:** repost do Reels + enquete "Polícia entra à noite com ordem judicial? (Sim / Não)" + sticker de link `https://estudaleges.com.br?utm_source=instagram&utm_medium=stories&utm_campaign=pegadinha_cf5xi&utm_content=ep10`.

## TikTok

Mesma legenda do Instagram. Link da bio: `https://estudaleges.com.br?utm_source=tiktok&utm_medium=bio&utm_campaign=pegadinha_cf5xi&utm_content=ep10`.

## Quando postar

3 dias seguidos, um gancho por dia (A, B, C), entre 19h e 22h; avaliar só depois de 7 dias.

## No GA4

Aquisição de tráfego → Campanha da sessão `pegadinha_cf5xi`; conteúdo `ep10_*`. Conversão: evento `sign_up`. Copie os números para `producao/resultados.csv` em 48 h e em 7 dias.
