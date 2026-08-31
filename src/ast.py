"""Nós da árvore sintática abstrata.

A AST representa conceitos da linguagem, não tokens: não há nó para chave, para
vírgula ou para palavra reservada. Todo nó guarda linha e coluna para que as
fases seguintes consigam apontar o ponto exato de um erro.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Music:
    nome: str
    itens: list = field(default_factory=list)
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Tempo:
    bpm: int
    linha: int
    coluna: int


@dataclass(frozen=True)
class Key:
    classe: str
    acidente: str
    modo: str
    linha: int
    coluna: int


@dataclass(frozen=True)
class Output:
    arquivo: str
    linha: int
    coluna: int


@dataclass(frozen=True)
class Melody:
    eventos: list
    linha: int
    coluna: int


@dataclass(frozen=True)
class Harmony:
    eventos: list
    linha: int
    coluna: int


@dataclass(frozen=True)
class Chord:
    cifra: str
    classe: str
    acidente: str
    qualidade: str
    duracao: tuple[int, int]
    linha: int
    coluna: int


@dataclass(frozen=True)
class Note:
    classe: str
    acidente: str
    oitava: int
    duracao: tuple[int, int]
    linha: int
    coluna: int


@dataclass(frozen=True)
class Rest:
    duracao: tuple[int, int]
    linha: int
    coluna: int


@dataclass(frozen=True)
class Variation:
    transformacoes: list
    linha: int
    coluna: int


@dataclass(frozen=True)
class Transpose:
    semitons: int
    linha: int
    coluna: int


@dataclass(frozen=True)
class OctaveShift:
    oitavas: int
    linha: int
    coluna: int


@dataclass(frozen=True)
class Repeat:
    vezes: int
    linha: int
    coluna: int


@dataclass(frozen=True)
class Reverse:
    linha: int
    coluna: int


@dataclass(frozen=True)
class Invert:
    linha: int
    coluna: int


# --------------------------------------------------------------- visualização


def _rotulo(no) -> str:
    """Como o nó aparece na árvore impressa por --ast."""
    if isinstance(no, Music):
        return f'Music(name="{no.nome}")'
    if isinstance(no, Tempo):
        return f"Tempo({no.bpm})"
    if isinstance(no, Key):
        return f"Key({no.classe}{no.acidente}, {no.modo})"
    if isinstance(no, Output):
        return f'Output("{no.arquivo}")'
    if isinstance(no, Melody):
        return "Melody"
    if isinstance(no, Harmony):
        return "Harmony"
    if isinstance(no, Chord):
        n, d = no.duracao
        return f"Chord({no.cifra}, {n}/{d})"
    if isinstance(no, Note):
        n, d = no.duracao
        return f"Note({no.classe}{no.acidente}{no.oitava}, {n}/{d})"
    if isinstance(no, Rest):
        n, d = no.duracao
        return f"Rest({n}/{d})"
    if isinstance(no, Variation):
        return "Variation"
    if isinstance(no, Transpose):
        return f"Transpose({no.semitons:+d})"
    if isinstance(no, OctaveShift):
        return f"OctaveShift({no.oitavas:+d})"
    if isinstance(no, Repeat):
        return f"Repeat({no.vezes})"
    if isinstance(no, Reverse):
        return "Reverse"
    if isinstance(no, Invert):
        return "Invert"
    return type(no).__name__


def _filhos(no) -> list:
    if isinstance(no, Music):
        return list(no.itens)
    if isinstance(no, Melody):
        return list(no.eventos)
    if isinstance(no, Harmony):
        return list(no.eventos)
    if isinstance(no, Variation):
        return list(no.transformacoes)
    return []


def desenhar(no, prefixo: str = "") -> list[str]:
    """Devolve a árvore em linhas, no formato do README §10."""
    linhas = [f"{prefixo}{_rotulo(no)}"] if not prefixo else [_rotulo(no)]
    filhos = _filhos(no)

    saida = [linhas[0]] if not prefixo else linhas
    for i, filho in enumerate(filhos):
        ultimo = i == len(filhos) - 1
        conector = "└── " if ultimo else "├── "
        continuacao = "    " if ultimo else "│   "

        sub = desenhar(filho)
        saida.append(prefixo + conector + sub[0])
        saida.extend(prefixo + continuacao + linha for linha in sub[1:])

    return saida


def imprimir(no) -> str:
    return "\n".join(desenhar(no))
