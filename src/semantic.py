"""Análise semântica.

Valida o que a BNF não consegue expressar. As regras estão numeradas como no
README §11 e cada mensagem de erro cita a sua, para dar para ir do erro à
especificação sem procurar.

O primeiro erro encontrado interrompe a compilação.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import ast
from .errors import SemanticError
from .music import MIDI_MAX, MIDI_MIN, numero_midi

BPM_MIN = 20
BPM_MAX = 300

OITAVA_MIN = 0
OITAVA_MAX = 9

DENOMINADORES = {1, 2, 4, 8, 16, 32}

TRANSPOSE_MAX = 24
OCTAVE_MAX = 4

EXTENSAO = ".mid"

BPM_PADRAO = 120
TONALIDADE_PADRAO = ("C", "", "major")

_NOME_DO_ITEM = {
    ast.Tempo: "tempo",
    ast.Key: "key",
    ast.Melody: "melody",
    ast.Output: "output",
}


@dataclass(frozen=True)
class Analise:
    """O que sobrou depois da validação, pronto para virar modelo musical."""

    nome: str
    bpm: int
    tonalidade: tuple[str, str, str]
    melodia: ast.Melody
    variacoes: list
    arquivo: str


def verificar(arvore: ast.Music, fonte: str | None = None) -> Analise:
    return _Verificador(arvore, fonte).executar()


class _Verificador:
    def __init__(self, arvore: ast.Music, fonte: str | None) -> None:
        self.arvore = arvore
        self.fonte = fonte

    def _erro(self, mensagem: str, no) -> SemanticError:
        return SemanticError(mensagem, no.linha, no.coluna, self.fonte)

    # ------------------------------------------------------------ execução

    def executar(self) -> Analise:
        unicos, variacoes = self._agrupar_itens()

        arquivo = self._validar_saida(unicos.get(ast.Output))
        melodia = self._validar_melodia(unicos.get(ast.Melody))
        bpm = self._validar_tempo(unicos.get(ast.Tempo))
        tonalidade = self._tonalidade(unicos.get(ast.Key))

        for evento in melodia.eventos:
            self._validar_duracao(evento)
            if isinstance(evento, ast.Note):
                self._validar_altura(evento)

        for variacao in variacoes:
            for transformacao in variacao.transformacoes:
                self._validar_transformacao(transformacao)

        return Analise(
            nome=self.arvore.nome,
            bpm=bpm,
            tonalidade=tonalidade,
            melodia=melodia,
            variacoes=variacoes,
            arquivo=arquivo,
        )

    # S5 — cada declaração no máximo uma vez
    def _agrupar_itens(self) -> tuple[dict, list]:
        unicos: dict = {}
        variacoes: list = []

        for item in self.arvore.itens:
            if isinstance(item, ast.Variation):
                variacoes.append(item)
                continue

            tipo = type(item)
            if tipo in unicos:
                nome = _NOME_DO_ITEM[tipo]
                anterior = unicos[tipo]
                raise self._erro(
                    f"S5: '{nome}' já foi declarado na linha {anterior.linha}. "
                    f"Cada declaração pode aparecer no máximo uma vez.",
                    item,
                )
            unicos[tipo] = item

        return unicos, variacoes

    # S6, S11 — output obrigatório e com extensão .mid
    def _validar_saida(self, no: ast.Output | None) -> str:
        if no is None:
            raise self._erro(
                "S6: falta a declaração 'output'. A música precisa dizer em que "
                "arquivo será gravada.",
                self.arvore,
            )

        if not no.arquivo.endswith(EXTENSAO):
            raise self._erro(
                f"S11: o arquivo de saída precisa terminar em '{EXTENSAO}'; "
                f'recebido "{no.arquivo}".',
                no,
            )

        return no.arquivo

    # S7 — melodia obrigatória e não vazia
    def _validar_melodia(self, no: ast.Melody | None) -> ast.Melody:
        if no is None:
            raise self._erro(
                "S7: falta o bloco 'melody'. A música precisa ter uma melodia.",
                self.arvore,
            )

        if not no.eventos:
            raise self._erro(
                "S7: o bloco 'melody' está vazio. É preciso ao menos um evento.", no
            )

        return no

    # S1 — faixa de BPM
    def _validar_tempo(self, no: ast.Tempo | None) -> int:
        if no is None:
            return BPM_PADRAO

        if not BPM_MIN <= no.bpm <= BPM_MAX:
            raise self._erro(
                f"S1: tempo {no.bpm} fora da faixa permitida "
                f"({BPM_MIN} a {BPM_MAX} BPM).",
                no,
            )

        return no.bpm

    def _tonalidade(self, no: ast.Key | None) -> tuple[str, str, str]:
        if no is None:
            return TONALIDADE_PADRAO
        return (no.classe, no.acidente, no.modo)

    # S4 — duração representável
    def _validar_duracao(self, evento) -> None:
        numerador, denominador = evento.duracao

        if numerador < 1:
            raise self._erro(
                f"S4: duração {numerador}/{denominador} inválida: o numerador "
                "precisa ser no mínimo 1.",
                evento,
            )

        if denominador not in DENOMINADORES:
            permitidos = ", ".join(str(d) for d in sorted(DENOMINADORES))
            raise self._erro(
                f"S4: duração {numerador}/{denominador} inválida: o denominador "
                f"precisa ser um de {permitidos}.",
                evento,
            )

    # S2, S3 — oitava e altura MIDI
    def _validar_altura(self, nota: ast.Note) -> None:
        if not OITAVA_MIN <= nota.oitava <= OITAVA_MAX:
            raise self._erro(
                f"S2: oitava {nota.oitava} fora da faixa permitida "
                f"({OITAVA_MIN} a {OITAVA_MAX}).",
                nota,
            )

        midi = numero_midi(nota.classe, nota.acidente, nota.oitava)
        if not MIDI_MIN <= midi <= MIDI_MAX:
            lexema = f"{nota.classe}{nota.acidente}{nota.oitava}"
            raise self._erro(
                f"S3: {lexema} corresponde ao número MIDI {midi}, fora da faixa "
                f"{MIDI_MIN} a {MIDI_MAX}.",
                nota,
            )

    # S8, S9, S10 — limites das transformações
    def _validar_transformacao(self, transformacao) -> None:
        if isinstance(transformacao, ast.Repeat):
            if transformacao.vezes < 1:
                raise self._erro(
                    f"S8: repeat {transformacao.vezes} inválido: é preciso "
                    "repetir ao menos uma vez.",
                    transformacao,
                )

        elif isinstance(transformacao, ast.Transpose):
            if abs(transformacao.semitons) > TRANSPOSE_MAX:
                raise self._erro(
                    f"S9: transpose {transformacao.semitons:+d} fora da faixa "
                    f"permitida (-{TRANSPOSE_MAX} a +{TRANSPOSE_MAX} semitons).",
                    transformacao,
                )

        elif isinstance(transformacao, ast.OctaveShift):
            if abs(transformacao.oitavas) > OCTAVE_MAX:
                raise self._erro(
                    f"S10: octave {transformacao.oitavas:+d} fora da faixa "
                    f"permitida (-{OCTAVE_MAX} a +{OCTAVE_MAX} oitavas).",
                    transformacao,
                )
