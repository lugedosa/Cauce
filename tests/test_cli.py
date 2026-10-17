from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def invoke(self, command, source, *extra):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "programa.cau"
            path.write_text(source, encoding="utf-8")
            return subprocess.run([sys.executable, "-m", "cauce", command, str(path), *extra],
                                  cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                                  env=self.utf8_env(), timeout=10)

    @staticmethod
    def utf8_env():
        import os
        return {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONINTMAXSTRDIGITS": "4300"}

    def test_success(self):
        result = self.invoke("run", 'input n: Int = 4; emit "sí"; emit n;', "--set", "n=8")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "sí\n8\n", ""))

    def test_no_partial_output_on_validation_failure(self):
        result = self.invoke("run", 'emit "primero"; require false, "bloqueado"; emit "último";')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("bloqueado", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_no_partial_output_on_late_emit_error(self):
        result = self.invoke("run", 'emit "primero"; emit 1 // 0;')
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("División entre cero", result.stderr)

    def test_type_error_stops_all_output(self):
        result = self.invoke("run", 'emit "primero"; emit 2 + true;')
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("Bool", result.stderr)

    def test_large_integer_formatting_failure_has_no_traceback_or_output(self):
        # Each literal is valid, but their product exceeds Python's default
        # decimal conversion limit. The language must still fail atomically.
        huge = "9" * 3000
        result = self.invoke("run", f'emit "primero"; emit {huge} * {huge};')
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("límites del anfitrión", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_does_not_run(self):
        result = self.invoke("check", "emit 1 // 0;")
        self.assertEqual((result.returncode, result.stdout), (0, "Programa válido.\n"))

    def test_graph_order(self):
        result = self.invoke("graph", "cell a = b + 1; cell b = 2;")
        self.assertEqual(result.stdout, "b: Int\na: Int\n")

    def test_bad_set_json_and_syntax(self):
        for setting in ("n=oops", "n", "=1"):
            with self.subTest(setting=setting):
                result = self.invoke("run", "input n: Int = 0;", "--set", setting)
                self.assertEqual((result.returncode, result.stdout), (1, ""))
                self.assertNotIn("Traceback", result.stderr)

    def test_duplicate_override(self):
        result = self.invoke("run", "input n: Int = 0;", "--set", "n=1", "--set", "n=2")
        self.assertEqual(result.returncode, 1)
        self.assertIn("repetida", result.stderr)

    def test_set_rejected_for_check_and_graph(self):
        for command in ("check", "graph"):
            with self.subTest(command=command):
                result = self.invoke(command, "input n: Int = 0;", "--set", "n=1")
                self.assertEqual(result.returncode, 1)

    def test_examples(self):
        expected = {
            "presupuesto.cau": "Total: 1000\nEnvío: 0\n",
            "series.cau": "[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]\n45\n4\n",
            "funciones.cau": "Hola, Luis\n100\n0\n",
        }
        for name, output in expected.items():
            with self.subTest(example=name):
                result = self.invoke("run", (ROOT / "examples" / name).read_text(encoding="utf-8"))
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, output, ""))
        for path in (ROOT / "examples" / "errors").glob("*.cau"):
            with self.subTest(example=path.name):
                result = self.invoke("run", path.read_text(encoding="utf-8"))
                self.assertEqual((result.returncode, result.stdout), (1, ""))


if __name__ == "__main__":
    unittest.main()
