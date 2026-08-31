<?php

namespace App\Support;

/**
 * Interpreta o nome de um acorde e devolve as notas que o formam.
 *
 * É a base dos diagramas: não há catálogo de acordes no banco — violão e
 * teclado são desenhados a partir daqui.
 */
class Acorde
{
    /** Semitom de cada tônica, contando de C = 0. */
    private const TONICAS = [
        'C' => 0, 'D' => 2, 'E' => 4, 'F' => 5, 'G' => 7, 'A' => 9, 'B' => 11,
    ];

    private const NOMES_SUSTENIDO = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

    private const NOMES_BEMOL = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

    /**
     * Intervalos de cada qualidade, em semitons a partir da tônica.
     *
     * A ordem importa: o primeiro sufixo que casar é o escolhido, então os
     * mais longos vêm antes dos mais curtos ("maj7" antes de "7").
     *
     * Nota sobre a notação brasileira: "A9" é lido como Aadd9 (tríade maior
     * com a nona), e não como acorde de nona dominante. É o uso corrente nas
     * cifras — para o dominante escreve-se "A7/9".
     *
     * @var array<string, array<int, int>>
     */
    private const QUALIDADES = [
        'm7b5' => [0, 3, 6, 10],
        'm7(b5)' => [0, 3, 6, 10],
        'maj7' => [0, 4, 7, 11],
        'maj9' => [0, 4, 7, 11, 2],
        '7maj' => [0, 4, 7, 11],
        '7M' => [0, 4, 7, 11],
        'M7' => [0, 4, 7, 11],
        'dim7' => [0, 3, 6, 9],
        'sus2' => [0, 2, 7],
        'sus4' => [0, 5, 7],
        '7sus4' => [0, 5, 7, 10],
        'add9' => [0, 4, 7, 2],
        'm11' => [0, 3, 7, 10, 2, 5],
        'm9' => [0, 3, 7, 10, 2],
        'm7' => [0, 3, 7, 10],
        'm6' => [0, 3, 7, 9],
        'mMaj7' => [0, 3, 7, 11],
        'dim' => [0, 3, 6],
        'aug' => [0, 4, 8],
        '+' => [0, 4, 8],
        '°' => [0, 3, 6],
        'º' => [0, 3, 6],
        '13' => [0, 4, 7, 10, 2, 9],
        '11' => [0, 4, 7, 10, 2, 5],
        '7/9' => [0, 4, 7, 10, 2],
        '7' => [0, 4, 7, 10],
        '6/9' => [0, 4, 7, 9, 2],
        '6' => [0, 4, 7, 9],
        '5' => [0, 7],
        '4' => [0, 5, 7],
        '2' => [0, 2, 7],
        '9' => [0, 4, 7, 2],
        'm' => [0, 3, 7],
        '' => [0, 4, 7],
    ];

    public readonly ?int $tonica;

    public readonly ?int $baixo;

    public readonly string $qualidade;

    /** @var array<int, int> semitons absolutos (0-11) */
    public readonly array $notas;

    public function __construct(public readonly string $nome)
    {
        $partes = $this->interpretar($nome);

        $this->tonica = $partes['tonica'];
        $this->baixo = $partes['baixo'];
        $this->qualidade = $partes['qualidade'];
        $this->notas = $partes['notas'];
    }

    public function valido(): bool
    {
        return $this->tonica !== null;
    }

    /**
     * Nomes das notas do acorde, na ordem tônica → extensões.
     *
     * @return array<int, string>
     */
    public function nomesDasNotas(): array
    {
        // A grafia segue o acidente da tônica: Bb usa bemóis, C# usa sustenidos.
        $tabela = str_starts_with(mb_substr($this->nome, 1), 'b') ? self::NOMES_BEMOL : self::NOMES_SUSTENIDO;

        return array_map(fn (int $semitom) => $tabela[$semitom], $this->notas);
    }

    /**
     * @return array{tonica: ?int, baixo: ?int, qualidade: string, notas: array<int, int>}
     */
    private function interpretar(string $nome): array
    {
        $nome = trim($nome);

        if (preg_match('/^([A-G])([#b]?)(.*)$/u', $nome, $partes) !== 1) {
            return ['tonica' => null, 'baixo' => null, 'qualidade' => '', 'notas' => []];
        }

        $tonica = (self::TONICAS[$partes[1]] + $this->acidente($partes[2])) % 12;
        $resto = $partes[3];
        $baixo = null;

        // Baixo invertido: D/F#
        if (preg_match('/^(.*)\/([A-G])([#b]?)$/u', $resto, $inversao) === 1) {
            $resto = $inversao[1];
            $baixo = (self::TONICAS[$inversao[2]] + $this->acidente($inversao[3])) % 12;
        }

        $qualidade = $this->qualidadeDe($resto);
        $intervalos = self::QUALIDADES[$qualidade];

        $notas = [];

        foreach ($intervalos as $intervalo) {
            $semitom = ($tonica + $intervalo) % 12;

            if (! in_array($semitom, $notas, true)) {
                $notas[] = $semitom;
            }
        }

        // O baixo invertido também soa
        if ($baixo !== null && ! in_array($baixo, $notas, true)) {
            $notas[] = $baixo;
        }

        return ['tonica' => $tonica, 'baixo' => $baixo, 'qualidade' => $qualidade, 'notas' => $notas];
    }

    private function acidente(string $sinal): int
    {
        return match ($sinal) {
            '#' => 1,
            'b' => -1 + 12,
            default => 0,
        };
    }

    /**
     * Escolhe a qualidade cujo sufixo casa com o texto — o mais longo primeiro.
     */
    private function qualidadeDe(string $resto): string
    {
        $resto = str_replace([' ', '(', ')'], '', $resto);

        if ($resto === '') {
            return '';
        }

        $candidatos = array_keys(self::QUALIDADES);

        usort($candidatos, fn ($a, $b) => mb_strlen($b) <=> mb_strlen($a));

        foreach ($candidatos as $sufixo) {
            if ($sufixo !== '' && str_starts_with($resto, str_replace(['(', ')'], '', $sufixo))) {
                return $sufixo;
            }
        }

        return '';
    }
}
