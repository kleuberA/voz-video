# Versões da voz

Nenhuma versão é apagada nem alterada. Refinamentos sempre viram uma versão nova.

| Versão | O que mudou | Erro | Pausas travadas/min | Entonação | Palavras/min |
|---|---|---|---|---|---|
| **v1** | Versão aprovada (opção 01) | 0% | 7,5 | 4,3 | 166 |
| v1.1 | v1 + corte corrigido (o "Se" inicial não é engolido) | 0% | 7,3 | 4,4 | 161 |
| v2 | + referência estendida do mesmo narrador (7,6 s) | 0%* | 6,5 | 5,3 | 162 |
| v2-suave | v2 com finalização mais leve (menos compressão e brilho) | 0%* | ≈ v2 | 5,2 | 162 |

\* O único aviso foi o Whisper escrever "Sível" no lugar de "Cível". A pronúncia está correta.

Para gerar qualquer versão com um roteiro novo:

```bash
python gerar_clonada.py roteiro.txt narracao.wav --preset v2
```
