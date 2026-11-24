"""Tarefa 188: loja do mercador.
- O E só funcionava pulando: a condição era Distance(trader, pato) de centro a centro, e o centro do mercador fica
  bem acima do do pato. Agora vale a distância na horizontal e a diferença de altura dos pés, as duas até
  trader.loja_raio (na dica do E e no E que abre a loja).
- O painel fica no meio da tela: x pelo meio de loja_largura, y pelo meio da lista + loja_desc_alt (altura reservada
  para a descrição, para o painel não pular quando ela muda de tamanho). loja_x/loja_y (canto de cima à esquerda)
  deixam de ser usados e saem dos hubs.
Rodar uma vez:  python3 tools/t188_loja_centro.py
"""
from gd_mig import *

HUBS = ('Hub', 'HubPurgatorio', 'HubParaiso')
X_MEIO = 'CameraBorderLeft("HUD") + (CameraWidth("HUD") - loja_largura + loja_desc_margem) / 2'
Y_MEIO = ('CameraBorderTop("HUD") + (CameraHeight("HUD") - GlobalVariableChildCount(loja_catalogo) * loja_linha_alt'
          ' - loja_desc_alt) / 2')
PERTO = [X('BuiltinCommonInstructions::CompareNumbers', 'abs(trader.CenterX() - pato.CenterX())', '<=',
           'trader.loja_raio'),
         X('BuiltinCommonInstructions::CompareNumbers',
           'abs(trader.Y() + trader.Height() - pato.Y() - pato.Height())', '<=', 'trader.loja_raio')]


def migra(d):
    ids = Ids('t188')
    for h in HUBS:
        vs = cena(d, h)['variables']
        poe_vars(ids, vs, h, [('loja_desc_alt', 60)])
        vs[:] = [v for v in vs if v['name'] not in ('loja_x', 'loja_y')]
    for e in todos(folha(d, 'Loja')['events']):
        cs = e.get('conditions', [])
        for i, c in enumerate(cs):
            if c['type']['value'] == 'Distance' and c['parameters'][:3] == ['trader', 'pato', 'trader.loja_raio']:
                cs[i:i + 1] = [json.loads(json.dumps(p)) for p in PERTO]
                break
        for a in e.get('actions', []):
            a['parameters'] = [p.replace('CameraBorderLeft("HUD") + loja_x', X_MEIO)
                                .replace('CameraBorderTop("HUD") + loja_y', Y_MEIO) for p in a['parameters']]


if __name__ == '__main__':
    roda(migra, lambda d: 'loja_x' not in {v['name'] for v in cena(d, 'Hub')['variables']}, 't188')
