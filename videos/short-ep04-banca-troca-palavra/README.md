# Episódio #4: "A banca troca uma palavra" (CF, art. 66, § 1º)

Formato "situação real de uso": pegadinha do prazo do veto (15 dias úteis, a banca escreve 20), o trecho vira flashcard "Ocultar trecho" e é revisado. Narrado com a voz **v2**, acelerada em 10%.

Arquivos: vídeo com e sem trilha (38,6 s, 1080×1920), capa, `PUBLICACAO.md` (YouTube e Instagram, com UTM), falas com a verificação do Whisper, `config.json` e `timing.json`.

Duas frases foram reescritas: "Treine" saía "Traine" e "Premium" saía "prêmio". A chamada falada ficou "sete dias de acesso completo, grátis e sem cartão"; na tela, o selo diz "7 dias de Premium grátis · sem cartão".

A animação fica no **juris-app**, branch `feat/shorts-pegadinha-da-semana`, em `video/shorts/ep04/`.

## Versão corrigida (20/11/2026)

A 1ª versão tinha uma pausa de ~1,2 s no meio da fala 2, tom "quebrando" e aceleração de 10%. As falas foram regeradas com `gerar_clonada.py --natural` (pausa, entonação, tom e ritmo verificados), sem aceleração e com a fala 2 desacelerada para o ritmo das outras. Os arquivos desta pasta são a versão corrigida.
