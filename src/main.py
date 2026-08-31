"""Interface de linha de comando.

Marco 3: léxico, sintático e semântico prontos — --tokens, --ast e --check
funcionam. A geração de MIDI entra no Marco 4.
"""

from __future__ import annotations

import argparse
import sys

from .ast import imprimir
from .errors import CompilerError
from .lexer import tokenizar
from .parser import analisar
from .semantic import verificar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="musiclang", description="Compilador da linguagem MusicLang."
    )
    parser.add_argument("arquivo", help="arquivo .music a compilar")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--tokens", action="store_true", help="imprime os tokens")
    grupo.add_argument("--ast", action="store_true", help="imprime a AST")
    grupo.add_argument("--check", action="store_true", help="valida sem gerar MIDI")
    args = parser.parse_args(argv)

    try:
        fonte = open(args.arquivo, encoding="utf-8").read()
    except OSError as erro:
        print(f"Não foi possível ler {args.arquivo}: {erro.strerror}", file=sys.stderr)
        return 2

    try:
        if args.tokens:
            for token in tokenizar(fonte):
                print(f"{token.linha:>4}:{token.coluna:<4} {token}")
            return 0

        arvore = analisar(fonte)

        if args.ast:
            print(imprimir(arvore))
            return 0

        analise = verificar(arvore, fonte)

        if args.check:
            _resumo(args.arquivo, analise)
            return 0
    except CompilerError as erro:
        print(erro, file=sys.stderr)
        return 1

    print("Apenas --tokens, --ast e --check estão disponíveis no Marco 3.", file=sys.stderr)
    return 2


def _resumo(caminho: str, analise) -> None:
    classe, acidente, modo = analise.tonalidade

    print("MusicLang Compiler")
    print()
    print(f"Source: {caminho}")
    print()
    print("[1/3] Lexical analysis........ OK")
    print("[2/3] Syntax analysis......... OK")
    print("[3/3] Semantic analysis....... OK")
    print()
    print(f"Music:      {analise.nome}")
    print(f"Tempo:      {analise.bpm} BPM")
    print(f"Key:        {classe}{acidente} {modo}")
    print(f"Notes:      {len(analise.melodia.eventos)}")
    print(f"Variations: {len(analise.variacoes)}")
    print(f"Output:     {analise.arquivo}")


if __name__ == "__main__":
    raise SystemExit(main())
