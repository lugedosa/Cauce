import unittest

from cauce import CauceError, check, run
from cauce.syntax import lex, parse


class SyntaxTests(unittest.TestCase):
    def test_token_positions_after_comment_and_unicode_text(self):
        tokens = lex('# comentario\ncell saludo = "¡Hola!";')
        self.assertEqual((tokens[0].kind, tokens[0].line, tokens[0].column), ("cell", 2, 1))
        self.assertEqual((tokens[1].text, tokens[1].column), ("saludo", 6))

    def test_precedence_and_left_associativity(self):
        self.assertEqual(run("emit 2 + 3 * 4; emit 20 - 5 - 2; emit (2 + 3) * 4;"), ["14", "13", "20"])

    def test_json_escapes(self):
        self.assertEqual(run(r'emit "uno\ndos\t\"tres\"";'), ['uno\ndos\t"tres"'])

    def test_missing_semicolon(self):
        with self.assertRaisesRegex(CauceError, "Se esperaba ';'"):
            parse("emit 1")

    def test_unknown_character(self):
        with self.assertRaisesRegex(CauceError, "1:6: Carácter inesperado"):
            lex("emit @;")

    def test_bad_escape(self):
        with self.assertRaisesRegex(CauceError, "Cadena inválida"):
            parse(r'emit "\q";')

    def test_unterminated_string(self):
        with self.assertRaises(CauceError):
            parse('emit "sin final;')


