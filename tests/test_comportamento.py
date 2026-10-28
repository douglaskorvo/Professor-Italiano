"""Testes offline sem tokens nem APIs externas."""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
NODES = []
for node in TREE.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TRIGGER_RE" for t in node.targets):
        NODES.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name == "quer_audio":
        NODES.append(node)
SCOPE = {"re": re}
exec(compile(ast.fix_missing_locations(ast.Module(body=NODES, type_ignores=[])), "main.py", "exec"), SCOPE)


class TestAudio(unittest.TestCase):
    def test_audio_solicitado(self):
        for frase in ("mande áudio", "quero ouvir sua voz", "Fale em italiano", "leia isso", "🔊"):
            with self.subTest(frase=frase):
                self.assertTrue(SCOPE["quer_audio"](frase))

    def test_texto_comum_sem_audio(self):
        for frase in ("Buongiorno, come stai?", "Corrija questa frase", "Traduza grazie", ""):
            with self.subTest(frase=frase):
                self.assertFalse(SCOPE["quer_audio"](frase))


if __name__ == "__main__":
    unittest.main()
