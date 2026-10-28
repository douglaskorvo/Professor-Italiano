# Registro de resgate dos chats — Professor Italiano BOT

**Recuperação elaborada em 28/10/2026.** Este documento diferencia a **informação histórica identificada em conversas** da **implementação reconstruída**.

## Identidade, objetivo e data

- Conversa original de desenvolvimento: **6 de junho de 2025**.
- Última proposta de código encontrada no registro do chat: **18h58 de 06/06/2025**.
- Nome: **Professor Italiano BOT**; professor/personagem: **Prof. Vittorio Benedetti**.
- Personagem estabelecido pelo usuário: italiano, natural de **Florença**, **55 anos**, linguista, lecionou durante **25 anos** antes da personificação como IA.
- Temperamento: gentil e paciente; elogia antes de corrigir; humor leve, referências à cultura italiana, expressões *Buongiorno!*, *Ben fatto!*, *Andiamo avanti!*.
- Assinatura histórica: **— Prof. Vittorio 🇮🇹**.

## Arquitetura comprovada nas conversas

- Bot do **Telegram** em **Python**, executado no **Replit** por `long polling`.
- Conversação, explicação, correção de italiano e tradução usando a **API da OpenAI**.
- SDK OpenAI via `OpenAI`, `client.chat.completions.create`, com modelo `gpt-3.5-turbo`.
- Voz sintetizada via `client.audio.speech.create`, modelo `tts-1`, voz `alloy`.
- **FFmpeg** converte MP3 em **OGG/Opus** para mensagem de voz do Telegram.
- Solicitação de áudio por `/audio` ou gatilhos naturais como “áudio”, “voz”, “fala”, “leia”, emojis; conversas normais permanecem apenas em texto.
- Funções documentadas: `corrigir`, `tts_to_ogg`, `quer_audio`, `reply_handler`, `start`.
- Constantes documentadas: `AUDIO_TRIGGERS`, `TRIGGER_RE`.
- Inicialização registrada: `app.run_polling(drop_pending_updates=True)`.
- Segredos definidos como `TG_TOKEN` e `OPENAI_KEY`.

## Dependências documentadas

Versão **final proposta em chat**:

- `python-telegram-bot==20.7`
- `openai>=1.25.0,<2.0`
- `httpx==0.26.0`

**Observação:** em outra mensagem do mesmo dia, o usuário informou ter utilizado `python-telegram-bot==21.1` e `openai==1.25.1` num ambiente em que o TTS e o FFmpeg funcionaram. O arquivo `requirements.txt` deste pacote usa a lista da **última resposta registrada**, não uma prova do ambiente final publicado.

## Problemas e testes relatados em 06/06/2025

- Conflito entre múltiplos processos `getUpdates` do Telegram.
- `RateLimitError` relacionado à cota da API OpenAI.
- Falta de FFmpeg no ambiente, resolvida posteriormente, com funcionamento do TTS confirmado.

## Limites de confiabilidade

**Não se recuperou o arquivo original, nem um histórico Git, nem um ZIP da conta excluída.** Os detalhes acima derivam de registros recuperados da conversa, mas o texto integral de `main.py` não estava disponível em forma de arquivo. O `main.py` incluso é uma **reconstrução funcional informada pela conversa**, e não se deve descrevê-lo como idêntico à versão apagada.

**Escolhas novas de reconstrução (não verificadas nos chats):** memória temporária de 12 mensagens por conversa; uso de `asyncio.to_thread` para não bloquear o bot; `/audio` sem argumentos repete a última resposta; tratamento de erros e logging; variáveis opcionais para os modelos; testes de gatilhos. Esses componentes foram adicionados para viabilizar uma recuperação executável.

## Próxima etapa recomendada

Testar com novas credenciais de API e Telegram em ambiente isolado. Antes de depositar no Zenodo, verificar autoria, licença, versões e substituir credenciais antigas eventualmente comprometidas. O código está em condições de ser auditado, mas **não foi testado ao vivo contra Telegram/OpenAI** nesta recuperação.