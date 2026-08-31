# Gramática da MusicLang

Notação de `DOCS/BNF_exemplo.pdf`: não-terminais entre `< >`, terminais em maiúsculas,
`::=` para geração, `|` para alternativa, `ε` para vazio.

**19 não-terminais · 25 terminais · 37 produções.**

## Produções

```
P1   <program>          ::= <music> EOF

P2   <music>            ::= MUSIC STRING LBRACE <music_body> RBRACE

P3   <music_body>       ::= <music_item> <music_body>
P4   <music_body>       ::= ε

P5   <music_item>       ::= <tempo_decl>
P6   <music_item>       ::= <key_decl>
P7   <music_item>       ::= <melody_block>
P8   <music_item>       ::= <harmony_block>
P9   <music_item>       ::= <variation_block>
P10  <music_item>       ::= <output_decl>

P11  <tempo_decl>       ::= TEMPO NUMBER
P12  <key_decl>         ::= KEY CHORD <mode>
P13  <mode>             ::= MAJOR
P14  <mode>             ::= MINOR
P15  <output_decl>      ::= OUTPUT STRING

P16  <melody_block>     ::= MELODY LBRACE <event_list> RBRACE
P17  <event_list>       ::= <event> <event_list>
P18  <event_list>       ::= ε
P19  <event>            ::= NOTE DURATION
P20  <event>            ::= REST DURATION

P21  <harmony_block>    ::= HARMONY LBRACE <chord_event_list> RBRACE
P22  <chord_event_list> ::= <chord_event> <chord_event_list>
P23  <chord_event_list> ::= ε
P24  <chord_event>      ::= CHORD DURATION
P25  <chord_event>      ::= REST DURATION

P26  <variation_block>  ::= VARIATION LBRACE <transform_list> RBRACE
P27  <transform_list>   ::= <transform> <transform_list>
P28  <transform_list>   ::= ε
P29  <transform>        ::= TRANSPOSE <signed_number>
P30  <transform>        ::= OCTAVE <signed_number>
P31  <transform>        ::= REPEAT NUMBER
P32  <transform>        ::= REVERSE
P33  <transform>        ::= INVERT

P34  <signed_number>    ::= <sign_opt> NUMBER
P35  <sign_opt>         ::= PLUS
P36  <sign_opt>         ::= MINUS
P37  <sign_opt>         ::= ε
```

## Decisões de projeto da gramática

| Problema | Como foi resolvido |
|---|---|
| Recursão à esquerda | Não existe. Toda lista é **recursiva à direita**: `<x_list> ::= <x> <x_list> \| ε`. |
| Fatoração | Nenhuma alternativa de um mesmo não-terminal começa com o mesmo símbolo, então não foi preciso fatorar. |
| Sinal opcional | `[ + \| - ]` virou o não-terminal anulável `<sign_opt>`, cujo FOLLOW é só `NUMBER` — não colide com `PLUS`/`MINUS`. |
| Ordem livre dos itens | `<music_body>` aceita `<music_item>` em qualquer ordem e qualquer quantidade. Duplicatas e ausências são problema da **análise semântica** (S5, S6, S7), não da BNF. |
| Harmonia funcional | `<harmony_block>` suporta cifras e durações (`CHORD DURATION`). As regras clássicas (T-S-D-T) são validadas na análise semântica (S12 a S17). |
| Duração | É sempre `DURATION` (`1/4`). `NUMBER` aparece só em `tempo` e `repeat`, o que evita qualquer alternância em `<event>` e `<chord_event>`. |

## Tabela LL(1) — `M[A, a]`

Uma produção por célula. Célula vazia ⇒ erro sintático.

| A | produção por token |
|---|---|
| `<program>` | MUSIC→P1 |
| `<music>` | MUSIC→P2 |
| `<music_body>` | TEMPO→P3 · KEY→P3 · MELODY→P3 · HARMONY→P3 · VARIATION→P3 · OUTPUT→P3 · RBRACE→P4 |
| `<music_item>` | TEMPO→P5 · KEY→P6 · MELODY→P7 · HARMONY→P8 · VARIATION→P9 · OUTPUT→P10 |
| `<tempo_decl>` | TEMPO→P11 |
| `<key_decl>` | KEY→P12 |
| `<mode>` | MAJOR→P13 · MINOR→P14 |
| `<output_decl>` | OUTPUT→P15 |
| `<melody_block>` | MELODY→P16 |
| `<event_list>` | NOTE→P17 · REST→P17 · RBRACE→P18 |
| `<event>` | NOTE→P19 · REST→P20 |
| `<harmony_block>` | HARMONY→P21 |
| `<chord_event_list>` | CHORD→P22 · REST→P22 · RBRACE→P23 |
| `<chord_event>` | CHORD→P24 · REST→P25 |
| `<variation_block>` | VARIATION→P26 |
| `<transform_list>` | TRANSPOSE→P27 · OCTAVE→P27 · REPEAT→P27 · REVERSE→P27 · INVERT→P27 · RBRACE→P28 |
| `<transform>` | TRANSPOSE→P29 · OCTAVE→P30 · REPEAT→P31 · REVERSE→P32 · INVERT→P33 |
| `<signed_number>` | PLUS→P34 · MINUS→P34 · NUMBER→P34 |
| `<sign_opt>` | PLUS→P35 · MINUS→P36 · NUMBER→P37 |

**50 células preenchidas.** A construção da tabela em `src/parser.py` levanta `GrammarError`
se alguma célula receber uma segunda produção — a ausência de conflitos é verificada em tempo
de importação, não confiada à conferência manual.
