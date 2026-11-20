# Diagnóstico dos Shorts #1 a #5 (20/11/2026)

Fontes: os vídeos finais deste repositório medidos com `qa_video.py` (relatórios em `videos/*/QA.md`
e `qa-folha.jpg`), os `timing.json`, os textos de publicação e os resultados registrados no
`ESTRATEGIA.md` do juris-app. Os números do #3 ao #5 **não foram registrados em lugar nenhum**: essa é
a primeira lacuna a fechar.

## Medições

| Episódio | Duração | Chamada final | Quadro 0* | Maior trecho parado | Pausas > 0,6 s na fala |
|---|---|---|---|---|---|
| #1 Presidente (art. 86) | 44,6 s | 7,9 s (18%) | **34%** ❌ | 0,8 s | 4 (0,7–1,1 s) |
| #2 Deputado (art. 53) | 35,4 s | 5,3 s (15%) | 107% | 1,8 s | 2 (1,4 s; 2,6 s na contagem) |
| #3 Escala 6x1 | 33,3 s | 5,7 s (17%) | 92% | 0,8 s | 3 (0,8–1,0 s) |
| #4 Banca troca palavra | 37,0 s | **9,5 s (26%)** | 60% | **5,0 s desde 0 s** | 2 (0,7 s) |
| #5 Restaurante | 37,4 s | **9,7 s (26%)** | 111% | **5,5 s desde 0,8 s** | 3 (1,0–1,3 s) |

\* Conteúdo do 1º quadro em relação a um quadro típico do vídeo. Abaixo de 60% = quase vazio.
Volume: todos em −14 LUFS (correto).

## O que está errado e o que muda

### 1. Os primeiros 5 segundos estão parados (#4 e #5)

O #5 abre com a conta cheia, o que está certo, mas **nada se mexe de 0,8 s a 6,3 s** enquanto a voz
lê o gancho. O #4 fica 5 s parado no "Certo / Errado". É exatamente a janela em que a pessoa decide
se desliza, e o #1 já mostrou o custo: 56% deslizaram.
**Regra nova:** nos primeiros 5 s, algo muda na tela a cada 1–1,5 s, acompanhando a fala (o item da
conta acende quando é citado, o total pisca, o número gira). `qa_video.py` acusa trecho parado > 2,5 s.

### 2. O gancho do #4 regrediu

Os #2 e #3 tinham manchete grande no centro. O #4 voltou à frase pequena no topo, com o meio da tela
vazio (60%).
**Regra nova:** gancho com até 8 palavras, em letra grande, no terço do meio. O verificador de roteiro
limita as palavras; o QA acusa quadro 0 fraco ou concentrado no topo.

### 3. A chamada final dobrou de tamanho

De 5,3 s (#2) para 9,5–9,7 s (#4, #5): **um quarto do vídeo é propaganda**. Quem sai antes do fim
derruba a duração média, que é o sinal que o algoritmo usa.
**Regra nova:** chamada falada em uma frase (≤ 15% do vídeo, ≈ 5 s). O resto da oferta fica na tela,
na descrição e na DM.

### 4. Pausas mortas entre as falas

1,0 a 1,3 s entre as falas do #5 (os `gaps` do `config.json` somados ao silêncio de cada fala). Numa fala
de 37 s, são ~4 s de silêncio.
**Regra nova:** no máximo 0,35 s entre falas. Os 35 s viram ~32 s sem cortar conteúdo.

### 5. Todos os vídeos têm a mesma cara

Mesmo fundo verde-escuro, mesmo layout e mesma voz. O próprio `ESTRATEGIA.md` aponta "formato
repetido" como causa provável do fracasso do #2. O #5 acertou ao trocar o cenário por **um objeto
que muda** (a conta).
**Regra nova:** a identidade (cores, fontes, logo, voz) fica; o objeto central muda a cada episódio
(conta, contrato, holerite, multa, linha do tempo).

### 6. A oferta mudava a cada vídeo

#1: "a Constituição é grátis, busca no Google". #4: "7 dias de Premium grátis, sem cartão". #5: "a lei
inteira grátis".
**Agora:** `oferta.json` é a fonte única. Na fala vai a parte sem atrito ("a lei inteira tá grátis");
o teste de 7 dias vai na tela e na descrição. O verificador bloqueia prazo diferente do atual.

### 7. O caminho até o site tem atrito demais

No Shorts, o link da descrição não é clicável no celular; no Instagram, "link na bio" exige 2 toques e
a bio só guarda o link do último vídeo.
**Agora:** `publicacao.py` gera a **palavra-chave de DM** ("comenta CONTA que eu te mando o link"):
o comentário conta para a distribuição e o link chega clicável. No YouTube, use o "Vídeo relacionado"
e o link do perfil. No Instagram, a bio aceita até 5 links: mantenha os 3 últimos episódios.

### 8. Nenhum gancho foi testado

Cada vídeo teve um começo só, e por isso não dá para saber se o tema ou o gancho falhou.
**Agora:** a ficha exige gancho A e B (`p1.txt` e `p1b.txt`). O B vai como *trial reel* do Instagram
(mostrado só a quem não segue).

### 9. Os resultados não são registrados

Só existem números do #1 e uma contagem do #2. Sem dados, a próxima decisão é palpite.
**Agora:** `resultados.csv` + `analisar_resultados.py`, preenchidos em 48 h e em 7 dias. O vidIQ está
conectado à sessão, mas **sem canal do YouTube autorizado**; autorizando, dá para puxar os números
direto do Studio.

### 10. A voz padrão não era a dos Shorts

`presets.json` tinha `v1` como padrão, mas todos os Shorts usam `v2 --natural --tentativas 6`.
Quem esquecesse as opções gerava a voz antiga.
**Agora:** o preset `shorts` (v2 + naturalidade + 6 tentativas + sem pós-produção) é o padrão.
A v1 continua congelada.

### 11. Segurança jurídica dependia de memória

As regras ("conferir no Planalto") existiam só em texto. O #3 cita a EC 141/2026 sem o texto literal
na documentação.
**Agora:** `checar_roteiro.py` bloqueia ficha sem link oficial, texto literal, quem conferiu e quando.
**Antes de reaproveitar o tema do #3, confira a EC 141/2026 no Planalto.**

## Sobre a distribuição 50/30/20

A proposta (50% pegadinhas, 30% técnicas, 20% demonstração) vai contra o que os dados mostraram: as
pegadinhas de prova tiveram o menor alcance (#2: 24 views), e o público de concurso é pequeno para o
algoritmo. A pauta inicial em `README.md` usa **2 de dia a dia + 1 pegadinha + 1 técnica ou
demonstração por semana**. É uma hipótese: reavalie depois de 4 semanas de `resultados.csv`.

## O que fica para a animação (juris-app, sem mudanças feitas aqui)

1. Algo se mexendo a cada 1–1,5 s nos primeiros 5 s (itens 1 e 2).
2. Manchete do gancho grande, no centro (item 2).
3. Chamada final de ≤ 5 s (item 3) e `gaps` ≤ 0,35 s (item 4).
4. Lente mais próxima nas telas do app: no #4 o texto das telas do app sai pequeno demais para ler no celular.
5. Render das duas variantes do gancho (item 8).
