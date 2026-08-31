import unittest

from src.ast import Chord, Harmony, Music, Note, Rest
from src.errors import SemanticError
from src.harmony import FuncaoHarmonica, TeoriaHarmonica
from src.lexer import TokenType, tokenizar
from src.parser import analisar
from src.semantic import verificar


class TestLexerHarmony(unittest.TestCase):
    def test_reconhecimento_palavra_reservada_harmony(self):
        tokens = tokenizar("harmony { }")
        self.assertEqual(tokens[0].tipo, TokenType.HARMONY)
        self.assertEqual(tokens[1].tipo, TokenType.LBRACE)
        self.assertEqual(tokens[2].tipo, TokenType.RBRACE)

    def test_reconhecimento_acordes_diversos(self):
        fonte = "C Dm G7 Cmaj7 Bdim Bm7b5 D7 F#m7"
        tokens = tokenizar(fonte)
        esperados = [
            ("C", "C", "", ""),
            ("Dm", "D", "", "m"),
            ("G7", "G", "", "7"),
            ("Cmaj7", "C", "", "maj7"),
            ("Bdim", "B", "", "dim"),
            ("Bm7b5", "B", "", "m7b5"),
            ("D7", "D", "", "7"),
            ("F#m7", "F", "#", "m7"),
        ]
        for token, (lexema, classe, acidente, qualidade) in zip(tokens[:-1], esperados):
            self.assertEqual(token.tipo, TokenType.CHORD)
            self.assertEqual(token.lexema, lexema)
            self.assertEqual(token.valor, (classe, acidente, qualidade))

    def test_distincao_entre_notas_e_acordes(self):
        tokens = tokenizar("C4 1/4 C 1/1 D4 1/4 Dm 1/2")
        self.assertEqual(tokens[0].tipo, TokenType.NOTE)
        self.assertEqual(tokens[0].valor, ("C", "", 4))
        self.assertEqual(tokens[1].tipo, TokenType.DURATION)
        self.assertEqual(tokens[2].tipo, TokenType.CHORD)
        self.assertEqual(tokens[2].valor, ("C", "", ""))
        self.assertEqual(tokens[4].tipo, TokenType.NOTE)
        self.assertEqual(tokens[6].tipo, TokenType.CHORD)
        self.assertEqual(tokens[6].valor, ("D", "", "m"))


class TestTeoriaHarmonica(unittest.TestCase):
    def setUp(self):
        self.c_major = TeoriaHarmonica("C", "", "major")
        self.a_minor = TeoriaHarmonica("A", "", "minor")

    def test_graus_diatonicos_c_maior(self):
        # I: C, ii: Dm, iii: Em, IV: F, V: G, vi: Am, vii°: Bdim
        c = self.c_major.analisar_acorde("C", "", "")
        self.assertIsNotNone(c)
        self.assertEqual(c.grau_romano, "I")
        self.assertEqual(c.funcao, FuncaoHarmonica.TONICA)

        dm = self.c_major.analisar_acorde("D", "", "m")
        self.assertIsNotNone(dm)
        self.assertEqual(dm.grau_romano, "ii")
        self.assertEqual(dm.funcao, FuncaoHarmonica.SUBDOMINANTE)

        em = self.c_major.analisar_acorde("E", "", "m")
        self.assertIsNotNone(em)
        self.assertEqual(em.grau_romano, "iii")
        self.assertEqual(em.funcao, FuncaoHarmonica.TONICA)

        f = self.c_major.analisar_acorde("F", "", "")
        self.assertIsNotNone(f)
        self.assertEqual(f.grau_romano, "IV")
        self.assertEqual(f.funcao, FuncaoHarmonica.SUBDOMINANTE)

        g7 = self.c_major.analisar_acorde("G", "", "7")
        self.assertIsNotNone(g7)
        self.assertEqual(g7.grau_romano, "V")
        self.assertEqual(g7.funcao, FuncaoHarmonica.DOMINANTE)

        am = self.c_major.analisar_acorde("A", "", "m")
        self.assertIsNotNone(am)
        self.assertEqual(am.grau_romano, "vi")
        self.assertEqual(am.funcao, FuncaoHarmonica.TONICA)

        bdim = self.c_major.analisar_acorde("B", "", "dim")
        self.assertIsNotNone(bdim)
        self.assertEqual(bdim.grau_romano, "vii°")
        self.assertEqual(bdim.funcao, FuncaoHarmonica.DOMINANTE)

    def test_dominantes_secundarios_c_maior(self):
        # D7 é V7/V (G)
        d7 = self.c_major.analisar_acorde("D", "", "7")
        self.assertIsNotNone(d7)
        self.assertTrue(d7.eh_secundario)
        self.assertEqual(d7.grau_romano, "V7/V")
        self.assertEqual(d7.alvo_grau_numero, 5)
        self.assertEqual(d7.alvo_nome, "V")

        # A7 é V7/ii (Dm)
        a7 = self.c_major.analisar_acorde("A", "", "7")
        self.assertIsNotNone(a7)
        self.assertTrue(a7.eh_secundario)
        self.assertEqual(a7.grau_romano, "V7/ii")
        self.assertEqual(a7.alvo_grau_numero, 2)

        # E7 é V7/vi (Am)
        e7 = self.c_major.analisar_acorde("E", "", "7")
        self.assertIsNotNone(e7)
        self.assertTrue(e7.eh_secundario)
        self.assertEqual(e7.grau_romano, "V7/vi")
        self.assertEqual(e7.alvo_grau_numero, 6)

    def test_acorde_estranho_rejeitado(self):
        # F#m não é diatônico em Dó Maior nem dominante secundária
        fsharp_m = self.c_major.analisar_acorde("F", "#", "m")
        self.assertIsNone(fsharp_m)


