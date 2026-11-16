# Versão v1 (aprovada em 16/11/2026)

Esta é a opção "01" que você escolheu: a voz clonada a partir de um narrador brasileiro do Common Voice (clipe CV-131).

- `amostra_v1.mp3`: o áudio original aprovado, para ouvir.
- `amostra_v1.flac`: o mesmo áudio em qualidade máxima, sem perdas, para editar.

## Medições

| Erro de fala | Pausas travadas | Entonação | Ritmo |
|---|---|---|---|
| 0% | 7,5/min | 4,3 semitons | 166 palavras/min |

## Regerar com outro roteiro

```bash
python gerar_clonada.py roteiro.txt narracao.wav --preset v1
```

O preset `v1` em `presets.json` está congelado. Ele inclui até o corte de silêncio antigo ("legado") que estava em uso quando a v1 foi gerada. Na tag do git `voz-v1` está o código exatamente como era nesse momento.
