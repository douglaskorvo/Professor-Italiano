# Professor Italiano BOT — Prof. Vittorio Benedetti 🇮🇹

> **Reconstrução informada pelas conversas de 6 de junho de 2025**, feita em 28/10/2026, após exclusão do projeto original no Replit. **Não é uma extração integral do código excluído.** Consulte `RECUPERACAO_DOS_CHATS.md` para identificar com precisão a origem de cada parte.

Professor virtual de italiano no Telegram, com conversação e correção de frases via OpenAI. Respostas são **textuais por padrão**; pedidos explícitos de áudio em linguagem natural ou por `/audio` acionam síntese de voz TTS, convertida a OGG/Opus para o Telegram.

## Conteúdo

- `main.py`: reconstrução do bot.
- `requirements.txt`: dependências registradas na última proposta do chat original.
- `.env.example`: nomes das credenciais; **não contém senhas reais**.
- `replit.nix`: dependência FFmpeg para ambientes Replit que suportam Nix.
- `tests/`: testes unitários de lógica sem uso de API.
- `RECUPERACAO_DOS_CHATS.md`: relatório de proveniência e limites.
- `RELATORIO_DE_TESTES.md`: registro dos testes executados e suas limitações.
- `.github/workflows/testes.yml`: testes automáticos offline no GitHub Actions.

## Configuração

1. Use **Python 3.11** para reproduzir o ambiente da época com menor risco de incompatibilidade.
2. Instale as dependências de `requirements.txt` no ambiente Python.
3. Instale **FFmpeg** no sistema e confira que o executável está disponível.
4. Configure os **Secrets** `TG_TOKEN` (BotFather/Telegram) e `OPENAI_KEY` (OpenAI). Nunca grave os valores reais nos arquivos.
5. Inicie `main.py` como processo único. **Não execute duas instâncias do mesmo bot em polling**, pois isso provocou conflito `getUpdates` no projeto original.
6. No Telegram, envie `/start`, faça uma pergunta em italiano e experimente `/audio` para escutar a última resposta.

A conta OpenAI deve ter acesso ao modelo escolhido e crédito/cota suficiente. Os modelos históricos registrados eram `gpt-3.5-turbo` e `tts-1`. Se estiverem indisponíveis, os nomes podem ser ajustados pelos Secrets `OPENAI_CHAT_MODEL` e `OPENAI_TTS_MODEL`. Não foi verificada a disponibilidade atual desses modelos.

## Comportamento de áudio

- Texto normal → resposta em texto.
- Mensagem que contenha pedido explícito de áudio/voz/fala/leitura → resposta em texto **e** mensagem de voz.
- `/audio` sem argumento → reproduz a última resposta em voz (escolha feita nesta reconstrução).
- `/audio <pergunta>` → responde à pergunta em texto e voz (escolha feita nesta reconstrução).

## Verificação local

A suíte `tests/` contém **13 testes** (todos aprovados em 28/10/2026), incluindo fluxo com dependências simuladas, comandos, tratamento de erros e conversão real de MP3 sintético para OGG/Opus com FFmpeg. Execute `python -m unittest discover -s tests -v`. Não houve chamadas à OpenAI nem ao Telegram; **é necessário um teste integrado com credenciais válidas** antes de declarar o bot funcional em produção. Consulte `RELATORIO_DE_TESTES.md`.

## Zenodo

Para depositar, use o arquivo ZIP, informe claramente que é uma **versão reconstruída com base no histórico de conversas**, a data da reconstrução e o caráter de protótipo. Confirme a licença que deseja aplicar e os dados de autoria antes do depósito. Não inclua segredos em código, anexos ou capturas de tela.

## Publicação pública no GitHub

Nome sugerido: `professor-italiano-vittorio`. Este pacote contém apenas código e documentação. Não inclui `.env` real, tokens, credenciais ou áudios pessoais. O workflow de testes será acionado após o envio dos arquivos.

**Licença:** ainda não definida pelo titular dos direitos. Repositório público não implica automaticamente uma licença open source. Se desejar permitir redistribuição/reutilização por terceiros, escolha e inclua uma licença adequada.