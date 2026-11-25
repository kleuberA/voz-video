# Voz padrão para Reels jurídicos (100% grátis e open-source)

> **Produção dos Shorts e Reels:** o passo a passo completo (pauta, validação jurídica, roteiro, voz,
> controle de qualidade, publicação e análise) está em [`producao/README.md`](producao/README.md). O
> diagnóstico dos episódios #1–#5 está em [`producao/DIAGNOSTICO.md`](producao/DIAGNOSTICO.md).
> **Voz padrão dos vídeos novos:** `gerar_qwen.py` (Qwen3-TTS) com a referência `referencias/cv_131_longa.wav`
> (voz "h" de `pesquisa_voz/RESULTADOS.md`). O `gerar_clonada.py` (Chatterbox, preset `shorts`) fica para os episódios antigos.
> `montar_audio.py` (trilha, efeitos e `timing.json` de cada episódio) também mora aqui agora.

## Instalação (uma vez só)

Você precisa de: Python 3.11 e 3.12, ffmpeg e [uv](https://docs.astral.sh/uv/).

```bash
uv venv -p 3.12 .venv && source .venv/bin/activate && uv pip install -r requirements-kokoro-piper.txt && deactivate
uv venv -p 3.11 .venv-cb && source .venv-cb/bin/activate && uv pip install -r requirements-clonada.txt && deactivate
```

As vozes do Piper ficam em `modelos/piper/`:

```bash
mkdir -p modelos/piper && cd modelos/piper
for ext in onnx onnx.json; do curl -L -o pt_BR-cadu-medium.$ext "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/cadu/medium/pt_BR-cadu-medium.$ext"; done
cd ../..
```

Os modelos do Kokoro, do Chatterbox e do Whisper são baixados sozinhos na primeira execução.

## Recomendado: voz clonada brasileira

```bash
source .venv-cb/bin/activate
python gerar_clonada.py meu_roteiro.txt narracao.wav referencias/cv_131.wav
```

Veja `referencias/FONTE.md` para conhecer as outras vozes.

## Uso diário

```bash
cd voz-juridica && source .venv/bin/activate
python voz.py meu_roteiro.txt narracao.wav      # padrão: Kokoro, voz pm_alex
```

A voz padrão fica em `config.json`. Para trocar de voz, edite o arquivo uma vez e todos os vídeos seguem o mesmo padrão.

## Modo voz clonada brasileira (mais natural)

```bash
source .venv-cb/bin/activate
python gerar_clonada.py meu_roteiro.txt narracao.wav referencias/cv_191.wav
```

- O timbre vem de uma gravação real de um brasileiro (Common Voice, CC0). Para usar a sua própria voz, grave de 6 a 10 s, salve em `referencias/minha_voz.wav` e passe esse arquivo no lugar.
- Cada parágrafo é gerado de uma vez só, o que deixa a fala corrida e sem travadas.
- O Whisper confere cada parágrafo e regera até 3 vezes se ouvir alguma palavra errada ou inventada. Se mesmo assim ficar algum erro, aparece um aviso ⚠ mostrando o que foi ouvido.
- Velocidade: cerca de 4 a 5 minutos de processamento por minuto de áudio em CPU.

O modo F5-TTS (`gerar_f5.py`, com o modelo pt-BR) tem licença **não comercial**. Não use em conteúdo monetizado.

## Como escrever o roteiro (faz muita diferença)

- **Uma linha em branco entre parágrafos** vira uma pausa de 650 ms. Use isso para separar as ideias.
- **Frases curtas** (até umas 20 palavras). Cada frase é gerada separadamente, então a entonação fica mais natural.
- **Números por extenso**: "artigo quarenta e nove", "vinte salários mínimos". Evite "art. 49" e "20 SM".
- **Siglas**: escreva do jeito que se fala ("Procon", "cê-dê-cê", "esse-tê-jota").
- Uma **pergunta no início** ganha uma pausa um pouco maior. Isso funciona bem como gancho.

## Base científica dos ajustes

| Ajuste | Valor | Por quê |
|---|---|---|
| Velocidade | ~155 palavras/min | A fala conversacional fica entre 150 e 170 ppm. Uma fala um pouco mais lenta e firme passa competência e dá tempo de absorver termos técnicos. |
| Voz masculina média-grave (F0 ≈ 135 Hz) | | Faixa típica da voz masculina: 85–180 Hz. Estudos de percepção (Klofstad et al., 2012; Tigue et al., 2012) mostram que vozes mais graves são vistas como mais confiáveis e competentes. |
| Variação de entonação | 3–4 semitons | Abaixo de ~2 semitons a fala soa monótona, "robótica". A fala humana expressiva fica por volta de 3–4. |
| Pausas | 320 ms entre frases / 650 ms entre parágrafos | Imitam os grupos respiratórios naturais. Sem pausa, a fala soa sintética. |
| EQ +2,5 dB em 3 kHz | | Na faixa de 2–4 kHz o ouvido é mais sensível (curvas isofônicas). É ali que estão as consoantes, então a voz fica mais clara no celular. |
| EQ +2 dB em 150 Hz, −1,5 dB em 350 Hz | | Dá corpo na região da F0 e tira o som "de caixa". |
| De-esser + compressão 3:1 | | Suaviza os "s" e deixa o volume constante. |
| −14 LUFS | | Nível de loudness que o Instagram/Reels usa. O áudio não sofre corte nem é abaixado. |
