# FIRST e FOLLOW

Cálculo para a gramática de `grammar.md`. Conferido contra a implementação por
`src/parser.py`, que calcula e verifica ausência de conflitos em tempo de importação.

Abreviações usadas nas tabelas:

- **ITENS** = `TEMPO` `KEY` `MELODY` `HARMONY` `VARIATION` `OUTPUT`
- **TRANSF** = `TRANSPOSE` `OCTAVE` `REPEAT` `REVERSE` `INVERT`

---

## FIRST

Regras aplicadas:

1. `FIRST(a) = {a}` para todo terminal `a`.
2. Para `A ::= X1 X2 … Xn`, acrescenta-se `FIRST(X1)` menos ε; se `X1` for anulável,
   segue-se para `X2`, e assim por diante.
3. Se todos os `Xi` forem anuláveis, ε entra em `FIRST(A)`.

| Não-terminal | FIRST | Origem |
|---|---|---|
| `<program>` | MUSIC | P1 → FIRST(`<music>`) |
| `<music>` | MUSIC | P2 começa com o terminal MUSIC |
| `<music_body>` | ITENS, ε | P3 → FIRST(`<music_item>`); P4 dá ε |
| `<music_item>` | ITENS | P5–P10, um terminal inicial distinto por alternativa |
| `<tempo_decl>` | TEMPO | P11 |
| `<key_decl>` | KEY | P12 |
| `<mode>` | MAJOR, MINOR | P13, P14 |
| `<output_decl>` | OUTPUT | P15 |
| `<melody_block>` | MELODY | P16 |
| `<event_list>` | NOTE, REST, ε | P17 → FIRST(`<event>`); P18 dá ε |
| `<event>` | NOTE, REST | P19, P20 |
| `<harmony_block>` | HARMONY | P21 |
| `<chord_event_list>` | CHORD, REST, ε | P22 → FIRST(`<chord_event>`); P23 dá ε |
| `<chord_event>` | CHORD, REST | P24, P25 |
| `<variation_block>` | VARIATION | P26 |
| `<transform_list>` | TRANSF, ε | P27 → FIRST(`<transform>`); P28 dá ε |
| `<transform>` | TRANSF | P29–P33 |
| `<signed_number>` | PLUS, MINUS, NUMBER | P34: `<sign_opt>` é anulável, então NUMBER também entra |
| `<sign_opt>` | PLUS, MINUS, ε | P35, P36, P37 |

---

## FOLLOW

Regras aplicadas:

1. Para `A ::= α B β`, acrescenta-se `FIRST(β)` menos ε a `FOLLOW(B)`.
2. Se `β` for anulável (ou vazio), acrescenta-se `FOLLOW(A)` a `FOLLOW(B)`.

`EOF` não precisa ser semeado no símbolo inicial: ele aparece explicitamente em P1.

| Não-terminal | FOLLOW | Origem |
|---|---|---|
| `<program>` | — | nunca aparece do lado direito |
| `<music>` | EOF | P1: `<music>` é seguido do terminal EOF |
| `<music_body>` | RBRACE | P2: seguido de RBRACE. P3 no fim → herda o próprio FOLLOW |
| `<music_item>` | ITENS, RBRACE | P3: FIRST(`<music_body>`) menos ε, mais FOLLOW(`<music_body>`) por ser anulável |
| `<tempo_decl>` | ITENS, RBRACE | P5: no fim de `<music_item>` → herda FOLLOW(`<music_item>`) |
| `<key_decl>` | ITENS, RBRACE | idem, por P6 |
| `<mode>` | ITENS, RBRACE | P12: no fim de `<key_decl>` → herda FOLLOW(`<key_decl>`) |
| `<output_decl>` | ITENS, RBRACE | idem, por P10 |
| `<melody_block>` | ITENS, RBRACE | idem, por P7 |
| `<harmony_block>` | ITENS, RBRACE | idem, por P8 |
| `<event_list>` | RBRACE | P16: seguido de RBRACE. P17 no fim → herda o próprio FOLLOW |
| `<event>` | NOTE, REST, RBRACE | P17: FIRST(`<event_list>`) menos ε, mais FOLLOW(`<event_list>`) |
| `<chord_event_list>` | RBRACE | P21: seguido de RBRACE. P22 no fim → herda o próprio FOLLOW |
| `<chord_event>` | CHORD, REST, RBRACE | P22: FIRST(`<chord_event_list>`) menos ε, mais FOLLOW(`<chord_event_list>`) |
| `<variation_block>` | ITENS, RBRACE | por P9 |
| `<transform_list>` | RBRACE | P26: seguido de RBRACE |
| `<transform>` | TRANSF, RBRACE | P27: FIRST(`<transform_list>`) menos ε, mais FOLLOW(`<transform_list>`) |
| `<signed_number>` | TRANSF, RBRACE | P29/P30: no fim de `<transform>` → herda FOLLOW(`<transform>`) |
| `<sign_opt>` | NUMBER | P34: seguido do terminal NUMBER |

---

## Verificação da condição LL(1)

### 1. Produções anuláveis: `FIRST(A) ∩ FOLLOW(A) = ∅`

| Anulável | FIRST menos ε | FOLLOW | ∩ |
|---|---|---|---|
| `<music_body>` | ITENS | RBRACE | ∅ ✔ |
| `<event_list>` | NOTE, REST | RBRACE | ∅ ✔ |
| `<chord_event_list>` | CHORD, REST | RBRACE | ∅ ✔ |
| `<transform_list>` | TRANSF | RBRACE | ∅ ✔ |
| `<sign_opt>` | PLUS, MINUS | NUMBER | ∅ ✔ |

### 2. Alternativas não-anuláveis: FIRST dois a dois disjuntos

| Não-terminal | Alternativas | FIRST |
|---|---|---|
| `<music_item>` | P5–P10 | TEMPO · KEY · MELODY · HARMONY · VARIATION · OUTPUT |
| `<mode>` | P13, P14 | MAJOR · MINOR |
| `<event>` | P19, P20 | NOTE · REST |
| `<chord_event>` | P24, P25 | CHORD · REST |
| `<transform>` | P29–P33 | TRANSPOSE · OCTAVE · REPEAT · REVERSE · INVERT |
| `<sign_opt>` | P35, P36 | PLUS · MINUS |

Nenhum terminal se repete dentro de uma mesma linha.

**Conclusão: a gramática é LL(1).**
