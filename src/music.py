"""Modelo musical interno e gerador de arquivos MIDI.

Independente da sintaxe: converte alturas para números MIDI, durações para ticks
e gera o arquivo .mid final utilizando o pacote mido.
"""

from __future__ import annotations

import os
from typing import Optional

import mido

from . import ast
from .harmony import INTERVALOS_QUALIDADES, semitom_nota

# Resolução temporal: quantos ticks vale uma semínima.
PPQ = 480

# Semitom de cada classe de altura, contando de C = 0.
SEMITONS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
ALTERACAO = {"": 0, "#": 1, "b": -1}

MIDI_MIN = 0
MIDI_MAX = 127


def numero_midi(classe: str, acidente: str, oitava: int) -> int:
    """C4 -> 60, C#4 -> 61, A4 -> 69."""
    return 12 * (oitava + 1) + SEMITONS[classe] + ALTERACAO.get(acidente, 0)


def ticks(duracao: tuple[int, int]) -> int:
    """1/4 -> 480, 1/2 -> 960, 1/1 -> 1920."""
    numerador, denominador = duracao
    return PPQ * 4 * numerador // denominador


def nome_da_altura(midi: int) -> str:
    """Inverso de numero_midi, em sustenidos. Útil em mensagens e testes."""
    nomes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{nomes[midi % 12]}{midi // 12 - 1}"


def notas_do_acorde(
    classe: str, acidente: str, qualidade: str, oitava_base: int = 3
) -> list[int]:
    """Retorna os números MIDI das notas que formam o acorde."""
    fund_semitom = semitom_nota(classe, acidente)

    # Normalizar qualidade
    q = qualidade.strip()
    if q in ("M", "maj"):
        q = ""
    elif q == "min":
        q = "m"
    elif q in ("7M", "M7"):
        q = "maj7"
    elif q in ("º", "°"):
        q = "dim"
    elif q in ("º7", "°7"):
        q = "dim7"

    intervalos = INTERVALOS_QUALIDADES.get(q, (0, 4, 7))
    fund_midi = 12 * (oitava_base + 1) + fund_semitom
    return [fund_midi + offset for offset in intervalos]


def gerar_midi(analise, caminho_saida: Optional[str] = None) -> str:
    """Gera o arquivo MIDI a partir da estrutura Analise."""
    arquivo_saida = caminho_saida or analise.arquivo
    pasta = os.path.dirname(arquivo_saida)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    mid = mido.MidiFile(ticks_per_beat=PPQ)
    tempo_us = mido.bpm2tempo(analise.bpm)

    # Track 1: Melodia
    track_melodia = mido.MidiTrack()
    mid.tracks.append(track_melodia)
    track_melodia.append(
        mido.MetaMessage("track_name", name=f"{analise.nome} - Melody", time=0)
    )
    track_melodia.append(mido.MetaMessage("set_tempo", tempo=tempo_us, time=0))
    track_melodia.append(
        mido.Message("program_change", program=0, channel=0, time=0)
    )

    delta_acumulado = 0
    for evento in analise.melodia.eventos:
        dur_ticks = ticks(evento.duracao)
        if isinstance(evento, ast.Note):
            nota_midi = numero_midi(
                evento.classe, evento.acidente, evento.oitava
            )
            track_melodia.append(
                mido.Message(
                    "note_on",
                    note=nota_midi,
                    velocity=90,
                    channel=0,
                    time=delta_acumulado,
                )
            )
            track_melodia.append(
                mido.Message(
                    "note_off",
                    note=nota_midi,
                    velocity=0,
                    channel=0,
                    time=dur_ticks,
                )
            )
            delta_acumulado = 0
        elif isinstance(evento, ast.Rest):
            delta_acumulado += dur_ticks

    track_melodia.append(mido.MetaMessage("end_of_track", time=0))

    # Track 2: Harmonia (se presente)
    if analise.harmonia is not None:
        track_harmonia = mido.MidiTrack()
        mid.tracks.append(track_harmonia)
        track_harmonia.append(
            mido.MetaMessage("track_name", name=f"{analise.nome} - Harmony", time=0)
        )
        track_harmonia.append(
            mido.Message("program_change", program=0, channel=1, time=0)
        )

        delta_harm_acumulado = 0
        for evento in analise.harmonia.eventos:
            dur_ticks = ticks(evento.duracao)
            if isinstance(evento, ast.Chord):
                notas_midi = notas_do_acorde(
                    evento.classe, evento.acidente, evento.qualidade, oitava_base=3
                )
                for i, n in enumerate(notas_midi):
                    t = delta_harm_acumulado if i == 0 else 0
                    track_harmonia.append(
                        mido.Message(
                            "note_on", note=n, velocity=75, channel=1, time=t
                        )
                    )
                for i, n in enumerate(notas_midi):
                    t = dur_ticks if i == 0 else 0
                    track_harmonia.append(
                        mido.Message(
                            "note_off", note=n, velocity=0, channel=1, time=t
                        )
                    )
                delta_harm_acumulado = 0
            elif isinstance(evento, ast.Rest):
                delta_harm_acumulado += dur_ticks

        track_harmonia.append(mido.MetaMessage("end_of_track", time=0))

    mid.save(arquivo_saida)
    return arquivo_saida
