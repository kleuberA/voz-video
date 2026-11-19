# Episódio #4 "A banca troca uma palavra": publicação no YouTube e no Instagram

Formato novo (Canal 1): **uma situação real de estudo**, sem propaganda de recursos. O estudante cai na pegadinha do prazo do veto (CF, art. 66, § 1º), transforma o trecho em flashcard e revisa.

Arquivos: `video/out/shorts/ep04/estuda-leges-ep04.mp4` (com trilha), `estuda-leges-ep04-sem-trilha.mp4` e `estuda-leges-ep04-capa.png`. O mesmo vídeo serve para o Shorts e para o Reels (9:16, menos de 60 s).

## ⚠️ Antes de publicar

1. **Abra o link do artigo** (`https://estudaleges.com.br/leis/constituicao-federal/art-66`) e confira se ele mostra o art. 66. O endereço segue o padrão do código (`/leis/<lei>/<artigo>`), mas o nome da lei vem do banco. Se a Constituição tiver outro endereço, troque nos links abaixo.
2. **Confira se a oferta continua "7 dias de Premium grátis, sem cartão"**, que é o texto da landing hoje. O vídeo fala e mostra exatamente isso.

## Por que o link vai para o artigo (e não para a página inicial)

A página pública do artigo (`app/leis/[slug]/[artigo]`) abre **sem login**. Quem vem do vídeo cai no mesmo art. 66 que acabou de ver, com a faixa "Crie sua conta grátis pra…" embaixo. É o caminho mais curto entre o vídeo e o cadastro, e o cadastro já é medido no GA4 (`sign_up`, PR #135).

## YouTube Shorts

**Título:** `A banca trocou UMA palavra e você errou 😳 #shorts`

**Descrição:**
```
O Presidente tem 15 dias ÚTEIS pra vetar um projeto, não 20 (CF, art. 66, § 1º). É essa troca que a banca faz.

Ler não é lembrar: selecione o trecho, transforme em flashcard e revise no dia certo.

✅ Treine esse artigo no Estuda Leges (7 dias de Premium grátis, sem cartão):
https://estudaleges.com.br/leis/constituicao-federal/art-66?utm_source=youtube&utm_medium=shorts&utm_campaign=situacao_real&utm_content=ep04_descricao

#direitoconstitucional #oab #concursopublico #flashcards #estudos #shorts
```

**Comentário fixado:**
```
Você marcou certo ou errado? 👇

Gabarito: ERRADO. São 15 dias úteis (art. 66, § 1º). E no § 3º: passados 15 dias, o silêncio do Presidente vira sanção.

Treine o art. 66 👉 estudaleges.com.br/leis/constituicao-federal/art-66?utm_source=youtube&utm_medium=shorts&utm_campaign=situacao_real&utm_content=ep04_comentario
```

## Instagram Reels

No Reels, o link clicável é o **link da bio** (ou um sticker de link nos Stories). Use um link próprio do Instagram para separar a origem no GA4:

**Link da bio:**
```
https://estudaleges.com.br/leis/constituicao-federal/art-66?utm_source=instagram&utm_medium=bio&utm_campaign=situacao_real&utm_content=ep04
```

**Legenda:**
```
A banca trocou UMA palavra. Você acertaria? 👇

O Presidente tem 15 dias ÚTEIS pra vetar um projeto (CF, art. 66, § 1º), e a banca escreve 20.

Quem só lê a lei esquece. Selecione o trecho, vire flashcard e revise no dia certo.

Treine esse artigo: link na bio (7 dias de Premium grátis, sem cartão).

#direitoconstitucional #oab #concursos #concurseiros #estudardireito #flashcards
```

**Story do mesmo dia:** repostar o Reels com a enquete "Certo ou errado?" e um sticker de link com `utm_source=instagram&utm_medium=stories&utm_campaign=situacao_real&utm_content=ep04`.

## No GA4

Aquisição de tráfego → Campanha da sessão `situacao_real`. A dimensão "Origem/mídia da sessão" separa `youtube / shorts`, `instagram / bio` e `instagram / stories`. A conversão é o evento `sign_up`.
