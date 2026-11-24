"""Tarefa 157: na luta com Deus as bordas da tela viram paredes, para o ricochete funcionar nelas.

Quatro parede_tela (sprite invisível no grupo Terreno, sem comportamento de plataforma, então o voo do pato não muda)
nascem no começo da luta, cada uma um quadrado de parede_tamanho logo além de uma borda da tela (lado 1 esquerda,
2 direita, 3 em cima, 4 embaixo), e acompanham a câmera. Como são Terreno, as balas com ricochete quicam nelas e as
outras param nelas, como numa parede. Fora da luta elas somem.
Só adiciona; a variável de cena que já existir fica com o valor atual.
Rodar uma vez:  python3 tools/t157_paredes_da_tela.py
"""
from gd_mig import *

ids = Ids('t157')
P = 'parede_tela'
IMG = 'assets/paraiso/parede.png'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
T = 'parede_tamanho'
RES = 'ResizableCapability::ResizableBehavior::'
LADOS = {'1': (f'{CX} - {CW} / 2 - {T}', f'{CY} - {T} / 2'),
         '2': (f'{CX} + {CW} / 2', f'{CY} - {T} / 2'),
         '3': (f'{CX} - {T} / 2', f'{CY} - {CH} / 2 - {T}'),
         '4': (f'{CX} - {T} / 2', f'{CY} + {CH} / 2')}


def migra(d):
    poe_recursos(d, [IMG])
    poe_objeto(d, sprite(ids, P, [('idle', [IMG], 1, 0.1, False)], [var(ids, P, 'lado', 0)]), 'inimigos/chefe')
    terreno = next(g for g in d['objectsGroups'] if g['name'] == 'Terreno')
    if P not in [x['name'] for x in terreno['objects']]:
        terreno['objects'].append({'name': P})
    c = cena(d, 'Paraiso')
    poe_vars(ids, c['variables'], 'Paraiso', [(T, 2000), ('parede_n', 0)])

    # uma por volta do Repeat: num evento só, o Create junta a nova às já escolhidas e o lado ia para todas
    nasce = repete(str(len(LADOS)), [
        X('SetNumberVariable', 'parede_n', '+', '1'), X('Create', '', P, '0', '0', '""'),
        setn(P, 'lado', '=', 'parede_n'), X('Hide', P),
        X(RES + 'SetWidth', P, 'Resizable', '=', T), X(RES + 'SetHeight', P, 'Resizable', '=', T)])
    grupo_ = grupo('Paredes da tela', [
        ev([cbol('luta', True), X('SceneInstancesCount', '', P, '=', '0')],
           [X('SetNumberVariable', 'parede_n', '=', '0')], [nasce]),
        *[ev([cbol('luta', True), num(P, 'lado', '=', lado)], [X('SetXY', P, '=', x, '=', y)])
          for lado, (x, y) in LADOS.items()],
        ev([cbol('luta', False), X('SceneInstancesCount', '', P, '>', '0')], [X('Delete', P, '')]),
    ])
    k = next(i for i, e in enumerate(c['events']) if e.get('name') == 'Voo do pato')
    c['events'].insert(k + 1, grupo_)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, P) is not None, 't157')
