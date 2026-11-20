# Operação de produção dos Shorts e Reels

Uma linha de produção, não uma sequência de vídeos avulsos. Cada etapa tem um arquivo e um comando,
e nenhum vídeo avança sem passar pelo verificador da etapa anterior. O diagnóstico que originou esta
estrutura está em [`DIAGNOSTICO.md`](DIAGNOSTICO.md).

| Arquivo | Para quê |
|---|---|
| `oferta.json` | **Fonte única** da oferta, do domínio, dos links e das promessas proibidas. Mudou no site? Mude aqui primeiro. |
| `pronuncia.json` | Escritas que a voz erra (aprendidas nos episódios #1–#5). |
| `episodios/_modelo.json` | Ficha do episódio: problema, 2 ganchos, falas, cenas, chamada, fontes, link e publicação. |
| `episodios/ep05-exemplo.json` | O #5 refeito como ficha (bloqueado de propósito: fontes sem conferência). |
| `checar_roteiro.py` | Trava antes da voz: fonte oficial conferida, 2 ganchos, oferta atual, duração e pronúncia. |
| `qa_video.py` | Trava antes de publicar: formato, volume, quadro 0, tela parada, chamada longa, áreas cobertas. |
| `publicacao.py` | Gera o `PUBLICACAO.md` com todos os links rastreados (UTM) montados do mesmo jeito. |
| `resultados.csv` | Uma linha por vídeo, por plataforma, por variante (A/B). |
| `analisar_resultados.py` | Diz qual parte de cada vídeo falhou (gancho, miolo, conversa, alcance) e o que mudar. |

## As 7 etapas

### 1. Pauta (segunda-feira)

Quatro vídeos por semana. Distribuição inicial, a revisar depois de 4 semanas de dados:

| Formato | Por semana | Papel |
|---|---|---|
| `dia_a_dia`: direito que todo mundo vive (consumo, trabalho, aluguel, trânsito) | 2 | **Alcance.** É o que o algoritmo distribui. |
| `pegadinha`: a palavra que a banca troca | 1 | **Qualificação.** Fala com quem compra (concurseiro, OAB). |
| `tecnica` ou `demonstracao` (alternando) | 1 | **Conversão.** Mostra o Estuda Leges resolvendo um problema real de estudo. |

Regra de tema: **precisa ter procura ou notícia** (o que as pessoas já perguntam). "Cai em prova" é
argumento de venda, não de alcance. Prefira leis que o app tem completas, porque o link leva ao artigo.

### 2. Validação jurídica

Abra o dispositivo no Planalto (ou DOU, Câmara, Senado, tribunal), copie o texto literal para a ficha
e preencha `conferido_por` e `conferido_em`. Questão atribuída a banca exige banca, ano, cargo e link;
sem isso, `"origem": "adaptada"`. **Se houver dúvida de interpretação, pare e peça revisão humana.**

### 3. Roteiro (ficha)

```bash
cp producao/episodios/_modelo.json producao/episodios/ep06.json
```

```bash
python producao/checar_roteiro.py producao/episodios/ep06.json
```

Regras que o verificador cobra: 1ª frase do gancho em até ~2 s; texto do gancho inteiro no quadro 0
(até 8 palavras); vídeo entre 20 e 35 s; chamada final em até 15% do vídeo (≈ 5 s, uma frase);
números por extenso e sem siglas na fala.

### 4. Voz

Com a ficha aprovada, grave as falas (gancho A em `p1.txt`, gancho B em `p1b.txt`):

```bash
python producao/checar_roteiro.py producao/episodios/ep06.json --gerar-falas videos/short-ep06-tema/narracao
```

```bash
for f in videos/short-ep06-tema/narracao/p*.txt; do python gerar_clonada.py "$f" "${f%.txt}.wav"; done
```

O preset padrão agora é `shorts` (voz v2 + verificação de naturalidade + 6 tentativas). Confira os
avisos ⚠ e reescreva a frase que errar em todas as tentativas, anotando a troca em `pronuncia.json`.

### 5. Animação e render

A animação (cenas, telas reais do app e render) fica no juris-app, branch
`feat/shorts-pegadinha-da-semana`. Este repositório entrega as falas, a ficha e as regras.
Renderize **as duas variantes do gancho** (o resto do vídeo é igual).

### 6. Controle de qualidade

```bash
python producao/qa_video.py videos/short-ep06-tema --salvar
```

Nenhum ❌. Os ⚠️ que ficarem precisam de motivo (ex.: a contagem do quiz). Olhe também a
`qa-folha.jpg` (1 quadro por segundo) e assista **sem som**, no celular.

### 7. Publicação e análise

```bash
python producao/publicacao.py producao/episodios/ep06.json -o videos/short-ep06-tema/PUBLICACAO.md
```

Publique o gancho A no Shorts, Reels e TikTok, e o B como *trial reel* no Instagram. Em 48 h e em
7 dias, copie os números do YouTube Studio, do Instagram e do GA4 para `resultados.csv` e rode:

```bash
python producao/analisar_resultados.py
```

Na segunda seguinte, a pauta repete o que passou das metas e muda o que falhou.
