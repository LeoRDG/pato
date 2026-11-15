"""Tarefa 64: o laser da mira volta a ser desenhado.

Na limpeza dos eventos do Jogador (commit fa484a6, "limpando eventos: controle das armas") o grupo Mira virou
"Controle das Armas > Mira e posicionamento", mas o pedaço que desenhava o laser ficou de fora: comprar o upgrade
(upgrades.laser) não mostrava nada. Esta migração de uso único só ADICIONA esse pedaço (igual ao que existia), no fim
do grupo "Cano e alvo", e só se ainda não houver um desenho do laser nos eventos do Jogador:
  - laser_x/laser_y = do cano até pato.laser_alcance na direção da mira;
  - um raio até o Terreno encurta o laser na primeira parede;
  - com GlobalVariable(upgrades.laser) > 0 desenha a linha no objeto laser.
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def I(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def evento():
    return {'type': 'BuiltinCommonInstructions::Standard', 'conditions': [],
            'actions': [I('SetNumberVariable', 'laser_x', '=', 'bocal_x + mira_lado * cos(mira_a) * pato.laser_alcance'),
                        I('SetNumberVariable', 'laser_y', '=', 'bocal_y + sin(mira_a) * pato.laser_alcance')],
            'events': [
                {'type': 'BuiltinCommonInstructions::Standard',
                 'conditions': [I('RaycastToPosition', 'Terreno', 'bocal_x', 'bocal_y', 'laser_x', 'laser_y', 'laser_x', 'laser_y', '')],
                 'actions': []},
                {'type': 'BuiltinCommonInstructions::Standard',
                 'conditions': [I('BuiltinCommonInstructions::CompareNumbers', 'GlobalVariable(upgrades.laser)', '>', '0')],
                 'actions': [I('PrimitiveDrawing::LineV2', 'laser', 'bocal_x', 'bocal_y', 'laser_x', 'laser_y', '1.5')]},
            ]}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def migra(d):
    jogador = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
    if any(a['type']['value'] == 'PrimitiveDrawing::LineV2' for e in todos(jogador) for a in e.get('actions') or []):
        return
    cano = next(e for e in todos(jogador) if e.get('name') == 'Cano e alvo')
    cano['events'].append(evento())


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
