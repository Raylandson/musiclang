"""Analisador léxico da MusicLang.

Percorre o fonte caractere a caractere, sem expressões regulares: o autômato é
construído à mão, como o projeto exige.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .errors import LexerError


class TokenType(Enum):
    # Palavras reservadas
    MUSIC = "MUSIC"
    TEMPO = "TEMPO"
    KEY = "KEY"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    MELODY = "MELODY"
    HARMONY = "HARMONY"
    REST = "REST"
    VARIATION = "VARIATION"
    TRANSPOSE = "TRANSPOSE"
    OCTAVE = "OCTAVE"
    REVERSE = "REVERSE"
    INVERT = "INVERT"
    REPEAT = "REPEAT"
    OUTPUT = "OUTPUT"

    # Símbolos
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    PLUS = "PLUS"
    MINUS = "MINUS"

    # Dados
    NUMBER = "NUMBER"
    STRING = "STRING"
    NOTE = "NOTE"
    PITCH = "PITCH"
    CHORD = "CHORD"
    DURATION = "DURATION"

    # Controle
    EOF = "EOF"


PALAVRAS_RESERVADAS = {
    "music": TokenType.MUSIC,
    "tempo": TokenType.TEMPO,
    "key": TokenType.KEY,
    "major": TokenType.MAJOR,
    "minor": TokenType.MINOR,
    "melody": TokenType.MELODY,
    "harmony": TokenType.HARMONY,
    "rest": TokenType.REST,
    "variation": TokenType.VARIATION,
    "transpose": TokenType.TRANSPOSE,
    "octave": TokenType.OCTAVE,
    "reverse": TokenType.REVERSE,
    "invert": TokenType.INVERT,
    "repeat": TokenType.REPEAT,
    "output": TokenType.OUTPUT,
}

SIMBOLOS = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
}

CLASSES_DE_ALTURA = "ABCDEFG"
ACIDENTES = "#b"
COMENTARIO = "#"

SUFIXOS_ACORDE = [
    "m7b5", "m7(b5)", "maj7", "dim7", "mMaj7", "min", "maj",
    "dim", "aug", "m7", "7M", "M7", "°7", "º7", "7", "m",
    "°", "º", "+"
]


@dataclass(frozen=True)
class Token:
    """Um token e sua posição no fonte.

    ``valor`` guarda o dado já interpretado, para o parser e a semântica não
    precisarem reabrir o lexema:

        NUMBER    -> int
        STRING    -> str (sem as aspas)
        NOTE      -> (classe, acidente, oitava)
        CHORD     -> (classe, acidente, qualidade)
        PITCH     -> (classe, acidente)
        DURATION  -> (numerador, denominador)
    """

    tipo: TokenType
    lexema: str
    linha: int
    coluna: int
    valor: Any = None

    def __str__(self) -> str:
        if self.valor is None:
            return self.tipo.value
        return f"{self.tipo.value}({self.lexema})"


class Lexer:
    def __init__(self, fonte: str) -> None:
        self.fonte = fonte
        self.pos = 0
        self.linha = 1
        self.coluna = 1

    # ------------------------------------------------------------------ API

    def tokens(self) -> list[Token]:
        """Varre o fonte inteiro. Levanta LexerError no primeiro problema."""
        resultado: list[Token] = []

        while True:
            self._descartar_irrelevantes()
            if self._fim():
                break
            resultado.append(self._proximo_token())

        resultado.append(Token(TokenType.EOF, "", self.linha, self.coluna))
        return resultado

    # -------------------------------------------------------- navegação

    def _fim(self) -> bool:
        return self.pos >= len(self.fonte)

    def _espiar(self, adiante: int = 0) -> str:
        i = self.pos + adiante
        return self.fonte[i] if i < len(self.fonte) else ""

    def _avancar(self) -> str:
        c = self.fonte[self.pos]
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _erro(self, mensagem: str, linha: int | None = None, coluna: int | None = None):
        return LexerError(
            mensagem,
            self.linha if linha is None else linha,
            self.coluna if coluna is None else coluna,
            self.fonte,
        )

    # ----------------------------------------------------- descarte

    def _descartar_irrelevantes(self) -> None:
        """Espaços, tabs, quebras de linha e comentários não geram token."""
        while not self._fim():
            c = self._espiar()
            if c in " \t\r\n":
                self._avancar()
            elif c == COMENTARIO:
                while not self._fim() and self._espiar() != "\n":
                    self._avancar()
            else:
                return

    # ---------------------------------------------------- reconhecimento

    def _proximo_token(self) -> Token:
        c = self._espiar()

        if c in SIMBOLOS:
            return self._simbolo()
        if c == '"':
            return self._string()
        if c.isdigit():
            return self._numero_ou_duracao()
        if c in CLASSES_DE_ALTURA:
            return self._nota_ou_acorde()
        if c.islower() or c == "_":
            return self._palavra_reservada()
        if c.isupper():
            raise self._erro(
                f"'{c}' não é uma classe de altura. As notas vão de A a G."
            )

        raise self._erro(f"Caractere inválido: '{c}'.")

    def _simbolo(self) -> Token:
        linha, coluna = self.linha, self.coluna
        c = self._avancar()
        return Token(SIMBOLOS[c], c, linha, coluna)

    def _string(self) -> Token:
        linha, coluna = self.linha, self.coluna
        self._avancar()  # aspas de abertura

        conteudo: list[str] = []
        while True:
            if self._fim() or self._espiar() == "\n":
                raise self._erro("String não fechada.", linha, coluna)
            if self._espiar() == '"':
                break
            conteudo.append(self._avancar())

        self._avancar()  # aspas de fechamento
        texto = "".join(conteudo)
        return Token(TokenType.STRING, f'"{texto}"', linha, coluna, texto)

    def _numero_ou_duracao(self) -> Token:
        linha, coluna = self.linha, self.coluna
        inteiro = self._digitos()

        # Um '/' seguido de dígito é o que separa 1/4 (duração) de 1 (número).
        if self._espiar() == "/" and self._espiar(1).isdigit():
            self._avancar()
            denominador = self._digitos()
            lexema = f"{inteiro}/{denominador}"
            valor = (int(inteiro), int(denominador))
            return Token(TokenType.DURATION, lexema, linha, coluna, valor)

        return Token(TokenType.NUMBER, inteiro, linha, coluna, int(inteiro))

    def _digitos(self) -> str:
        digitos: list[str] = []
        while not self._fim() and self._espiar().isdigit():
            digitos.append(self._avancar())
        return "".join(digitos)

    def _nota_ou_acorde(self) -> Token:
        linha, coluna = self.linha, self.coluna
        classe = self._avancar()

        acidente = ""
        if self._espiar() in ACIDENTES and self._espiar() != "":
            acidente = self._avancar()

        # Verifica se casa com sufixo de qualidade de acorde
        resto = self.fonte[self.pos :]
        for sufixo in SUFIXOS_ACORDE:
            if resto.startswith(sufixo):
                for _ in sufixo:
                    self._avancar()
                lexema = f"{classe}{acidente}{sufixo}"
                valor = (classe, acidente, sufixo)
                return Token(TokenType.CHORD, lexema, linha, coluna, valor)

        # Se houver dígitos de oitava, é NOTE (ex: C4, C99)
        if self._espiar().isdigit():
            oitava = self._digitos()
            lexema = f"{classe}{acidente}{oitava}"
            valor = (classe, acidente, int(oitava))
            return Token(TokenType.NOTE, lexema, linha, coluna, valor)

        # Sem sufixo e sem dígito, é CHORD com tríade maior padrão (ex: C, F#)
        lexema = f"{classe}{acidente}"
        return Token(TokenType.CHORD, lexema, linha, coluna, (classe, acidente, ""))

    def _palavra_reservada(self) -> Token:
        linha, coluna = self.linha, self.coluna

        letras: list[str] = []
        while not self._fim() and (self._espiar().isalnum() or self._espiar() == "_"):
            letras.append(self._avancar())
        palavra = "".join(letras)

        tipo = PALAVRAS_RESERVADAS.get(palavra)
        if tipo is None:
            # A linguagem não tem identificadores: o que não é reservado é erro.
            raise self._erro(
                f"'{palavra}' não é uma palavra reservada da MusicLang.", linha, coluna
            )

        return Token(tipo, palavra, linha, coluna)


def tokenizar(fonte: str) -> list[Token]:
    """Atalho para quem só quer a lista de tokens."""
    return Lexer(fonte).tokens()
