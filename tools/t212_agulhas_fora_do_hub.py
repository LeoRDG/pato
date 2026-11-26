"""Tarefa 212: sem agulhas/pilares de rocha no HubPurgatorio (lado de fora, com a serra).

As agulhas de longe.png e pilares.png foram repintadas pontudas (tools/arte_agulhas_purgatorio.py) e continuam na fase.
No hub:
- sai a instância de bg_purgatorio_pilares;
- a instância de bg_purgatorio_longe é trocada, no mesmo lugar da lista (a serra continua logo depois dela), com a
  mesma posição, tamanho, camada e zOrder, por uma de bg_purgatorio_longe_hub: objeto novo (TiledSprite, pasta
  cenario) com assets/purgatorio/fundo/longe_hub.png, a mesma névoa com os fachos de luz, sem agulhas. A variável
  parallax_extra dele começa com o valor atual da de bg_purgatorio_longe, e o evento do hub que anda com o fundo
  ganha as mesmas duas ações de XOffset/YOffset para ele.
Os objetos bg_purgatorio_longe e bg_purgatorio_pilares, a fase Purgatorio, portais, placar, loja, mercador e serra
não mudam.
Rodar uma vez:  python3 tools/t212_agulhas_fora_do_hub.py
"""
from gd_mig import *

IMG = 'assets/purgatorio/fundo/longe_hub.png'
NOVO = 'bg_purgatorio_longe_hub'
HUB = 'HubPurgatorio'


def migra(d):
    ids = Ids('t212')
    longe = objeto(d, 'bg_purgatorio_longe')
    extra = next(v['value'] for v in longe['variables'] if v['name'] == 'parallax_extra')
    poe_recursos(d, [IMG])
    poe_objeto(d, tiled(ids, NOVO, IMG, longe['width'], longe['height'], [var(ids, NOVO, 'parallax_extra', extra)]),
               'cenario')

    c = cena(d, HUB)
    insts = c['instances']
    pilares = [i for i in insts if i['name'] == 'bg_purgatorio_pilares']
    for i in pilares:
        insts.remove(i)
    velhas = [i for i in insts if i['name'] == 'bg_purgatorio_longe']
    for i in velhas:
        k = insts.index(i)
        nova = dict(i, name=NOVO, persistentUuid=ids(f'inst/{HUB}/{k}'))
        insts[k] = nova
    print(f'hub: {len(pilares)} pilares removido(s), {len(velhas)} longe trocado(s)')

    for e in todos(c['events']):
        acoes = e.get('actions') or []
        for a in list(acoes):
            t = a['type']['value']
            if t in ('TiledSpriteObject::XOffset', 'TiledSpriteObject::YOffset') and a['parameters'][0] == 'bg_purgatorio_longe':
                p = [NOVO] + [x.replace('bg_purgatorio_longe.', NOVO + '.') for x in a['parameters'][1:]]
                if not any(b['type']['value'] == t and b['parameters'][0] == NOVO for b in acoes):
                    acoes.insert(acoes.index(a) + 1, X(t, *p))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, NOVO) is not None, 't212')
