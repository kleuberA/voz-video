# Pesquisa de voz natural (23/11/2026)

**Pergunta:** por que a narração soa "robotizada" e qual combinação de motor e referência chega mais
perto de uma voz humana em português do Brasil?

## Motores considerados

Só os que permitem uso comercial (o Estuda Leges é um produto pago):

| Motor | Licença | pt-BR | Clonagem | Situação |
|---|---|---|---|---|
| Chatterbox Multilingual (atual) | MIT | sim (23 idiomas) | sim | testado |
| Chatterbox Multilingual V3 **pt-BR** (Resemble, ajuste dedicado) | MIT | sim | sim | testado |
| **Qwen3-TTS 12Hz 1.7B Base** (Alibaba) | Apache-2.0 | sim (10 idiomas) | sim (3 s+) | testado |
| Kokoro / Piper | Apache / MIT | sim | não | descartado: vozes fixas, prosódia plana |
| F5-TTS, XTTS-v2, Fish/OpenAudio, Phonon | não comerciais | — | — | descartados pela licença |
| Azure Speech (neural/HD) | pago | sim | não | indisponível nesta sessão (proxy bloqueia o host) |

## Como medimos

Mesmo texto para todos (`texto_teste.txt`, tom de Short), medido por `avaliar.py`:
- **Erro de palavra** (Whisper).
- **DNSMOS P.808** (Microsoft): nota 1–5 aprendida com avaliações humanas. Mede bem a qualidade do
  som, mas os preditores de MOS são pouco sensíveis a erros de prosódia (Takagi et al., 2026). O
  UTMOS22 foi descartado porque o checkpoint só carrega em modo inseguro do PyTorch.
- **Prosódia** comparada a fala humana medida do mesmo jeito: variação e faixa de tom (semitons),
  ritmo, pausas por frase e maior pausa. Alertas: monótona, quebrada, lenta/corrida, emendada, travada.
- **Sotaque** (`sotaque_wav.py`): marcas do português europeu × africadas brasileiras, para escolher
  referências (4 dos 5 narradores mais expressivos do MLS eram de Portugal).

## Resultado

| amostra | MOS | erro | tom (st) | faixa (st) | pal/min | pausas/frase | maior pausa | alertas |
|---|---|---|---|---|---|---|---|---|
| **i — Qwen3-TTS + referência de narração** | **4,18** | **0%** | 5,0 | 16,0 | 188 | 1,2 | 0,43 s | **nenhum** |
| e — Chatterbox pt-BR (exag. 0,6, cfg 0,4) | 4,00 | 2% | 4,0 | 13,1 | 167 | 0,8 | 0,40 s | nenhum |
| h — Qwen3-TTS + referência antiga (Common Voice) | 4,07 | 5% | 3,1 | 9,2 | 205 | 0,7 | 0,40 s | corrida |
| a — **voz atual** (multilíngue, uma geração por frase) | 4,03 | 2% | 4,8 | 16,9 | 193 | 1,7 | 1,06 s | travada |
| d — multilíngue, texto inteiro de uma vez | 4,07 | 0% | 4,2 | 17,3 | 208 | 0,2 | 0,34 s | corrida, emendada |
| f/g — Chatterbox pt-BR + referência de narração | 3,7–3,9 | 20–23% | 6,0–7,7 | 21–26 | 97–129 | 2,8 | 0,6–0,9 s | lenta, quebrada |
| b/c — Chatterbox pt-BR, cfg 0,5 / exag. 0,7 | 3,7–3,9 | 45–48% | — | — | 96–112 | — | 1,4–1,5 s | lenta, travada, erra palavras |
| *humano — narrador do MLS (referência nova)* | 3,85 | 4% | 5,2 | 17,5 | 159 | 4,0 | 0,45 s | nenhum |
| *humano — Common Voice (referência antiga)* | 3,70 | — | **1,9** | **5,4** | 134 | 0,5 | 0,32 s | **monótona**, lenta |

## Conclusões

1. **A referência é metade do problema.** A voz atual foi clonada de uma pessoa *lendo uma frase
   solta* (Common Voice): 1,9 semitons de variação e faixa de 5,4, que é fala monótona. Os modelos
   copiam o timbre e também o jeito de falar. O mesmo Qwen3-TTS sai plano e corrido com essa
   referência (h) e com prosódia de narrador com a referência de narração (i).
2. **Qwen3-TTS + referência de narração foi o melhor em tudo**: maior nota, 0% de erro e tom e faixa
   próximos do narrador humano (5,0/16,0 contra 5,2/17,5). Custo: ~2 min de CPU para ~17 s de fala
   (um Short de 35 s ≈ 4–5 min).
3. **O Chatterbox pt-BR é sensível demais à configuração**: com cfg 0,5 inventa ou pula palavras
   (45–48% de erro); com exagero 0,6/cfg 0,4 fica bom (e), mas abaixo do Qwen.
4. **Gerar frase por frase cria as travadas** (a: pausa de 1,06 s). Na produção, gerar o roteiro
   inteiro de uma vez e cortar as falas depois pelo alinhamento do Whisper.
5. **Os números não substituem o ouvido.** As amostras estão em `ouvir/` (fora do git).

## Recomendação

1. **Trocar o motor para Qwen3-TTS** (Apache-2.0) com geração contínua do roteiro.
2. **Trocar a referência.** A de narração do MLS (`referencias/mls_12428.wav`, CC BY 4.0) serviu
   para o teste. Para produção, o melhor é gravar **20–30 s de uma voz com consentimento** (a sua ou
   a de um locutor contratado), falando como num Short: frases curtas, perguntas e ênfase. Celular
   num quarto silencioso basta. Assim a voz é própria e não de um narrador anônimo de audiolivro.
3. Manter a verificação por Whisper e os alertas de prosódia em cada geração.
