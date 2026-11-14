"""Tarefa 46: o laser da mira vira upgrade da loja e o alvo (mira) fica escondido.

- Novo item no catálogo: id "laser" (1 nível); upgrades.laser = 0. O laser só é desenhado com upgrades.laser > 0.
- O objeto alvo continua existindo (o tiro mira nele, FireTowardObject), mas fica escondido (Hide todo quadro).
Rodar uma vez:  python3 tools/t46_laser_upgrade.py
"""
import json
from migra import carrega, salva, var, estrutura, adiciona_var, externo, C, A, E


def main():
    d = carrega()
    mira = next(e for e in externo(d, 'Jogador')['events'] if e.get('name') == 'Mira')['events']
    if 'upgrades.laser' in json.dumps(mira):
        print('já migrado'); return
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    if not any(c['value'] == 'laser' for i in cat['children'] for c in i['children'] if c['name'] == 'id'):
        cat['children'].append(estrutura(None, {'id': 'laser', 'nome': 'Laser',
                                                'descricao': 'Mira a laser: mostra para onde a arma aponta',
                                                'tipo': 'upgrade', 'nivel_max': 1, 'preco_base': 50, 'preco_mult': 1.6,
                                                'requer': ''}))
    adiciona_var(next(v for v in d['variables'] if v['name'] == 'upgrades')['children'], var('laser', 0))

    desenhos = [e for e in mira for e in [e, *(e.get('events') or [])]
                if any(a['type']['value'] == 'PrimitiveDrawing::LineV2' and a['parameters'][0] == 'laser' for a in e.get('actions') or [])]
    if len(desenhos) != 1:
        raise SystemExit(f'evento que desenha o laser: esperado 1, achei {len(desenhos)}; nada alterado')
    desenhos[0]['conditions'].append(C('BuiltinCommonInstructions::CompareNumbers', 'GlobalVariable(upgrades.laser)', '>', '0'))
    pos = next(e for e in mira if any(a['parameters'][:1] == ['alvo'] and a['type']['value'] == 'SetXY' for a in e.get('actions') or []))
    mira.insert(mira.index(pos) + 1, E([], [A('Hide', 'alvo', '')]))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
