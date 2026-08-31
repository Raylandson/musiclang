"""Parser LL(1) dirigido por tabela.

A gramática vive em PRODUCOES, como dado. Daí saem, calculados em tempo de
importação, FIRST, FOLLOW e a tabela M[A, a] — que é conferida célula a célula:
duas produções na mesma célula levantam GrammarError na hora do import, então
uma gramática com conflito nem chega a rodar.

O reconhecimento é o algoritmo clássico de pilha:

    topo é terminal      -> casa com o lookahead e avança
    topo é não-terminal  -> expande por M[topo, lookahead]
    célula vazia         -> ParserError

A AST é construída por símbolos de ação empilhados junto com o lado direito de
cada produção. Como a pilha é LIFO e o lado direito entra invertido, a ação é
empilhada primeiro e desempilhada por último — ou seja, depois que todos os
símbolos daquela produção já produziram seus valores.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from . import ast
from .errors import ParserError
from .lexer import Token, TokenType, tokenizar


class GrammarError(Exception):
    """A gramática não é LL(1). Só pode acontecer em tempo de importação."""


class NT(Enum):
    """Não-terminais."""

    PROGRAM = "<program>"
    MUSIC = "<music>"
    MUSIC_BODY = "<music_body>"
    MUSIC_ITEM = "<music_item>"
    TEMPO_DECL = "<tempo_decl>"
    KEY_DECL = "<key_decl>"
    MODE = "<mode>"
    OUTPUT_DECL = "<output_decl>"
    MELODY_BLOCK = "<melody_block>"
    EVENT_LIST = "<event_list>"
    EVENT = "<event>"
    VARIATION_BLOCK = "<variation_block>"
    TRANSFORM_LIST = "<transform_list>"
    TRANSFORM = "<transform>"
    SIGNED_NUMBER = "<signed_number>"
    SIGN_OPT = "<sign_opt>"


VAZIO = "ε"


@dataclass(frozen=True)
class Producao:
    numero: int
    lhs: NT
    rhs: tuple
    acao: Callable[[list], object]

    def __str__(self) -> str:
        direita = " ".join(
            s.value if isinstance(s, NT) else s.value for s in self.rhs
        )
        return f"{self.lhs.value} ::= {direita or VAZIO}"


def _pos(token: Token) -> tuple[int, int]:
    return token.linha, token.coluna


# --------------------------------------------------------------- a gramática

_ESPECIFICACAO = [
    # (lhs, rhs, ação)
    (NT.PROGRAM, (NT.MUSIC, TokenType.EOF), lambda v: v[0]),
    (
        NT.MUSIC,
        (TokenType.MUSIC, TokenType.STRING, TokenType.LBRACE, NT.MUSIC_BODY, TokenType.RBRACE),
        lambda v: ast.Music(v[1].valor, v[3], *_pos(v[0])),
    ),
    (NT.MUSIC_BODY, (NT.MUSIC_ITEM, NT.MUSIC_BODY), lambda v: [v[0], *v[1]]),
    (NT.MUSIC_BODY, (), lambda v: []),
    (NT.MUSIC_ITEM, (NT.TEMPO_DECL,), lambda v: v[0]),
    (NT.MUSIC_ITEM, (NT.KEY_DECL,), lambda v: v[0]),
    (NT.MUSIC_ITEM, (NT.MELODY_BLOCK,), lambda v: v[0]),
    (NT.MUSIC_ITEM, (NT.VARIATION_BLOCK,), lambda v: v[0]),
    (NT.MUSIC_ITEM, (NT.OUTPUT_DECL,), lambda v: v[0]),
    (
        NT.TEMPO_DECL,
        (TokenType.TEMPO, TokenType.NUMBER),
        lambda v: ast.Tempo(v[1].valor, *_pos(v[0])),
    ),
    (
        NT.KEY_DECL,
        (TokenType.KEY, TokenType.PITCH, NT.MODE),
        lambda v: ast.Key(v[1].valor[0], v[1].valor[1], v[2], *_pos(v[0])),
    ),
    (NT.MODE, (TokenType.MAJOR,), lambda v: "major"),
    (NT.MODE, (TokenType.MINOR,), lambda v: "minor"),
    (
        NT.OUTPUT_DECL,
        (TokenType.OUTPUT, TokenType.STRING),
        lambda v: ast.Output(v[1].valor, *_pos(v[0])),
    ),
    (
        NT.MELODY_BLOCK,
        (TokenType.MELODY, TokenType.LBRACE, NT.EVENT_LIST, TokenType.RBRACE),
        lambda v: ast.Melody(v[2], *_pos(v[0])),
    ),
    (NT.EVENT_LIST, (NT.EVENT, NT.EVENT_LIST), lambda v: [v[0], *v[1]]),
    (NT.EVENT_LIST, (), lambda v: []),
    (
        NT.EVENT,
        (TokenType.NOTE, TokenType.DURATION),
        lambda v: ast.Note(*v[0].valor, v[1].valor, *_pos(v[0])),
    ),
    (
        NT.EVENT,
        (TokenType.REST, TokenType.DURATION),
        lambda v: ast.Rest(v[1].valor, *_pos(v[0])),
    ),
    (
        NT.VARIATION_BLOCK,
        (TokenType.VARIATION, TokenType.LBRACE, NT.TRANSFORM_LIST, TokenType.RBRACE),
        lambda v: ast.Variation(v[2], *_pos(v[0])),
    ),
    (NT.TRANSFORM_LIST, (NT.TRANSFORM, NT.TRANSFORM_LIST), lambda v: [v[0], *v[1]]),
    (NT.TRANSFORM_LIST, (), lambda v: []),
    (
        NT.TRANSFORM,
        (TokenType.TRANSPOSE, NT.SIGNED_NUMBER),
        lambda v: ast.Transpose(v[1], *_pos(v[0])),
    ),
    (
        NT.TRANSFORM,
        (TokenType.OCTAVE, NT.SIGNED_NUMBER),
        lambda v: ast.OctaveShift(v[1], *_pos(v[0])),
    ),
    (
        NT.TRANSFORM,
        (TokenType.REPEAT, TokenType.NUMBER),
        lambda v: ast.Repeat(v[1].valor, *_pos(v[0])),
    ),
    (NT.TRANSFORM, (TokenType.REVERSE,), lambda v: ast.Reverse(*_pos(v[0]))),
    (NT.TRANSFORM, (TokenType.INVERT,), lambda v: ast.Invert(*_pos(v[0]))),
    (NT.SIGNED_NUMBER, (NT.SIGN_OPT, TokenType.NUMBER), lambda v: v[0] * v[1].valor),
    (NT.SIGN_OPT, (TokenType.PLUS,), lambda v: 1),
    (NT.SIGN_OPT, (TokenType.MINUS,), lambda v: -1),
    (NT.SIGN_OPT, (), lambda v: 1),
]

PRODUCOES = [
    Producao(i + 1, lhs, rhs, acao)
    for i, (lhs, rhs, acao) in enumerate(_ESPECIFICACAO)
]

INICIAL = NT.PROGRAM


# -------------------------------------------------------------- FIRST/FOLLOW


def _calcular_first() -> dict[NT, set]:
    first: dict[NT, set] = {nt: set() for nt in NT}
    mudou = True

    while mudou:
        mudou = False
        for p in PRODUCOES:
            antes = len(first[p.lhs])
            first[p.lhs] |= _first_da_sequencia(p.rhs, first)
            mudou = mudou or len(first[p.lhs]) != antes

    return first


def _first_da_sequencia(simbolos: tuple, first: dict[NT, set]) -> set:
    """FIRST de uma sequência; contém VAZIO se toda ela puder derivar ε."""
    resultado: set = set()

    for simbolo in simbolos:
        if isinstance(simbolo, TokenType):
            resultado.add(simbolo)
            return resultado

        resultado |= first[simbolo] - {VAZIO}
        if VAZIO not in first[simbolo]:
            return resultado

    resultado.add(VAZIO)
    return resultado


def _calcular_follow(first: dict[NT, set]) -> dict[NT, set]:
    follow: dict[NT, set] = {nt: set() for nt in NT}
    mudou = True

    while mudou:
        mudou = False
        for p in PRODUCOES:
            for i, simbolo in enumerate(p.rhs):
                if not isinstance(simbolo, NT):
                    continue

                antes = len(follow[simbolo])
                resto = _first_da_sequencia(p.rhs[i + 1 :], first)
                follow[simbolo] |= resto - {VAZIO}
                if VAZIO in resto:
                    follow[simbolo] |= follow[p.lhs]
                mudou = mudou or len(follow[simbolo]) != antes

    return follow


FIRST = _calcular_first()
FOLLOW = _calcular_follow(FIRST)


def _construir_tabela() -> dict[tuple[NT, TokenType], Producao]:
    tabela: dict[tuple[NT, TokenType], Producao] = {}

    for p in PRODUCOES:
        cabeca = _first_da_sequencia(p.rhs, FIRST)

        terminais = cabeca - {VAZIO}
        if VAZIO in cabeca:
            terminais = terminais | FOLLOW[p.lhs]

        for terminal in terminais:
            chave = (p.lhs, terminal)
            if chave in tabela:
                raise GrammarError(
                    f"Conflito LL(1) em M[{p.lhs.value}, {terminal.value}]: "
                    f"P{tabela[chave].numero} e P{p.numero}."
                )
            tabela[chave] = p

    return tabela


TABELA = _construir_tabela()


# -------------------------------------------------------------------- parser


@dataclass(frozen=True)
class _Reducao:
    """Marcador de ação: some da pilha construindo um nó da AST."""

    producao: Producao


class Parser:
    def __init__(self, tokens: list[Token], fonte: str | None = None) -> None:
        self.tokens = tokens
        self.fonte = fonte
        self.i = 0

    @property
    def atual(self) -> Token:
        return self.tokens[self.i]

    def analisar(self) -> ast.Music:
        pilha: list = [INICIAL]
        valores: list = []

        while pilha:
            topo = pilha.pop()

            if isinstance(topo, _Reducao):
                quantos = len(topo.producao.rhs)
                consumidos = valores[len(valores) - quantos :] if quantos else []
                del valores[len(valores) - quantos :]
                valores.append(topo.producao.acao(consumidos))

            elif isinstance(topo, TokenType):
                if self.atual.tipo is not topo:
                    raise self._erro([topo])
                valores.append(self.atual)
                self.i += 1

            else:
                producao = TABELA.get((topo, self.atual.tipo))
                if producao is None:
                    raise self._erro(self._esperados(topo))
                pilha.append(_Reducao(producao))
                pilha.extend(reversed(producao.rhs))

        return valores[0]

    def _esperados(self, nao_terminal: NT) -> list[TokenType]:
        return [t for (nt, t) in TABELA if nt is nao_terminal]

    def _erro(self, esperados: list[TokenType]) -> ParserError:
        nomes = sorted(t.value for t in esperados)
        lista = nomes[0] if len(nomes) == 1 else ", ".join(nomes)

        return ParserError(
            f"Esperado:    {lista}\nEncontrado:  {self.atual}",
            self.atual.linha,
            self.atual.coluna,
            self.fonte,
        )


def analisar(fonte: str) -> ast.Music:
    """Fonte -> AST. Levanta LexerError ou ParserError."""
    return Parser(tokenizar(fonte), fonte).analisar()
