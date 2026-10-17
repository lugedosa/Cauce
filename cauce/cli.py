"""Interfaz de terminal del MVP."""
import argparse
import json
from pathlib import Path
import sys

from .runtime import check, run
from .syntax import CauceError


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cauce", description="Cauce 0.1: calcular, validar y publicar")
    parser.add_argument("command", choices=("run", "check", "graph"))
    parser.add_argument("file", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="NOMBRE=JSON", help="Sustituye una entrada (solo run)")
    args = parser.parse_args(argv)
    try:
        if args.set and args.command != "run":
            raise CauceError("--set solo se admite con run")
        source = args.file.read_text(encoding="utf-8-sig")
        inputs = {}
        for item in args.set:
            name, separator, raw = item.partition("=")
            if not separator or not name:
                raise CauceError("Usa --set NOMBRE=JSON")
            if name in inputs:
                raise CauceError(f"Entrada repetida: {name}")
            try:
                inputs[name] = json.loads(raw)
            except ValueError:
                raise CauceError(f"JSON inválido para {name}") from None
        if args.command == "run":
            output = run(source, inputs)
            if output:
                sys.stdout.write("\n".join(output) + "\n")
        else:
            plan = check(source)
            if args.command == "check":
                print("Programa válido.")
            else:
                for name in plan.order:
                    print(f"{name}: {plan.types[name]}")
        return 0
    except (CauceError, OSError, UnicodeError, RecursionError, MemoryError) as error:
        print(f"{args.file}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
