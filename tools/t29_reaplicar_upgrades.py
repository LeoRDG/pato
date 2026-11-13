"""Tarefa 29: upgrades podem ser reaplicados no meio da cena (compra na loja) sem acumular a velocidade.

- Antes do 'Aplicar upgrades': no início da cena guarda pato.velocidade_base = MaxSpeed do comportamento (editável no GDevelop).
- O evento roda no início da cena OU quando pato.reaplicar_upgrades = verdadeiro (e desliga a variável).
- A velocidade passa a partir de pato.velocidade_base (antes multiplicava o MaxSpeed atual: acumulava ao rodar de novo).
Rodar uma vez:  python3 tools/t29_reaplicar_upgrades.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, externo, C, A, E

VELHO = 'pato.PlatformerObject::MaxSpeed() * (1 + pato.upg_velocidade * GlobalVariable(upgrades.velocidade))'
NOVO = 'pato.velocidade_base * (1 + pato.upg_velocidade * GlobalVariable(upgrades.velocidade))'


def main():
    d = carrega()
    grupo = next(e for e in externo(d, 'AplicarUpgrades')['events'] if e.get('name') == 'Aplicar upgrades')
    alvos = [e for e in grupo['events'] if any(a['type']['value'] == 'PlatformBehavior::MaxSpeed' for a in e.get('actions') or [])]
    assert len(alvos) == 1, 'evento Aplicar upgrades não encontrado uma única vez'
    alvo = alvos[0]
    if 'reaplicar_upgrades' in json.dumps(alvo['conditions']):
        print('já migrado'); return
    ms = next(a for a in alvo['actions'] if a['type']['value'] == 'PlatformBehavior::MaxSpeed')
    if ms['parameters'][-1] != VELHO:
        raise SystemExit('A fórmula da velocidade foi editada no GDevelop; não mexi em nada: ' + ms['parameters'][-1])

    base = E([C('SceneJustBegins', '')],
             [A('SetNumberObjectVariable', 'pato', 'velocidade_base', '=', 'pato.PlatformerObject::MaxSpeed()')])
    grupo['events'].insert(grupo['events'].index(alvo), base)
    ou = C('BuiltinCommonInstructions::Or')
    ou['subInstructions'] = [alvo['conditions'][0], C('BooleanObjectVariable', 'pato', 'reaplicar_upgrades', 'True', '')]
    assert alvo['conditions'][0]['type']['value'] == 'SceneJustBegins' and len(alvo['conditions']) == 1
    alvo['conditions'] = [ou]
    ms['parameters'][-1] = NOVO
    alvo['actions'].append(A('SetBooleanObjectVariable', 'pato', 'reaplicar_upgrades', 'False', ''))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
