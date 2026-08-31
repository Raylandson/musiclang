# 🎼 MusicLang

**MusicLang** é um compilador completo desenvolvido em Python para uma linguagem de domínio específico (DSL) voltada à descrição textual, validação formal, análise harmônica funcional e geração de arquivos **MIDI**.

O projeto percorre todas as fases clássicas da teoria de compiladores: análise léxica manual (sem regex), análise sintática **LL(1)** dirigida por tabela preditiva, construção de Árvore Sintática Abstrata (AST), validação semântica com verificação de **harmonia funcional por graus da escala** e geração de arquivos `.mid` multitrack com suporte a melodia e acompanhamento harmônico.

---

## 📑 Sumário

- [Arquitetura do Compilador](#-arquitetura-do-compilador)
- [Pré-requisitos e Instalação](#-pré-requisitos-e-instalação)
- [Como Executar](#-como-executar)
- [Sintaxe da Linguagem MusicLang](#-sintaxe-da-linguagem-musiclang)
- [Análise e Validação de Harmonia Funcional](#-análise-e-validação-de-harmonia-funcional)
- [Catálogo de Erros Semânticos (S1 a S17)](#-catálogo-de-erros-semânticos-s1-a-s17)
- [Exemplos Incluídos](#-exemplos-incluídos)
- [Como Escutar os Arquivos MIDI Gerados](#-como-escutar-os-arquivos-midi-gerados)
- [Testes Automatizados](#-testes-automatizados)
- [Estrutura do Repositório](#-estrutura-do-repositório)

---

## 🏛️ Arquitetura do Compilador

O compilador processa os arquivos de entrada através das seguintes etapas:

```
Código-Fonte (.music)
         │
         ▼
 [1] Analisador Léxico (src/lexer.py) ──► Autômato finito manual caractere a caractere
         │
         ▼
 [2] Analisador Sintático LL(1) (src/parser.py) ──► Tabela M[A, a] (50 células, 0 conflitos)
         │
         ▼
 [3] Árvore Sintática Abstrata (src/ast.py) ──► Nós estruturados com coordenadas
         │
         ▼
 [4] Análise Semântica (src/semantic.py & src/harmony.py) ──► Regras físicas e Gramática Funcional
         │
         ▼
 [5] Geração de Código MIDI (src/music.py) ──► Arquivo .mid multitrack (melodia + harmonia)
```

### Módulos Principais

* **[`src/lexer.py`](src/lexer.py):** Analisador léxico manual. Reconhece palavras-chave (`music`, `tempo`, `key`, `harmony`, `melody`, `variation`, `output`), símbolos, durações fracionárias (`1/4`, `1/8`, etc.), notas com oitava (`C4`, `F#3`) e cifras de acordes (`C`, `Dm`, `G7`, `Cmaj7`, `Bdim`, `Bm7b5`, `D7`).
* **[`src/parser.py`](src/parser.py):** Analisador sintático LL(1) preditivo não-recursivo (baseado em pilha). Calcula os conjuntos `FIRST` e `FOLLOW` e constrói a tabela sintática em tempo de importação, impedindo a execução de qualquer gramática com ambiguidades.
* **[`src/ast.py`](src/ast.py):** Estrutura de nós tipados (`Music`, `Tempo`, `Key`, `Harmony`, `Chord`, `Melody`, `Note`, `Rest`, `Variation`, `Transpose`, etc.) e gerador de representação visual em árvore.
* **[`src/harmony.py`](src/harmony.py):** Motor de teoria musical e gramática harmônica funcional. Mapeia escalas maiores e menores, deduz graus romanos ($I, ii, \dots, vii^\circ$), identifica Dominantes Secundárias ($V/X$) e valida regras de condução clássica estrita.
* **[`src/semantic.py`](src/semantic.py):** Validador semântico com mensagens didáticas e coordenadas de linha e coluna para cada erro diagnosticado (regras S1 a S17).
* **[`src/music.py`](src/music.py):** Conversões de altura em números MIDI ($0\text{ a }127$), cálculo de durações em *ticks* (resolução PPQ = 480) e síntese do arquivo `.mid` com canais independentes para melodia e harmonia.
* **[`src/main.py`](src/main.py):** Interface de linha de comando (CLI).

---

## 🚀 Pré-requisitos e Instalação

O projeto utiliza **Python 3.12+** e o gerenciador de pacotes e ambientes **[`uv`](https://docs.astral.sh/uv/)**.

### 1. Clonar o repositório

```bash
git clone https://github.com/raylandsoncesario/MusicLang.git
cd MusicLang
```

### 2. Sincronizar o ambiente com o `uv`

```bash
uv sync
```

---

## 💻 Como Executar

### Compilar e Gerar o Arquivo MIDI

Para compilar um programa `.music` e produzir o arquivo `.mid`:

```bash
uv run python -m src.main examples/canon_in_d.music
```

Saída:
```text
MusicLang Compiler

Source: examples/canon_in_d.music

[1/4] Lexical analysis........ OK
[2/4] Syntax analysis......... OK
[3/4] Semantic analysis....... OK
[4/4] MIDI generation......... OK

Music:      Canon in D
Tempo:      70 BPM
Key:        D major
Notes:      57
Chords:     25
Variations: 0
Output:     output/canon_in_d.mid
```

---

### Modos de Depuração e Inspeção

#### 1. Inspecionar Tokens (`--tokens`)
```bash
uv run python -m src.main --tokens examples/simple.music
```

#### 2. Visualizar a Árvore Sintática Abstrata (`--ast`)
```bash
uv run python -m src.main --ast examples/canon_in_d.music
```
Saída:
```text
Music(name="Canon in D")
├── Tempo(70)
├── Key(D, major)
├── Harmony
│   ├── Chord(D, 1/2)
│   ├── Chord(A, 1/2)
│   ├── Chord(Bm, 1/2)
│   ├── ...
├── Melody
│   ├── Note(F#4, 1/2)
│   ├── Note(E4, 1/2)
│   ├── ...
└── Output("output/canon_in_d.mid")
```

#### 3. Validar Sintaxe e Semântica sem gerar MIDI (`--check`)
```bash
uv run python -m src.main --check examples/harmony_valid.music
```

---

## 🎼 Sintaxe da Linguagem MusicLang

Um programa MusicLang é delimitado pelo bloco `music "<Nome>" { ... }` e aceita os seguintes elementos:

```music
music "Exemplo de Musica" {
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
        E4 1/4
        G4 1/4
        C5 1/4
        rest 1/4
        G4 1/4
        E4 1/4
        C4 1/4
    }

    variation {
        transpose +2
    }

    output "output/exemplo.mid"
}
```

### Elementos da Linguagem

| Declaração | Sintaxe | Descrição |
| :--- | :--- | :--- |
| **`tempo`** | `tempo <BPM>` | Define o andamento em batidas por minuto ($20 \le \text{BPM} \le 300$). Padrão: 120. |
| **`key`** | `key <PITCH> <major\|minor>` | Tonalidade da música (ex: `key C major`, `key D major`, `key A minor`). |
| **`harmony`** | `harmony { <CHORD> <DURACAO> ... }` | Sequência harmônica funcional com cifras e durações. |
| **`melody`** | `melody { <NOTA\|REST> <DURACAO> ... }` | Melodia principal com notas (`C4`, `F#3`) ou pausas (`rest`). |
| **`variation`** | `variation { <TRANSFORMACAO> ... }` | Transformações musicais (`transpose +2`, `octave -1`, `repeat 2`, `reverse`, `invert`). |
| **`output`** | `output "<arquivo.mid>"` | Caminho de destino do arquivo MIDI compilado (obrigatório terminar em `.mid`). |

### Durações Musicais

As durações são expressas como frações de tempo:
* `1/1` = Semibreve (1 compasso inteiro em 4/4 = 4 tempos)
* `1/2` = Mínima (2 tempos)
* `1/4` = Semínima (1 tempo)
* `1/8` = Colcheia (meio tempo)
* `1/16` = Semicolcheia (um quarto de tempo)

---

## 🎯 Análise e Validação de Harmonia Funcional

O compilador MusicLang implementa a **Gramática de Harmonia Funcional Clássica Estrita**:

```
 [Início da Música] ──► Tônica (I, vi, iii)
                           │
                           ├──► Subdominante (IV, ii) ──► Dominante (V, V7, vii°) ──┐
                           │          │                          │                  │
                           │          ▼                          ▼                  ▼
                           ├──► Dominante Secundária (V/X) ──► Alvo (X) ──► Tônica (I) [Resolução]
                           │                                                        ▲
                           └────────────────────────────────────────────────────────┘
```

### Classificação de Funções e Graus

| Grau (Maior / Menor) | Acordes Aceitos | Função Harmônica | Papel Funcional |
| :--- | :--- | :--- | :--- |
| **I / i** | `C`, `Cmaj7` / `Am`, `Am7` | **Tônica (T)** | Repouso pleno, centro tonal da música. |
| **ii / ii°** | `Dm`, `Dm7` / `Bdim`, `Bm7b5` | **Subdominante (S)** | Afastamento, preparação da dominante ($ii \to V$). |
| **iii / III** | `Em`, `Em7` / `C`, `Cmaj7` | **Tônica (T)** | Mediante, compartilhamento de notas da tônica. |
| **IV / iv** | `F`, `Fmaj7` / `Dm`, `Dm7` | **Subdominante (S)** | Movimento, afastamento moderado. |
| **V** | `G`, `G7` / `E`, `E7` | **Dominante (D)** | Tensão máxima, atração para resolver no grau I. |
| **vi / VI** | `Am`, `Am7` / `F`, `Fmaj7` | **Tônica Relativa (T)** | Repouso relativo, alvo de cadência de engano. |
| **vii°** | `Bdim`, `Bm7b5` / `G#dim` | **Dominante (D)** | Tensão alta (contém o trítono tonal). |
| **V/X ($D_{sec}$)** | `D7` ($V/V$), `A7` ($V/ii$), `E7` ($V/vi$), `C7` ($V/IV$) | **Dominante Secundária** | Tensão artificial direcionada obrigatoriamente ao grau alvo $X$. |

### Regras de Condução Estrita:
1. **Proibição de Retrogradação ($D \to S$):** O compilador rejeita movimentos de Dominante para Subdominante (ex: $V \to IV$, como `G7 -> F`), pois violam o encadeamento clássico de tensão $\to$ resolução.
2. **Resolução de Dominantes Secundárias:** Se um acorde $V/X$ for utilizado (ex: `D7` em Dó Maior, que é $V/V$), o próximo acorde **deve obrigatoriamente** ser o grau $X$ (`G` ou `G7`).
3. **Resolução Final Conclusiva:** A progressão deve terminar na **Tônica (grau I)** para fechar o ciclo harmônico.

---

## 🛑 Catálogo de Erros Semânticos (S1 a S17)

Cada erro semântico possui código e mensagem explicativa com cursor visual indicando o local exato:

| Código | Descrição da Regra |
| :--- | :--- |
| **S1** | Tempo fora da faixa permitida ($20 \le \text{BPM} \le 300$). |
| **S2** | Oitava de nota fora da faixa permitida ($0 \le \text{oitava} \le 9$). |
| **S3** | Altura gera número MIDI fora do limite ($0 \le \text{MIDI} \le 127$). |
| **S4 / S12** | Duração inválida (numerador $< 1$ ou denominador não pertencente a $\{1, 2, 4, 8, 16, 32\}$). |
| **S5** | Declaração duplicada (cada bloco/declaração pode aparecer no máximo uma vez). |
| **S6** | Falta da declaração obrigatória `output`. |
| **S7** | Falta do bloco obrigatório `melody` ou bloco `melody` vazio. |
| **S8** | Repetição inválida em variação (`repeat` deve ser $\ge 1$). |
| **S9** | Transposição fora do limite permitido ($-24 \le \text{transpose} \le +24$ semitons). |
| **S10** | Mudança de oitava fora do limite ($-4 \le \text{octave} \le +4$ oitavas). |
| **S11** | Arquivo de saída não possui extensão `.mid`. |
| **S13** | Bloco `harmony` vazio ou contendo apenas pausas. |
| **S14** | Acorde estranho à tonalidade (não pertence ao campo harmônico nem é dominante secundária válida). |
| **S15** | Violação de condução funcional clássica: retrogradação harmônica de Dominante para Subdominante. |
| **S16** | Dominante secundária não resolvida no acorde alvo esperado. |
| **S17** | Progressão harmônica incompleta (não finaliza na função Tônica / grau I). |

---

## 📂 Exemplos Incluídos

* **[`examples/canon_in_d.music`](examples/canon_in_d.music):** O famoso *Canon in D* de Johann Pachelbel em Ré Maior, com 3 variações rítmicas autênticas (tema em mínimas, variação em semínimas e cascata barroca em colcheias) sincronizadas com o baixo ostinato de 8 acordes.
* **[`examples/harmony_valid.music`](examples/harmony_valid.music):** Progressão funcional completa demonstrando cadência com dominante secundária e cadência deceptiva ($I \to IV \to V7/V \to V7 \to vi \to ii \to V7 \to I$).
* **[`examples/harmony_error_retrograde.music`](examples/harmony_error_retrograde.music):** Exemplo inválido que dispara o erro **S15** (tentativa de retrogradação $G7 \to F$).
* **[`examples/simple.music`](examples/simple.music):** Exemplo mínimo para testes de compilação rápida.

---

## 🎧 Como Escutar os Arquivos MIDI Gerados

Como arquivos MIDI contêm apenas mensagens de eventos e notas, utilize um reprodutor com suporte a sintetizador:

1. **Reprodutores no Terminal / Sistema (Linux):**
   ```bash
   # Via VLC
   vlc output/canon_in_d.mid

   # Via MPV
   mpv output/canon_in_d.mid
   ```
2. **Navegador Web (Sem instalar nada):**
   * Arraste o arquivo `.mid` para o **[Signal MIDI Editor](https://signal.vercel.app/)** ou **[Online MIDI Player](https://midi-player.net/)**.
3. **DAWs e Notação Musical:**
   * Abra o arquivo no **MuseScore**, **Reaper**, **FL Studio**, **Ableton Live** ou **GarageBand**.

---

## 🧪 Testes Automatizados

A suíte de testes cobre a análise léxica de acordes, o parser LL(1), a teoria harmônica e todas as regras de validação funcional.

Para executar todos os testes:

```bash
uv run pytest -v
```

---

## 📁 Estrutura do Repositório

```
MusicLang/
├── DOCS/                              # Documentos de especificação e planos do projeto
│   ├── Acorde.php                     # Referência de formação de acordes por intervalos
│   └── MusicLang — Plano...pdf        # Plano completo de arquitetura do compilador
├── docs/                              # Documentação formal da gramática
│   ├── grammar.md                     # Gramática BNF e tabela LL(1)
│   └── first-follow.md                # Cálculo detalhado dos conjuntos FIRST e FOLLOW
├── examples/                          # Arquivos de exemplo .music
│   ├── canon_in_d.music               # Canon in D de Pachelbel
│   ├── harmony_valid.music            # Cadência funcional clássica válida
│   ├── harmony_error_retrograde.music # Exemplo disparando erro semântico S15
│   └── simple.music                   # Exemplo básico
├── src/                               # Código-fonte do compilador
│   ├── __init__.py
│   ├── ast.py                         # Nós da Árvore Sintática Abstrata
│   ├── errors.py                      # Classes de erros léxicos, sintáticos e semânticos
│   ├── harmony.py                     # Teoria musical e gramática harmônica funcional
│   ├── lexer.py                       # Analisador léxico manual (tokens e autômato)
│   ├── main.py                        # Ponto de entrada CLI
│   ├── music.py                       # Modelo musical e gerador de arquivos MIDI
│   ├── parser.py                      # Analisador sintático preditivo LL(1) por tabela
│   └── semantic.py                    # Analisador semântico e regras S1 a S17
├── tests/                             # Suíte de testes automatizados
│   ├── __init__.py
│   └── test_harmony.py                # Testes unitários de harmonia, parser, lexer e semântica
├── pyproject.toml                     # Configuração do projeto e dependências (uv)
├── uv.lock                            # Lockfile reproduzível do uv
└── README.md                          # Documentação principal do projeto
```
