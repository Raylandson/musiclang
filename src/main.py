"""Interface de linha de comando.

Compila arquivos .music, valida léxico, sintaxe e semântica harmônica e gera
arquivos MIDI.
"""

from __future__ import annotations

import argparse
import sys

from .ast import imprimir
from .errors import CompilerError
from .lexer import tokenizar
from .music import gerar_midi
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
            _resumo(args.arquivo, analise, gerou_midi=False)
            return 0

        gerar_midi(analise)
        _resumo(args.arquivo, analise, gerou_midi=True)
        return 0
    except CompilerError as erro:
        print(erro, file=sys.stderr)
        return 1


def _resumo(caminho: str, analise, gerou_midi: bool = True) -> None:
    classe, acidente, modo = analise.tonalidade

    print("MusicLang Compiler")
    print()
    print(f"Source: {caminho}")
    print()
    print("[1/4] Lexical analysis........ OK")
    print("[2/4] Syntax analysis......... OK")
    print("[3/4] Semantic analysis....... OK")
    if gerou_midi:
        print("[4/4] MIDI generation......... OK")
    print()
    print(f"Music:      {analise.nome}")
    print(f"Tempo:      {analise.bpm} BPM")
    print(f"Key:        {classe}{acidente} {modo}")
    print(f"Notes:      {len(analise.melodia.eventos)}")
    if analise.harmonia is not None:
        print(f"Chords:     {len(analise.harmonia.eventos)}")
    print(f"Variations: {len(analise.variacoes)}")
    print(f"Output:     {analise.arquivo}")


if __name__ == "__main__":
    raise SystemExit(main())
