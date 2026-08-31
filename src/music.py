"""Modelo musical interno.

Independente da sintaxe: aqui não existe token nem nó de AST, só altura em
número MIDI e duração em ticks.

Marco 3 usa apenas as conversões — as estruturas Song/Note entram no Marco 4.
"""

from __future__ import annotations

# Resolução temporal: quantos ticks vale uma semínima.
PPQ = 480

# Semitom de cada classe de altura, contando de C = 0.
SEMITONS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

ALTERACAO = {"": 0, "#": 1, "b": -1}

MIDI_MIN = 0
MIDI_MAX = 127


def numero_midi(classe: str, acidente: str, oitava: int) -> int:
    """C4 -> 60, C#4 -> 61, A4 -> 69."""
    return 12 * (oitava + 1) + SEMITONS[classe] + ALTERACAO[acidente]


def ticks(duracao: tuple[int, int]) -> int:
    """1/4 -> 480, 1/2 -> 960, 1/1 -> 1920."""
    numerador, denominador = duracao
    return PPQ * 4 * numerador // denominador


def nome_da_altura(midi: int) -> str:
    """Inverso de numero_midi, em sustenidos. Útil em mensagens e testes."""
    nomes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{nomes[midi % 12]}{midi // 12 - 1}"
