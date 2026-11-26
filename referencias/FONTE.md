# Vozes de referência

Os clipes vêm do **Mozilla Common Voice 17, português do Brasil**. Os dados são de domínio público (CC0). Foram baixados do conjunto de teste `DynamicSuperb/PTBRSpeechRecognition_CommonVoice17-Test`. Depois foram limpos: tirei o silêncio, apliquei um filtro passa-alta, reduzi o ruído e normalizei o volume.

| Arquivo | F0 | Resultado nos testes |
|---|---|---|
| `cv_131.wav` | ~106 Hz | **Recomendada.** 0% de erro, fala fluida, entonação rica |
| `cv_191.wav` | ~101 Hz | Muito expressiva. Ficou um pouco lenta (acelere 10% com `atempo=1.1`) |
| `cv_87.wav` | ~105 Hz | Mais sóbria, com menos variação de tom |

O `.txt` de cada clipe é a transcrição do áudio (o F5-TTS precisa dela).

## Referência de narração (teste de 23/11/2026)

| Arquivo | Origem | Licença | Medidas |
|---|---|---|---|
| `mls_12428.wav` | Multilingual LibriSpeech (MLS), português, falante 12428, trecho `12428_13511_000001` (12,6 s). Gravação de audiolivro do LibriVox. | MLS: CC BY 4.0 (citar "Multilingual LibriSpeech, Pratap et al., 2020"); gravação LibriVox em domínio público. | Tom ~125 Hz, variação 5,2 semitons, 151 palavras/min; sem marcas de português europeu (`pesquisa_voz/sotaque_wav.py`). |

Escolhida porque é **narração** (entonação de contar algo), e não a leitura de uma frase solta como no
Common Voice. Para produção, o ideal é uma referência gravada com consentimento: a sua voz ou a de um
locutor contratado (20 a 30 s, no tom de um Short). Ver `pesquisa_voz/RESULTADOS.md`.
