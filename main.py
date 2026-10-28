"""Professor Italiano BOT — reconstrução informada pelos chats de 06/06/2025.

IMPORTANTE: este arquivo NÃO é uma extração byte a byte do código excluído.
Ele recompõe o comportamento e as interfaces documentados na conversa original.
"""
from __future__ import annotations

import asyncio
from io import BytesIO
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("professor_vittorio")

TG_TOKEN = os.environ.get("TG_TOKEN", "").strip()
OPENAI_KEY = os.environ.get("OPENAI_KEY", "").strip()
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-3.5-turbo")
TTS_MODEL = os.environ.get("OPENAI_TTS_MODEL", "tts-1")
TTS_VOICE = os.environ.get("OPENAI_TTS_VOICE", "alloy")

# Elementos do personagem e do ensino foram recuperados das mensagens de 06/06/2025.
SYSTEM_PROMPT = """Você é o Prof. Vittorio Benedetti, professor virtual de italiano.
É italiano, nasceu em Florença, tem 55 anos, é linguista e ensinou por 25 anos.
Você fala italiano e português com naturalidade. É gentil, paciente e encorajador;
elogia o esforço antes de corrigir, com humor leve e eventuais referências à
cultura italiana (arte, gastronomia e futebol).
Ajude a conversar em italiano, a traduzir e a corrigir frases. Quando houver erro,
explique com delicadeza e ofereça uma forma corrigida e mais natural. Seja breve:
prefira até dois pequenos blocos de resposta. Pode usar expressões como
'Buongiorno!', 'Ben fatto!' e 'Andiamo avanti!'.
Encerre suas respostas com a assinatura: — Prof. Vittorio 🇮🇹
"""

# Nomes e comportamento de detecção presentes nos registros da versão final.
AUDIO_TRIGGERS = ("áudio", "audio", "voz", "fala", "fale", "leia", "🔊", "🎤", "🎙", "🗣")
TRIGGER_RE = re.compile(r"\b(?:áudio|audio|voz|fala|fale|leia)\b|[🔊🎤🎙🗣]", re.IGNORECASE)
MAX_HISTORY_MESSAGES = 12  # Reconstrução: retenção apenas em memória, por conversa.


def quer_audio(texto: str) -> bool:
    """Detecta pedido explícito de áudio; mensagens comuns continuam em texto."""
    return bool(TRIGGER_RE.search(texto or ""))


def corrigir(mensagem: str, historico: list[dict[str, str]] | None = None) -> str:
    """Envia texto ao modelo de conversação para tutoria/correção em italiano."""
    if not OPENAI_KEY:
        raise RuntimeError("A credencial OPENAI_KEY não foi configurada.")
    cliente = OpenAI(api_key=OPENAI_KEY)
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensagens.extend(historico or [])
    mensagens.append({"role": "user", "content": mensagem})
    resposta = cliente.chat.completions.create(
        model=CHAT_MODEL,
        messages=mensagens,
        temperature=0.6,
        max_tokens=350,
    )
    texto = resposta.choices[0].message.content
    if not texto or not texto.strip():
        raise RuntimeError("A OpenAI retornou uma resposta vazia.")
    return texto.strip()


def tts_to_ogg(texto: str) -> bytes:
    """Converte fala da OpenAI (MP3) em OGG/Opus para áudio de voz no Telegram."""
    if not OPENAI_KEY:
        raise RuntimeError("A credencial OPENAI_KEY não foi configurada.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg não encontrado; instale-o no ambiente de execução.")
    cliente = OpenAI(api_key=OPENAI_KEY)
    with tempfile.TemporaryDirectory(prefix="vittorio_") as pasta:
        mp3 = Path(pasta) / "fala.mp3"
        ogg = Path(pasta) / "fala.ogg"
        audio = cliente.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=texto,
        )
        audio.stream_to_file(mp3)
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp3),
             "-c:a", "libopus", "-b:a", "48k", str(ogg)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return ogg.read_bytes()


async def _enviar_voz(update: Update, texto: str) -> None:
    dados = await asyncio.to_thread(tts_to_ogg, texto)
    arquivo = BytesIO(dados)
    arquivo.name = "vittorio.ogg"
    await update.effective_message.reply_voice(voice=arquivo)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Buongiorno! 🇮🇹 Sono il Professor Vittorio Benedetti. "
        "Podemos conversar em italiano, traduzir e corrigir suas frases. "
        "Respondo normalmente em texto; peça 'áudio', 'voz', 'fale' ou use /audio "
        "quando quiser ouvir minha resposta.\n\n— Prof. Vittorio 🇮🇹"
    )


async def comando_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lê a última resposta; se /audio vier com texto, responde à nova mensagem."""
    pedido = " ".join(context.args or []).strip()
    if pedido:
        await _responder(update, context, pedido, com_audio=True)
        return
    anterior = context.chat_data.get("ultima_resposta")
    if not anterior:
        await update.effective_message.reply_text(
            "Envie uma frase ou pergunta primeiro, ou use /audio seguido da mensagem."
        )
        return
    try:
        await _enviar_voz(update, anterior)
    except Exception:
        logger.exception("Falha ao gerar/enviar voz")
        await update.effective_message.reply_text(
            "Não consegui produzir o áudio agora. Verifique a configuração do TTS e do FFmpeg."
        )


async def _responder(update: Update, context: ContextTypes.DEFAULT_TYPE, mensagem: str,
                     com_audio: bool) -> None:
    historico = context.chat_data.get("historico", [])
    try:
        resposta = await asyncio.to_thread(corrigir, mensagem, list(historico))
    except Exception:
        logger.exception("Falha na conversação com a API")
        await update.effective_message.reply_text(
            "Não consegui responder neste momento. Confira a chave da API e sua cota de uso."
        )
        return

    await update.effective_message.reply_text(resposta)
    historico = (historico + [
        {"role": "user", "content": mensagem},
        {"role": "assistant", "content": resposta},
    ])[-MAX_HISTORY_MESSAGES:]
    context.chat_data["historico"] = historico
    context.chat_data["ultima_resposta"] = resposta

    if com_audio:
        try:
            await _enviar_voz(update, resposta)
        except Exception:
            logger.exception("Falha ao gerar/enviar voz")
            await update.effective_message.reply_text(
                "A resposta em texto foi enviada, mas o áudio não pôde ser gerado."
            )


async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = (update.effective_message.text or "").strip()
    if not texto:
        return
    await _responder(update, context, texto, com_audio=quer_audio(texto))


def main() -> None:
    if not TG_TOKEN:
        raise SystemExit("Defina o segredo TG_TOKEN (token do bot do Telegram).")
    if not OPENAI_KEY:
        raise SystemExit("Defina o segredo OPENAI_KEY (chave da API OpenAI).")
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", comando_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_handler))
    logger.info("Professor Italiano BOT iniciado (polling)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()