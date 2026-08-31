"""Módulo de teoria musical e harmonia funcional.

Implementa:
1. Mapeamento de notas e escalas (maior e menor).
2. Campo harmônico diatônico (tríades e tétrades) e cálculo de graus romanos.
3. Reconhecimento de Dominantes Secundários (V/X).
4. Gramática funcional estrita clássica (T -> S -> D -> T) e detecção de erros
   (retrogradação harmônica, dominantes secundárias não resolvidas e resolução final).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FuncaoHarmonica(Enum):
    TONICA = "Tônica"
    SUBDOMINANTE = "Subdominante"
    DOMINANTE = "Dominante"
    DOMINANTE_SECUNDARIA = "Dominante Secundária"


SEMITONS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOMES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ALTERACOES = {"": 0, "#": 1, "b": -1, "##": 2, "bb": -2}

# Intervalos em semitons para qualidades de acordes
INTERVALOS_QUALIDADES: dict[str, tuple[int, ...]] = {
    # Tríades
    "": (0, 4, 7),
    "maj": (0, 4, 7),
    "m": (0, 3, 7),
    "min": (0, 3, 7),
    "dim": (0, 3, 6),
    "°": (0, 3, 6),
    "º": (0, 3, 6),
    "aug": (0, 4, 8),
    "+": (0, 4, 8),
    # Tétrades
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "7M": (0, 4, 7, 11),
    "M7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "m7b5": (0, 3, 6, 10),
    "m7(b5)": (0, 3, 6, 10),
    "ø": (0, 3, 6, 10),
    "dim7": (0, 3, 6, 9),
    "°7": (0, 3, 6, 9),
    "º7": (0, 3, 6, 9),
    "mMaj7": (0, 3, 7, 11),
}

# Fórmulas de escalas em semitons a partir da tônica
ESCALA_MAIOR = [0, 2, 4, 5, 7, 9, 11]
ESCALA_MENOR_NATURAL = [0, 2, 3, 5, 7, 8, 10]
ESCALA_MENOR_HARMONICA = [0, 2, 3, 5, 7, 8, 11]

# Graus diatônicos em algarismos romanos
GRAUS_MAIOR = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
GRAUS_MENOR = ["i", "ii°", "III", "iv", "V", "VI", "vii°"]


def semitom_nota(classe: str, acidente: str) -> int:
    return (SEMITONS[classe] + ALTERACOES.get(acidente, 0)) % 12


@dataclass(frozen=True)
class InfoGrau:
    cifra: str
    fundamental_semitom: int
    grau_romano: str
    grau_numero: int  # 1 a 7
    funcao: FuncaoHarmonica
    eh_secundario: bool = False
    alvo_grau_numero: Optional[int] = None
    alvo_nome: Optional[str] = None


class TeoriaHarmonica:
    """Motor de análise e classificação funcional de acordes."""

    def __init__(self, fundamental_tom: str, acidente_tom: str, modo: str) -> None:
        self.tom_fundamental = fundamental_tom
        self.tom_acidente = acidente_tom
        self.modo = modo.lower()  # "major" ou "minor"
        self.tonica_semitom = semitom_nota(fundamental_tom, acidente_tom)

        if self.modo == "major":
            self.graus_semitons = [
                (self.tonica_semitom + s) % 12 for s in ESCALA_MAIOR
            ]
        else:
            self.graus_semitons = [
                (self.tonica_semitom + s) % 12 for s in ESCALA_MENOR_NATURAL
            ]

    def analisar_acorde(self, fundamental: str, acidente: str, qualidade: str) -> Optional[InfoGrau]:
        """Identifica o acorde como diatônico ou dominante secundária. Devolve None se for estranho."""
        cifra = f"{fundamental}{acidente}{qualidade}"
        semitom_fund = semitom_nota(fundamental, acidente)
        qualidade_padrao = self._normalizar_qualidade(qualidade)
        intervalos = INTERVALOS_QUALIDADES.get(qualidade_padrao)

        if intervalos is None:
            return None

        # 1. Tentar casar com acorde diatônico da tonalidade
        diatonico = self._identificar_diatonico(cifra, semitom_fund, qualidade_padrao)
        if diatonico is not None:
            return diatonico

        # 2. Tentar casar com Dominante Secundária (V ou V7 de algum grau diatônico válido)
        secundario = self._identificar_dominante_secundaria(cifra, semitom_fund, qualidade_padrao)
        if secundario is not None:
            return secundario

        return None

    def _normalizar_qualidade(self, qualidade: str) -> str:
        q = qualidade.strip()
        if q in ("M", "maj"):
            return ""
        if q == "min":
            return "m"
        if q in ("7M", "M7"):
            return "maj7"
        if q in ("º", "°"):
            return "dim"
        if q in ("º7", "°7"):
            return "dim7"
        return q

    def _identificar_diatonico(self, cifra: str, semitom_fund: int, qualidade: str) -> Optional[InfoGrau]:
        if semitom_fund not in self.graus_semitons:
            # Em modo menor, a sensível da harmônica (grau 7 elevado) pode ser a fundamental do vii°
            if self.modo == "minor":
                sensivel_harmonica = (self.tonica_semitom + 11) % 12
                if semitom_fund == sensivel_harmonica and qualidade in ("dim", "dim7", "m7b5"):
                    return InfoGrau(
                        cifra=cifra,
                        fundamental_semitom=semitom_fund,
                        grau_romano="vii°",
                        grau_numero=7,
                        funcao=FuncaoHarmonica.DOMINANTE,
                    )
            return None

        grau_idx = self.graus_semitons.index(semitom_fund)  # 0 a 6
        grau_num = grau_idx + 1

        if self.modo == "major":
            grau_romano = GRAUS_MAIOR[grau_idx]
            match grau_num:
                case 1:  # I - Maior / maj7
                    if qualidade in ("", "maj7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 1, FuncaoHarmonica.TONICA)
                case 2:  # ii - Menor / m7
                    if qualidade in ("m", "m7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 2, FuncaoHarmonica.SUBDOMINANTE)
                case 3:  # iii - Menor / m7
                    if qualidade in ("m", "m7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 3, FuncaoHarmonica.TONICA)
                case 4:  # IV - Maior / maj7
                    if qualidade in ("", "maj7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 4, FuncaoHarmonica.SUBDOMINANTE)
                case 5:  # V - Maior / 7
                    if qualidade in ("", "7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 5, FuncaoHarmonica.DOMINANTE)
                case 6:  # vi - Menor / m7
                    if qualidade in ("m", "m7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 6, FuncaoHarmonica.TONICA)
                case 7:  # vii° - Diminuto / m7b5
                    if qualidade in ("dim", "m7b5", "dim7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 7, FuncaoHarmonica.DOMINANTE)
        else:
            # Modo Menor
            grau_romano = GRAUS_MENOR[grau_idx]
            match grau_num:
                case 1:  # i - Menor / m7 / mMaj7
                    if qualidade in ("m", "m7", "mMaj7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 1, FuncaoHarmonica.TONICA)
                case 2:  # ii° - Diminuto / m7b5
                    if qualidade in ("dim", "m7b5"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 2, FuncaoHarmonica.SUBDOMINANTE)
                case 3:  # III - Maior / maj7
                    if qualidade in ("", "maj7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 3, FuncaoHarmonica.TONICA)
                case 4:  # iv - Menor / m7
                    if qualidade in ("m", "m7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 4, FuncaoHarmonica.SUBDOMINANTE)
                case 5:  # V (harmônica) ou v (natural)
                    if qualidade in ("", "7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 5, FuncaoHarmonica.DOMINANTE)
                    if qualidade in ("m", "m7"):
                        return InfoGrau(cifra, semitom_fund, "v", 5, FuncaoHarmonica.DOMINANTE)
                case 6:  # VI - Maior / maj7
                    if qualidade in ("", "maj7"):
                        return InfoGrau(cifra, semitom_fund, grau_romano, 6, FuncaoHarmonica.TONICA)
                case 7:  # VII (natural)
                    if qualidade in ("", "7"):
                        return InfoGrau(cifra, semitom_fund, "VII", 7, FuncaoHarmonica.DOMINANTE)

        return None

    def _identificar_dominante_secundaria(
        self, cifra: str, semitom_fund: int, qualidade: str
    ) -> Optional[InfoGrau]:
        """Verifica se é V ou V7 de um grau diatônico legítimo (não diminuto e diferente de I)."""
        if qualidade not in ("", "7"):
            return None

        # Alvos possíveis em modo maior: ii (2), iii (3), IV (4), V (5), vi (6)
        # Alvos possíveis em modo menor: III (3), iv (4), V (5), VI (6)
        alvos_validos = [2, 3, 4, 5, 6] if self.modo == "major" else [3, 4, 5, 6]

        for grau_alvo in alvos_validos:
            alvo_semitom = self.graus_semitons[grau_alvo - 1]
            # O dominante de um alvo está 7 semitons acima (uma quinta justa)
            dominante_esperada_semitom = (alvo_semitom + 7) % 12

            if semitom_fund == dominante_esperada_semitom:
                nome_grau_alvo = (
                    GRAUS_MAIOR[grau_alvo - 1]
                    if self.modo == "major"
                    else GRAUS_MENOR[grau_alvo - 1]
                )
                grau_romano = f"V/{nome_grau_alvo}" if qualidade == "" else f"V7/{nome_grau_alvo}"
                return InfoGrau(
                    cifra=cifra,
                    fundamental_semitom=semitom_fund,
                    grau_romano=grau_romano,
                    grau_numero=5,
                    funcao=FuncaoHarmonica.DOMINANTE_SECUNDARIA,
                    eh_secundario=True,
                    alvo_grau_numero=grau_alvo,
                    alvo_nome=nome_grau_alvo,
                )

        return None
