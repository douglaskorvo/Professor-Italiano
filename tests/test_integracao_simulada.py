"""Integração simulada: nenhum token ou conexão de rede é necessário."""
import asyncio
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class Filtro:
    def __and__(self, other):
        return self

    def __invert__(self):
        return self


def carregar_bot():
    openai = types.ModuleType("openai")
    openai.OpenAI = Mock()
    telegram = types.ModuleType("telegram")
    telegram.Update = type("Update", (), {})
    ext = types.ModuleType("telegram.ext")
    ext.ApplicationBuilder = Mock()
    ext.CommandHandler = Mock(side_effect=lambda *a: ("command", a))
    ext.MessageHandler = Mock(side_effect=lambda *a: ("message", a))
    ext.ContextTypes = types.SimpleNamespace(DEFAULT_TYPE=object)
    ext.filters = types.SimpleNamespace(TEXT=Filtro(), COMMAND=Filtro())
    spec = importlib.util.spec_from_file_location("vittorio_teste", ROOT / "main.py")
    bot = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"openai": openai, "telegram": telegram, "telegram.ext": ext}):
        spec.loader.exec_module(bot)
    return bot


def objetos(texto=""):
    msg = types.SimpleNamespace(reply_text=AsyncMock(), reply_voice=AsyncMock(), text=texto)
    return types.SimpleNamespace(effective_message=msg), types.SimpleNamespace(chat_data={}, args=[])


class TesteBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = carregar_bot()

    def test_corrigir_com_historico(self):
        resposta = types.SimpleNamespace(choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content="  Ben fatto!  "))])
        criar = Mock(return_value=resposta)
        cliente = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=criar)))
        historico = [{"role": "user", "content": "Ciao"}]
        with patch.object(self.bot, "OPENAI_KEY", "ficticia"), patch.object(self.bot, "OpenAI", return_value=cliente):
            self.assertEqual(self.bot.corrigir("Come stai?", historico), "Ben fatto!")
        self.assertEqual(criar.call_args.kwargs["messages"][1:2], historico)

    def test_sem_chave(self):
        with patch.object(self.bot, "OPENAI_KEY", ""):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_KEY"):
                self.bot.corrigir("Ciao")

    def test_texto_e_memoria(self):
        update, ctx = objetos("Come stai?")
        with patch.object(self.bot, "corrigir", return_value="Sto bene!"), patch.object(
            self.bot, "_enviar_voz", new_callable=AsyncMock
        ) as fala:
            asyncio.run(self.bot.reply_handler(update, ctx))
        update.effective_message.reply_text.assert_awaited_once_with("Sto bene!")
        fala.assert_not_awaited()
        self.assertEqual(ctx.chat_data["ultima_resposta"], "Sto bene!")
        self.assertEqual(len(ctx.chat_data["historico"]), 2)

    def test_voz_sob_demanda(self):
        update, ctx = objetos("Fale em italiano")
        with patch.object(self.bot, "corrigir", return_value="Buongiorno!"), patch.object(
            self.bot, "_enviar_voz", new_callable=AsyncMock
        ) as fala:
            asyncio.run(self.bot.reply_handler(update, ctx))
        fala.assert_awaited_once_with(update, "Buongiorno!")

    def test_audio_ultima_resposta(self):
        update, ctx = objetos()
        ctx.chat_data["ultima_resposta"] = "Grazie!"
        with patch.object(self.bot, "_enviar_voz", new_callable=AsyncMock) as fala:
            asyncio.run(self.bot.comando_audio(update, ctx))
        fala.assert_awaited_once_with(update, "Grazie!")

    def test_audio_sem_historico(self):
        update, ctx = objetos()
        asyncio.run(self.bot.comando_audio(update, ctx))
        update.effective_message.reply_text.assert_awaited_once()

    def test_erro_api(self):
        update, ctx = objetos("Ciao")
        with patch.object(self.bot, "corrigir", side_effect=RuntimeError("teste")):
            asyncio.run(self.bot.reply_handler(update, ctx))
        self.assertIn("Não consegui responder", update.effective_message.reply_text.call_args.args[0])

    def test_start(self):
        update, ctx = objetos()
        asyncio.run(self.bot.start(update, ctx))
        self.assertIn("Vittorio Benedetti", update.effective_message.reply_text.call_args.args[0])

    def test_main_sem_credenciais(self):
        with patch.object(self.bot, "TG_TOKEN", ""), patch.object(self.bot, "OPENAI_KEY", ""):
            with self.assertRaises(SystemExit):
                self.bot.main()

    def test_configuracao_polling(self):
        app, builder = MagicMock(), MagicMock()
        builder.token.return_value.build.return_value = app
        with patch.object(self.bot, "TG_TOKEN", "teste"), patch.object(
            self.bot, "OPENAI_KEY", "teste"
        ), patch.object(self.bot, "ApplicationBuilder", return_value=builder):
            self.bot.main()
        self.assertEqual(app.add_handler.call_count, 3)
        app.run_polling.assert_called_once_with(drop_pending_updates=True)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg não instalado")
    def test_mp3_para_ogg_opus(self):
        with tempfile.TemporaryDirectory() as d:
            mp3 = Path(d) / "teste.mp3"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2",
                            str(mp3)], check=True, capture_output=True)

            class FalaFicticia:
                def stream_to_file(self, destino):
                    shutil.copyfile(mp3, destino)

            cliente = types.SimpleNamespace(audio=types.SimpleNamespace(
                speech=types.SimpleNamespace(create=Mock(return_value=FalaFicticia()))))
            with patch.object(self.bot, "OPENAI_KEY", "ficticia"), patch.object(
                self.bot, "OpenAI", return_value=cliente
            ):
                ogg = self.bot.tts_to_ogg("Buongiorno!")
            self.assertTrue(ogg.startswith(b"OggS"))
            self.assertIn(b"OpusHead", ogg)


if __name__ == "__main__":
    unittest.main()
