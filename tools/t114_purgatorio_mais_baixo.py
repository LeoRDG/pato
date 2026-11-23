"""Tarefa 114: Purgatório mais baixo: a escada de pontes (10 pontes, 9 vãos) passa a ter 4 vãos.

A escada é a instância de tiles_purgatorio_ponte com 10 pontes (uma a cada 4 linhas). Some uma faixa horizontal do
nível inteiro com a altura dos 5 vãos de baixo (20 linhas de 64 px = 1280 px), começando na 5ª ponte: nessa faixa
todas as linhas do tilemap principal têm os mesmos tiles cheios e vazios (parede, poço, pilar, área aberta, parede;
muda só a variação do desenho da borda), então nada além da altura
muda. Em cada tilemap as linhas dentro da faixa saem; tilemap que começa abaixo da faixa sobe 1280 px.
Instâncias da camada do mundo: as que ficam dentro da faixa (moedas dos vãos tirados) saem, as de baixo sobem
1280 px. O fundo (camada Fundo, parallax) e o HUD não mudam. Nada nos eventos da cena usa posição fixa; saida_y e retorno_y ficam acima da faixa.
Rodar uma vez:  python3 tools/t114_purgatorio_mais_baixo.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAOS_FICAM = 4


def tm(i):
    return next(s for s in i['stringProperties'] if s['name'] == 'tilemap')


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cena = next(l for l in d['layouts'] if l['name'] == 'Purgatorio')
    escadas = []
    for i in cena['instances']:
        if i['name'] == 'tiles_purgatorio_ponte':
            t = json.loads(tm(i)['value'])
            linhas = [r for r, row in enumerate(t['layers'][0]['tiles']) if any(v >= 0 for v in row)]
            if len(linhas) > VAOS_FICAM + 1:
                escadas.append((i, t, linhas))
    if not escadas:
        sys.exit('t114 já foi aplicada (escada já tem no máximo 4 vãos); não roda de novo.')
    assert len(escadas) == 1, len(escadas)
    esc, t, linhas = escadas[0]
    assert len(linhas) == 10, linhas
    ts = t['tileHeight']
    corte_y = esc['y'] + linhas[VAOS_FICAM] * ts            # onde a faixa começa (5ª ponte)
    altura = (linhas[-1] - linhas[VAOS_FICAM]) * ts          # 5 vãos
    assert altura == 1280, altura

    novas = []
    for i in cena['instances']:
        sp = next((s for s in i.get('stringProperties', []) if s['name'] == 'tilemap'), None)
        if i['layer'] != '':
            novas.append(i)
            continue
        if sp is not None:
            m = json.loads(sp['value'])
            th = m['tileHeight']
            r0 = round((corte_y - i['y']) / th)               # primeira linha da faixa neste tilemap
            n = altura // th
            if r0 <= 0:                                        # o tilemap todo está abaixo da faixa
                assert i['y'] >= corte_y + altura - th / 2, (i['name'], i['y'])
                i['y'] -= altura
            elif r0 < m['dimY']:
                tiles = m['layers'][0]['tiles']
                fora = tiles[r0:r0 + n]
                if i is not esc:                               # fora da escada a faixa tem que ser uniforme
                    cheio = lambda row: [v >= 0 for v in row]   # (só muda a variação do desenho da borda)
                    assert all(cheio(row) == cheio(tiles[r0]) for row in fora), (i['name'], i['y'])
                del tiles[r0:r0 + n]
                m['dimY'] = len(tiles)
                sp['value'] = json.dumps(m, separators=(',', ':'))
            novas.append(i)
            continue
        if i['y'] < corte_y - 32:
            novas.append(i)
        elif i['y'] >= corte_y + altura - 32:
            i['y'] -= altura
            novas.append(i)
        # dentro da faixa: sai
    print(len(cena['instances']) - len(novas), 'instâncias tiradas da faixa; corte em y', corte_y, 'altura', altura)
    cena['instances'] = novas

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('Purgatório mais baixo')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