class LanguageTests(unittest.TestCase):
    def reject(self, source, message):
        with self.assertRaisesRegex(CauceError, message):
            check(source)

    def test_forward_references(self):
        source = "cell a = doble(b); cell b = 21; fn doble(x: Int) -> Int = x * 2; emit a;"
        self.assertEqual(run(source), ["42"])
        self.assertEqual(check(source).order, ["b", "a"])

    def test_diamond_graph_has_one_entry_per_cell(self):
        plan = check("cell z = a + b; cell a = x * 2; cell b = x + 1; cell x = 5; emit z;")
        self.assertEqual(plan.order, ["x", "a", "b", "z"])

    def test_cycle_even_in_dead_branch(self):
        self.reject("cell a = if false then b else 1; cell b = a;", "Ciclo de celdas")

    def test_self_cycle(self):
        self.reject("cell a = a;", "a -> a")

    def test_function_cycle(self):
        self.reject("fn a() -> Int = b(); fn b() -> Int = a();", "Ciclo de funciones")

    def test_bool_is_not_int(self):
        self.reject("emit 1 + true;", "Se esperaba Int; se obtuvo Bool")
        self.reject("emit 1 == true;", "Se esperaba Int; se obtuvo Bool")

    def test_bad_unused_function(self):
        self.reject('fn mal() -> Int = "texto"; emit 1;', "Se esperaba Int")

    def test_unused_cell_still_checked(self):
        self.reject("cell olvidada = desconocida; emit 1;", "desconocida")

    def test_function_cannot_capture_cells(self):
        self.reject("cell n = 7; fn f() -> Int = n; emit f();", "solo puede leer sus parámetros")

    def test_forward_function_call_and_local_parameters(self):
        self.assertEqual(run("fn a(x: Int) -> Int = b(x) + 1; fn b(y: Int) -> Int = y * 2; emit a(3);"), ["7"])

    def test_duplicate_and_reserved_names(self):
        self.reject("cell a = 1; cell a = 2;", "duplicado")
        self.reject("cell sum = 1;", "reservado")
        self.reject("cell f = 1; fn f() -> Int = 1;", "duplicado")

    def test_duplicate_and_shadowing_parameters(self):
        self.reject("fn f(x: Int, x: Int) -> Int = x;", "Parámetro duplicado")
        self.reject("fn f(sum: Int) -> Int = sum;", "ocultar")

    def test_wrong_argument_count_and_type(self):
        self.reject("fn f(n: Int) -> Int = n; emit f();", "espera 1 argumentos")
        self.reject('fn f(n: Int) -> Int = n; emit f("x");', "Se esperaba Int")
        self.reject("emit len(1, 2);", "espera un argumento")

    def test_unknown_call(self):
        self.reject("emit sistema(1);", "Función desconocida")

    def test_conditional_types(self):
        self.reject("emit if 1 then 2 else 3;", "Se esperaba Bool")
        self.reject('emit if true then 1 else "x";', "Se esperaba Int")

    def test_all_branches_checked(self):
        self.reject('emit if true then 1 else "x" + 2;', "Se esperaba Text")

    def test_short_circuit(self):
        self.assertEqual(run("emit false and (1 // 0 == 0); emit true or (1 // 0 == 0); emit if true then 7 else 1 // 0;"), ["false", "true", "7"])

    def test_nested_conditional(self):
        self.assertEqual(run("emit if false then 1 else if true then 2 else 3;"), ["2"])

    def test_comparison_and_not(self):
        self.assertEqual(run("emit not (2 < 1) and 3 >= 3; emit 2 != 3; emit 2 <= 1;"), ["true", "true", "false"])
        self.reject("emit 1 < 2 < 3;", "Se esperaba Bool; se obtuvo Int")

    def test_negative_floor_division_and_modulo(self):
        self.assertEqual(run("emit -7 // 3; emit -7 % 3; emit 7 // -3; emit 7 % -3;"), ["-3", "2", "-3", "-2"])

    def test_list_types_and_equality(self):
        self.assertEqual(run('cell xs: [[Int]] = [[], [1, 2]]; emit xs; emit [1, 2] == [1, 2];'), ["[[], [1, 2]]", "true"])
        self.reject("cell xs = [1, true];", "Se esperaba Int")

    def test_contextual_empty_lists(self):
        self.assertEqual(run("cell xs: [Int] = []; fn f(xs: [Int]) -> [Int] = xs; fn g() -> [Int] = []; emit sum([]); emit f([]); emit g();"), ["0", "[]", "[]"])
        self.assertEqual(run("emit if true then [1] else [];"), ["[1]"])
        self.reject("cell xs = [];", "lista vacía necesita")

    def test_builtins(self):
        self.assertEqual(run('emit len("a😀"); emit len([1,2]); emit sum(range(5)); emit text([true, false]);'), ["2", "2", "10", "[true, false]"])
        self.reject("emit sum([true]);", "Se esperaba Int")
        self.reject("emit len(2);", "len espera")

    def test_range_bounds(self):
        self.assertEqual(run("emit range(0); emit len(range(100000));"), ["[]", "100000"])
        for n in (-1, 100001):
            with self.subTest(n=n), self.assertRaisesRegex(CauceError, "range requiere"):
                run(f"emit range({n});")

    def test_literal_input_defaults(self):
        self.assertEqual(run('input a: Int = -2; input b: [Int] = [-1, 0]; input c: Text = "sí"; emit a; emit b; emit c;'), ["-2", "[-1, 0]", "sí"])
        self.reject("input x: Int = 1 + 2;", "debe ser literal")
        self.reject("input xs: [Int] = range(2);", "debe ser literal")

    def test_typed_input_overrides(self):
        source = "input n: Int = 2; input xs: [[Bool]] = []; emit n; emit xs;"
        self.assertEqual(run(source, {"n": 9, "xs": [[], [True]]}), ["9", "[[], [true]]"])
        for bad in (True, 2.0, "2", None):
            with self.subTest(value=bad), self.assertRaisesRegex(CauceError, "requiere Int"):
                run(source, {"n": bad})
        with self.assertRaisesRegex(CauceError, "requiere"):
            run(source, {"xs": [[1]]})

    def test_unknown_or_cell_override(self):
        for name in ("x", "otro"):
            with self.subTest(name=name), self.assertRaisesRegex(CauceError, "No existe la entrada"):
                run("cell x = 2;", {name: 1})

    def test_override_does_not_hide_invalid_default(self):
        with self.assertRaises(CauceError):
            run('input n: Int = "mal";', {"n": 1})

    def test_require_is_bool(self):
        self.reject('require 1, "fallo";', "Se esperaba Bool")

    def test_require_error_and_position(self):
        with self.assertRaisesRegex(CauceError, "2:1: Condición incumplida: límite"):
            run('emit 7;\nrequire false, "límite";')

    def test_check_does_not_execute(self):
        check('cell x = 1 // 0; require false, "no"; emit x;')
        with self.assertRaisesRegex(CauceError, "División entre cero"):
            run("emit 1 // 0;")

    def test_unused_cells_are_evaluated(self):
        with self.assertRaisesRegex(CauceError, "División entre cero"):
            run("cell sin_uso = 1 // 0; emit 1;")

    def test_output_formats_and_order(self):
        self.assertEqual(run('emit "hola"; emit true; emit 3; emit ["a", "b"];'), ["hola", "true", "3", '["a", "b"]'])

    def test_empty_program(self):
        self.assertEqual(run("# vacío"), [])


if __name__ == "__main__":
    unittest.main()
