# Vozes de referência

Os clipes vêm do **Mozilla Common Voice 17, português do Brasil**. Os dados são de domínio público (CC0). Foram baixados do conjunto de teste `DynamicSuperb/PTBRSpeechRecognition_CommonVoice17-Test`. Depois foram limpos: tirei o silêncio, apliquei um filtro passa-alta, reduzi o ruído e normalizei o volume.

| Arquivo | F0 | Resultado nos testes |
|---|---|---|
| `cv_131.wav` | ~106 Hz | **Recomendada.** 0% de erro, fala fluida, entonação rica |
| `cv_191.wav` | ~101 Hz | Muito expressiva. Ficou um pouco lenta (acelere 10% com `atempo=1.1`) |
| `cv_87.wav` | ~105 Hz | Mais sóbria, com menos variação de tom |

O `.txt` de cada clipe é a transcrição do áudio (o F5-TTS precisa dela).