class TestParserHarmony(unittest.TestCase):
    def test_ast_com_bloco_harmony(self):
        fonte = """
        music "Teste Harmonia" {
            tempo 120
            key C major
            harmony {
                C 1/1
                Dm 1/2
                G7 1/2
                C 1/1
            }
            melody {
                C4 1/4
            }
            output "teste.mid"
        }
        """
        arvore = analisar(fonte)
        self.assertEqual(len(arvore.itens), 5)
        harmonia = next(i for i in arvore.itens if isinstance(i, Harmony))
        self.assertEqual(len(harmonia.eventos), 4)
        self.assertIsInstance(harmonia.eventos[0], Chord)
        self.assertEqual(harmonia.eventos[0].cifra, "C")
        self.assertEqual(harmonia.eventos[1].cifra, "Dm")
        self.assertEqual(harmonia.eventos[2].cifra, "G7")
        self.assertEqual(harmonia.eventos[3].cifra, "C")


class TestSemanticHarmonyValidation(unittest.TestCase):
    def _compilar(self, progressao_chords: str, tom="C major") -> None:
        fonte = f"""
        music "Harmonia" {{
            tempo 120
            key {tom}
            harmony {{
                {progressao_chords}
            }}
            melody {{
                C4 1/4
            }}
            output "teste.mid"
        }}
        """
        arvore = analisar(fonte)
        return verificar(arvore, fonte)

    def test_cadencia_autentica_perfeita_valida(self):
        # I -> IV -> V7 -> I (C -> F -> G7 -> C)
        analise = self._compilar("C 1/1 F 1/1 G7 1/1 C 1/1")
        self.assertIsNotNone(analise.harmonia)
        self.assertEqual(len(analise.harmonia.eventos), 4)

    def test_cadencia_jazz_mpb_valida(self):
        # I -> ii -> V7 -> I (C -> Dm -> G7 -> C)
        analise = self._compilar("C 1/1 Dm 1/1 G7 1/1 C 1/1")
        self.assertIsNotNone(analise.harmonia)

    def test_cadencia_deceptiva_engano_valida(self):
        # I -> IV -> V7 -> vi -> ii -> V7 -> I (C -> F -> G7 -> Am -> Dm -> G7 -> C)
        analise = self._compilar("C 1/1 F 1/1 G7 1/1 Am 1/1 Dm 1/1 G7 1/1 C 1/1")
        self.assertIsNotNone(analise.harmonia)

    def test_dominante_secundaria_resolvida_valida(self):
        # I -> V7/V -> V7 -> I (C -> D7 -> G7 -> C)
        analise = self._compilar("C 1/1 D7 1/1 G7 1/1 C 1/1")
        self.assertIsNotNone(analise.harmonia)

    def test_erro_s15_retrogradacao_dominante_para_subdominante(self):
        # V -> IV (G7 -> F) é retrogradação proibida no modo clássico estrito
        with self.assertRaises(SemanticError) as ctx:
            self._compilar("C 1/1 G7 1/1 F 1/1 C 1/1")
        self.assertIn("S15", str(ctx.exception))
        self.assertIn("retrogradação harmônica", str(ctx.exception))

    def test_erro_s16_dominante_secundaria_nao_resolvida(self):
        # D7 (V/V) deve resolver em G, mas vai para Am (vi)
        with self.assertRaises(SemanticError) as ctx:
            self._compilar("C 1/1 D7 1/1 Am 1/1 C 1/1")
        self.assertIn("S16", str(ctx.exception))
        self.assertIn("dominante secundária", str(ctx.exception))

    def test_erro_s14_acorde_estranho_a_tonalidade(self):
        # F#m em C major
        with self.assertRaises(SemanticError) as ctx:
            self._compilar("C 1/1 F#m 1/1 G 1/1 C 1/1")
        self.assertIn("S14", str(ctx.exception))
        self.assertIn("estranho à tonalidade", str(ctx.exception))

    def test_erro_s17_progressao_nao_resolve_na_tonica(self):
        # Termina em G7 (Dominante) em vez da Tônica C
        with self.assertRaises(SemanticError) as ctx:
            self._compilar("C 1/1 Dm 1/1 G7 1/1")
        self.assertIn("S17", str(ctx.exception))
        self.assertIn("resolução final na Tônica", str(ctx.exception))

    def test_erro_s13_bloco_harmony_vazio(self):
        fonte = """
        music "Harmonia" {
            tempo 120
            key C major
            harmony { }
            melody { C4 1/4 }
            output "teste.mid"
        }
        """
        with self.assertRaises(SemanticError) as ctx:
            verificar(analisar(fonte), fonte)
        self.assertIn("S13", str(ctx.exception))

    def test_retrocompatibilidade_musica_sem_harmony(self):
        # Músicas anteriores sem bloco harmony continuam compilando normalmente
        fonte = """
        music "Sem Harmonia" {
            tempo 120
            key C major
            melody {
                C4 1/4 D4 1/4 E4 1/4 G4 1/2
            }
            output "teste.mid"
        }
        """
        analise = verificar(analisar(fonte), fonte)
        self.assertIsNone(analise.harmonia)
        self.assertEqual(len(analise.melodia.eventos), 4)


if __name__ == "__main__":
    unittest.main()
