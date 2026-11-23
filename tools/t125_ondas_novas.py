"""Tarefa 125: ondas de chão novas (o desenho antigo era pequeno, parado e fraco).

- onda (pigman): 4 quadros em laço (onda_1..4, 72x48): lascas de pedra que irrompem do chão, com fenda de brasa na
  base, poeira atrás e cascalho voando. O pigman a cria com o centro 16 px acima dos pés, então o chão do desenho fica
  na linha 40; a máscara (x 6-66, y 4-36) para acima do chão para o projétil não sumir no Terreno.
- onda_abissal (cutulu, animação nova do projetil_inimigo): 4 quadros em laço (onda_abissal_1..4, 96x60): vagalhão de
  ícor do abismo com espuma, lábio curvado para a frente e tentáculos nas costas. O chão do desenho é a última linha;
  a máscara (x 6-90, y 6-52) para 8 px acima. As ondas da folha Cutulu passam a usar esta animação.
Só troca os quadros da animação onda e adiciona a onda_abissal; nada mais muda.
Rodar uma vez:  python3 tools/t125_ondas_novas.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = 'assets/inimigos/projeteis/'


def quadros(nome, mascara):
    x0, y0, x1, y1 = mascara
    return [{'hasCustomCollisionMask': True, 'image': f'{P}{nome}_{q}.png', 'points': [],
             'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
             'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0},
             'customCollisionMask': [[{'x': x0, 'y': y0}, {'x': x1, 'y': y0}, {'x': x1, 'y': y1},
                                      {'x': x0, 'y': y1}]]} for q in range(1, 5)]


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    proj = next(o for o in d['objects'] if o['name'] == 'projetil_inimigo')
    if any(a['name'] == 'onda_abissal' for a in proj['animations']):
        sys.exit('t125 já foi aplicada; não roda de novo.')
    rec = d['resources']['resources']
    for nome in ('onda', 'onda_abissal'):
        for q in range(1, 5):
            arq = f'{P}{nome}_{q}.png'
            if not any(r['name'] == arq for r in rec):
                rec.append({'file': arq, 'kind': 'image', 'metadata': '', 'name': arq, 'smoothed': False,
                            'userAdded': True})
    onda = next(a for a in proj['animations'] if a['name'] == 'onda')
    di = onda['directions'][0]
    di['sprites'] = quadros('onda', (6, 4, 66, 36))
    di['looping'] = True
    proj['animations'].append({'name': 'onda_abissal', 'useMultipleDirections': False,
                               'directions': [{'looping': True, 'timeBetweenFrames': di['timeBetweenFrames'],
                                               'sprites': quadros('onda_abissal', (6, 6, 90, 52))}]})
    folha = next(x for x in d['externalEvents'] if x['name'] == 'Cutulu')
    trocas = [0]

    def troca(evs):
        for e in evs:
            for a in e.get('actions', []):
                if a['type']['value'].endswith('SetName') and a['parameters'][:1] == ['projetil_inimigo'] \
                        and a['parameters'][3] == '"onda"':
                    a['parameters'][3] = '"onda_abissal"'
                    trocas[0] += 1
            troca(e.get('events') or [])
    troca(folha['events'])
    assert trocas[0] == 4, trocas

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('ondas novas; ondas do cutulu trocadas:', trocas[0])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
