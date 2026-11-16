# Short: "O Presidente pode ser preso?" (CF, art. 86)

1º Short do YouTube do Estuda Leges, narrado com a voz **v2** deste projeto (preset `v2`).

| Arquivo | O que é |
|---|---|
| `estuda-leges-short.mp4` | Vídeo final, 1080×1920, 30 fps, 44,6 s, voz + efeitos + trilha. |
| `estuda-leges-short-sem-trilha.mp4` | Voz + efeitos, para pôr uma música em alta no app do YouTube. |
| `estuda-leges-short-capa.png` | Capa (o carimbo "Nem em flagrante"). |
| `ESTRATEGIA.md` | Análise de público, roteiro, texto de publicação, métricas e próximos temas. |
| `narracao/pN.txt` | Falas, uma por cena. `narracao/roteiro.txt` tem o texto completo. |
| `narracao/pN.json` | Config usada e verificação do Whisper de cada fala. |
| `montar_audio.py` | Junta as falas (+8% de velocidade), mede as palavras, sintetiza efeitos e trilha e gera `timing.json`. |
| `timing.json` | Tempo de cada cena, evento e palavra da legenda. |

## Como foi gerada a narração

```bash
python gerar_clonada.py videos/short-presidente-art86/narracao/p1.txt p1.wav --preset v2 --sem_pos --tentativas 5
```

Três frases foram reescritas porque a voz errava nelas em todas as tentativas: "nem em flagrante" virou "nem mesmo se for flagrante"; "quóruns" virou "frações"; e "Estuda Leges" foi para o fim da frase.

## Imagem

A animação usa as telas reais do app e fica no repositório **juris-app**, branch `feat/short-youtube-art86`, em `video/shorts/` (composição, estúdio e `render.mjs`). O passo a passo do render está no `video/shorts/README.md` de lá.
