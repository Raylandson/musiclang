"""Erros das fases do compilador.

Todo erro carrega linha e coluna e, quando o fonte está disponível, imprime a
linha ofensora com um cursor apontando a coluna exata.
"""

from __future__ import annotations


class CompilerError(Exception):
    """Base das três fases. Subclasses só trocam o rótulo da fase."""

    fase = "de compilação"

    def __init__(
        self,
        mensagem: str,
        linha: int,
        coluna: int,
        fonte: str | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.fonte = fonte

    def __str__(self) -> str:
        partes = [f"Erro {self.fase} na linha {self.linha}, coluna {self.coluna}.", ""]
        partes.append(self.mensagem)

        contexto = self._contexto()
        if contexto:
            partes.extend(["", *contexto])

        return "\n".join(partes)

    def _contexto(self) -> list[str]:
        if self.fonte is None:
            return []

        linhas = self.fonte.splitlines()
        if not 1 <= self.linha <= len(linhas):
            return []

        numero = str(self.linha)
        texto = linhas[self.linha - 1]

        # Tabs deslocariam o cursor; viram espaços para o alinhamento bater.
        texto = texto.replace("\t", " ")

        return [
            f"  {numero} | {texto}",
            f"  {' ' * len(numero)} | {' ' * (self.coluna - 1)}^",
        ]


class LexerError(CompilerError):
    fase = "léxico"


class ParserError(CompilerError):
    fase = "sintático"


class SemanticError(CompilerError):
    fase = "semântico"
