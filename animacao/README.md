# Animação dos Shorts

O vídeo é uma página HTML em que **cada quadro é função pura do instante `t`** (`motor.js`): nenhuma
transição CSS, timer ou número aleatório. O Playwright desenha quadro a quadro, captura o palco
(432×768 px a 2,5× = 1080×1920) e o ffmpeg codifica. É o mesmo princípio do filme da landing, aqui sem
depender do juris-app.

O tempo vem da narração: os eventos do `config.json` do episódio estão ligados a palavras
("o carimbo bate em *vale*"), e o `montar_audio.py` grava no `timing.json` quando cada palavra é
dita. Antes da narração, `producao/tempo_provisorio.py` estima esses tempos pelo texto, e o vídeo sai
marcado **RASCUNHO**. Quando o `timing.json` de verdade existir, o mesmo render passa a usá-lo.

| Arquivo | Papel |
|---|---|
| `motor.js` | Curvas, molas, `rise`/`leave`/`pop`/`stamp`/`shake`, quadros-chave. |
| `pecas.js` | Fundo, selo da marca, legenda palavra por palavra, ícones e troca de cenas. |
| `base.css` | Identidade (verde-escuro, Instrument Serif, Newsreader, Geist, âmbar) e áreas seguras. |
| `pagina.html` | Carrega config, ficha, oferta e timing do episódio; ponte `window.__video.setFrame()`. |
| `episodios/<id>.js` | As cenas do episódio. Texto de lei só da ficha (`fontes[].texto_literal`). |
| `render.mjs` | Quadros de revisão, captura completa e MP4 final (com e sem trilha) + capa. |
| `fontes/`, `logo.png` | Fontes (OFL) e logo do Estuda Leges. |

## Fluxo

```bash
python producao/tempo_provisorio.py videos/short-ep06-black-friday
```

```bash
node animacao/render.mjs stills videos/short-ep06-black-friday A 0,2,8,15,21,27
```

Olhe os PNGs em `animacao/out/<id>/stills/`: texto cortado, sobreposição, legenda encostando em algo,
áreas cobertas (rodapé ~200 px, coluna direita ~60 px).

```bash
node animacao/render.mjs tudo videos/short-ep06-black-friday A
```

```bash
node animacao/render.mjs tudo videos/short-ep06-black-friday B
```

Saída na pasta do episódio: `estuda-leges-<id>[-B].mp4`, `-sem-trilha.mp4` e `-capa.png`
(rascunho: `-rascunho.mp4`, mudo e fora do git). Depois, `python producao/qa_video.py <pasta>`.

## Regras das cenas

- **Quadro 0 completo**: o gancho aparece inteiro desde o 1º quadro (`rise(t, 0)` não anima).
- **Nada parado no gancho**: algo muda a cada 1–1,5 s nos primeiros 5 s.
- **Um objeto que muda** (pedido, fatura, cupom), não texto sobre fundo vazio.
- **Fonte na tela**: o dispositivo citado aparece no kicker de cada trecho.
- **Dados de demonstração** (pedido, datas, valores) marcados "exemplo" na tela.
- Conteúdo entre 60 e 505 px de altura; a legenda fica em 520 px, acima do rodapé coberto.
