# Gramática da MusicLang

Notação de `DOCS/BNF_exemplo.pdf`: não-terminais entre `< >`, terminais em maiúsculas,
`::=` para geração, `|` para alternativa, `ε` para vazio.

**13 não-terminais · 24 terminais · 31 produções.**

## Produções

```
P1   <program>          ::= <music> EOF

P2   <music>            ::= MUSIC STRING LBRACE <music_body> RBRACE

P3   <music_body>       ::= <music_item> <music_body>
P4   <music_body>       ::= ε

P5   <music_item>       ::= <tempo_decl>
P6   <music_item>       ::= <key_decl>
P7   <music_item>       ::= <melody_block>
P8   <music_item>       ::= <variation_block>
P9   <music_item>       ::= <output_decl>

P10  <tempo_decl>       ::= TEMPO NUMBER
P11  <key_decl>         ::= KEY PITCH <mode>
P12  <mode>             ::= MAJOR
P13  <mode>             ::= MINOR
P14  <output_decl>      ::= OUTPUT STRING

P15  <melody_block>     ::= MELODY LBRACE <event_list> RBRACE
P16  <event_list>       ::= <event> <event_list>
P17  <event_list>       ::= ε
P18  <event>            ::= NOTE DURATION
P19  <event>            ::= REST DURATION

P20  <variation_block>  ::= VARIATION LBRACE <transform_list> RBRACE
P21  <transform_list>   ::= <transform> <transform_list>
P22  <transform_list>   ::= ε
P23  <transform>        ::= TRANSPOSE <signed_number>
P24  <transform>        ::= OCTAVE <signed_number>
P25  <transform>        ::= REPEAT NUMBER
P26  <transform>        ::= REVERSE
P27  <transform>        ::= INVERT

P28  <signed_number>    ::= <sign_opt> NUMBER
P29  <sign_opt>         ::= PLUS
P30  <sign_opt>         ::= MINUS
P31  <sign_opt>         ::= ε
```

## Decisões de projeto da gramática

| Problema | Como foi resolvido |
|---|---|
| Recursão à esquerda | Não existe. Toda lista é **recursiva à direita**: `<x_list> ::= <x> <x_list> \| ε`. |
| Fatoração | Nenhuma alternativa de um mesmo não-terminal começa com o mesmo símbolo, então não foi preciso fatorar. |
| Sinal opcional | `[ + \| - ]` virou o não-terminal anulável `<sign_opt>`, cujo FOLLOW é só `NUMBER` — não colide com `PLUS`/`MINUS`. |
| Ordem livre dos itens | `<music_body>` aceita `<music_item>` em qualquer ordem e qualquer quantidade. Duplicatas e ausências são problema da **análise semântica** (S5, S6, S7), não da BNF. |
| Duração | É sempre `DURATION` (`1/4`). `NUMBER` aparece só em `tempo` e `repeat`, o que evita qualquer alternância em `<event>`. |

## Tabela LL(1) — `M[A, a]`

Uma produção por célula. Célula vazia ⇒ erro sintático.

| A | produção por token |
|---|---|
| `<program>` | MUSIC→P1 |
| `<music>` | MUSIC→P2 |
| `<music_body>` | TEMPO→P3 · KEY→P3 · MELODY→P3 · VARIATION→P3 · OUTPUT→P3 · RBRACE→P4 |
| `<music_item>` | TEMPO→P5 · KEY→P6 · MELODY→P7 · VARIATION→P8 · OUTPUT→P9 |
| `<tempo_decl>` | TEMPO→P10 |
| `<key_decl>` | KEY→P11 |
| `<mode>` | MAJOR→P12 · MINOR→P13 |
| `<output_decl>` | OUTPUT→P14 |
| `<melody_block>` | MELODY→P15 |
| `<event_list>` | NOTE→P16 · REST→P16 · RBRACE→P17 |
| `<event>` | NOTE→P18 · REST→P19 |
| `<variation_block>` | VARIATION→P20 |
| `<transform_list>` | TRANSPOSE→P21 · OCTAVE→P21 · REPEAT→P21 · REVERSE→P21 · INVERT→P21 · RBRACE→P22 |
| `<transform>` | TRANSPOSE→P23 · OCTAVE→P24 · REPEAT→P25 · REVERSE→P26 · INVERT→P27 |
| `<signed_number>` | PLUS→P28 · MINUS→P28 · NUMBER→P28 |
| `<sign_opt>` | PLUS→P29 · MINUS→P30 · NUMBER→P31 |

**42 células preenchidas.** A construção da tabela em `src/parser.py` levanta `GrammarError`
se alguma célula receber uma segunda produção — a ausência de conflitos é verificada em tempo
de importação, não confiada à conferência manual.

## Algoritmo do parser

```
empilha <program>
enquanto a pilha não estiver vazia:
    topo = desempilha()
    se topo é terminal:
        casa com o lookahead e avança          (senão: ParserError)
    se topo é não-terminal:
        p = M[topo, lookahead]                 (se vazio: ParserError)
        empilha a ação de p
        empilha o lado direito de p invertido
    se topo é ação:
        desempilha os valores dos símbolos de p e constrói o nó da AST
```

A ação é empilhada **antes** do lado direito. Como a pilha é LIFO, ela sai por último — depois
que todos os símbolos daquela produção já produziram seus valores.
