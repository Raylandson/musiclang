# FIRST e FOLLOW

Cálculo manual para a gramática de `grammar.md`. Conferido contra a implementação por
`tests/parser/test_grammar.py`, que compara os conjuntos aqui documentados com os que
`src/parser.py` calcula.

Abreviações usadas nas tabelas:

- **ITENS** = `TEMPO` `KEY` `MELODY` `VARIATION` `OUTPUT`
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
| `<music_item>` | ITENS | P5–P9, um terminal inicial distinto por alternativa |
| `<tempo_decl>` | TEMPO | P10 |
| `<key_decl>` | KEY | P11 |
| `<mode>` | MAJOR, MINOR | P12, P13 |
| `<output_decl>` | OUTPUT | P14 |
| `<melody_block>` | MELODY | P15 |
| `<event_list>` | NOTE, REST, ε | P16 → FIRST(`<event>`); P17 dá ε |
| `<event>` | NOTE, REST | P18, P19 |
| `<variation_block>` | VARIATION | P20 |
| `<transform_list>` | TRANSF, ε | P21 → FIRST(`<transform>`); P22 dá ε |
| `<transform>` | TRANSF | P23–P27 |
| `<signed_number>` | PLUS, MINUS, NUMBER | P28: `<sign_opt>` é anulável, então NUMBER também entra |
| `<sign_opt>` | PLUS, MINUS, ε | P29, P30, P31 |

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
| `<mode>` | ITENS, RBRACE | P11: no fim de `<key_decl>` → herda FOLLOW(`<key_decl>`) |
| `<output_decl>` | ITENS, RBRACE | idem, por P9 |
| `<melody_block>` | ITENS, RBRACE | idem, por P7 |
| `<event_list>` | RBRACE | P15: seguido de RBRACE. P16 no fim → herda o próprio FOLLOW |
| `<event>` | NOTE, REST, RBRACE | P16: FIRST(`<event_list>`) menos ε, mais FOLLOW(`<event_list>`) |
| `<variation_block>` | ITENS, RBRACE | por P8 |
| `<transform_list>` | RBRACE | P20: seguido de RBRACE |
| `<transform>` | TRANSF, RBRACE | P21: FIRST(`<transform_list>`) menos ε, mais FOLLOW(`<transform_list>`) |
| `<signed_number>` | TRANSF, RBRACE | P23/P24: no fim de `<transform>` → herda FOLLOW(`<transform>`) |
| `<sign_opt>` | NUMBER | P28: seguido do terminal NUMBER |

---

## Verificação da condição LL(1)

### 1. Produções anuláveis: `FIRST(A) ∩ FOLLOW(A) = ∅`

| Anulável | FIRST menos ε | FOLLOW | ∩ |
|---|---|---|---|
| `<music_body>` | ITENS | RBRACE | ∅ ✔ |
| `<event_list>` | NOTE, REST | RBRACE | ∅ ✔ |
| `<transform_list>` | TRANSF | RBRACE | ∅ ✔ |
| `<sign_opt>` | PLUS, MINUS | NUMBER | ∅ ✔ |

O que torna as três primeiras seguras é o mesmo fato: só `RBRACE` fecha um bloco, e `RBRACE`
nunca inicia nenhum item, evento ou transformação.

### 2. Alternativas não-anuláveis: FIRST dois a dois disjuntos

| Não-terminal | Alternativas | FIRST |
|---|---|---|
| `<music_item>` | P5–P9 | TEMPO · KEY · MELODY · VARIATION · OUTPUT |
| `<mode>` | P12, P13 | MAJOR · MINOR |
| `<event>` | P18, P19 | NOTE · REST |
| `<transform>` | P23–P27 | TRANSPOSE · OCTAVE · REPEAT · REVERSE · INVERT |
| `<sign_opt>` | P29, P30 | PLUS · MINUS |

Nenhum terminal se repete dentro de uma mesma linha.

**Conclusão: a gramática é LL(1).**
