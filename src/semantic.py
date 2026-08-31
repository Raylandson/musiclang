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
from .harmony import FuncaoHarmonica, InfoGrau, TeoriaHarmonica
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
    ast.Harmony: "harmony",
    ast.Output: "output",
}


@dataclass(frozen=True)
class Analise:
    """O que sobrou depois da validação, pronto para virar modelo musical."""

    nome: str
    bpm: int
    tonalidade: tuple[str, str, str]
    melodia: ast.Melody
    harmonia: ast.Harmony | None
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
        harmonia = self._validar_harmonia(unicos.get(ast.Harmony), tonalidade)

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
            harmonia=harmonia,
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

    # S12, S13, S14, S15, S16, S17 — validação do bloco harmony
    def _validar_harmonia(
        self, no: ast.Harmony | None, tonalidade: tuple[str, str, str]
    ) -> ast.Harmony | None:
        if no is None:
            return None

        if not no.eventos:
            raise self._erro(
                "S13: o bloco 'harmony' está vazio. É preciso ao menos um acorde.", no
            )

        for evento in no.eventos:
            self._validar_duracao(evento)

        acordes = [e for e in no.eventos if isinstance(e, ast.Chord)]
        if not acordes:
            raise self._erro(
                "S13: o bloco 'harmony' contém apenas pausas. É preciso ao menos um acorde.",
                no,
            )

        self._validar_progressao(acordes, tonalidade)
        return no

    def _validar_progressao(
        self, acordes: list[ast.Chord], tonalidade: tuple[str, str, str]
    ) -> None:
        classe_tom, acidente_tom, modo = tonalidade
        teoria = TeoriaHarmonica(classe_tom, acidente_tom, modo)

        analises: list[tuple[ast.Chord, InfoGrau]] = []
        for acorde in acordes:
            info = teoria.analisar_acorde(
                acorde.classe, acorde.acidente, acorde.qualidade
            )
            if info is None:
                tom_str = f"{classe_tom}{acidente_tom} {modo}"
                raise self._erro(
                    f"S14: acorde '{acorde.cifra}' estranho à tonalidade '{tom_str}'. "
                    "Não pertence ao campo harmônico nem é dominante secundária legítima.",
                    acorde,
                )
            analises.append((acorde, info))

        # Validação da condução funcional clássica estrita passo a passo
        for i in range(len(analises) - 1):
            acorde_atual, info_atual = analises[i]
            acorde_prox, info_prox = analises[i + 1]

            # S16: Dominante secundária deve resolver no seu acorde alvo
            if info_atual.eh_secundario:
                if info_prox.grau_numero != info_atual.alvo_grau_numero:
                    raise self._erro(
                        f"S16: dominante secundária '{acorde_atual.cifra}' ({info_atual.grau_romano}) "
                        f"deve resolver no grau alvo {info_atual.alvo_nome}, mas foi seguida por '{acorde_prox.cifra}' ({info_prox.grau_romano}).",
                        acorde_atual,
                    )

            # S15: Proibição de retrogradação funcional (Dominante -> Subdominante)
            if info_atual.funcao == FuncaoHarmonica.DOMINANTE:
                if info_prox.funcao == FuncaoHarmonica.SUBDOMINANTE:
                    raise self._erro(
                        f"S15: violação de condução funcional clássica: retrogradação harmônica de "
                        f"Dominante ('{acorde_atual.cifra}' - grau {info_atual.grau_romano}) para "
                        f"Subdominante ('{acorde_prox.cifra}' - grau {info_prox.grau_romano}). "
                        "A função Dominante deve resolver em Tônica ou cadência de engano.",
                        acorde_prox,
                    )

        # S17: Resolução final na Tônica (grau I / i)
        ultimo_acorde, ultima_info = analises[-1]
        if ultima_info.grau_numero != 1 or ultima_info.funcao != FuncaoHarmonica.TONICA:
            raise self._erro(
                f"S17: progressão harmônica incompleta: encerra em '{ultimo_acorde.cifra}' "
                f"({ultima_info.grau_romano} - {ultima_info.funcao.value}), mas a condução clássica "
                "exige resolução final na Tônica (grau I / repouso).",
                ultimo_acorde,
            )

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

    # S4 / S12 — duração representável
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
