"""Tarefa 152: sai a borda de fogo da luta com Deus.

- O grupo "Borda queimando" (desenho, empurrão e dano) sai, e o Começo da luta não cria mais queima_borda.
- Sem a borda, o voo prende o pato dentro da tela também embaixo (antes só em cima).
O objeto queima_borda e as variáveis borda_* ficam no projeto, sem uso.
Rodar uma vez:  python3 tools/t152_sem_borda.py
"""
from gd_mig import *

CY, CH = 'CameraCenterY("", 0)', 'CameraHeight("", 0)'


def migra(d):
    c = cena(d, 'Paraiso')
    c['events'] = [e for e in c['events'] if e.get('name') != 'Borda queimando']
    comeco = acha(c['events'], 'Começo da luta')['events'][0]
    comeco['actions'] = [a for a in comeco['actions'] if 'queima_borda' not in json.dumps(a)]
    voo = acha(c['events'], 'Voo do pato')
    for e in todos(voo['events']):
        for a in e['actions']:
            if a['type']['value'] == 'SetY' and a['parameters'][0] == 'pato' and a['parameters'][2] == f'max(pato.Y(), {CY} - {CH} / 2)':
                a['parameters'][2] = f'clamp(pato.Y(), {CY} - {CH} / 2, {CY} + {CH} / 2 - pato.Height())'


if __name__ == '__main__':
    roda(migra, lambda d: acha(cena(d, 'Paraiso')['events'], 'Borda queimando') is None, 't152')
