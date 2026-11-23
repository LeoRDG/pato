"""Tarefa 147: correções visuais do chefe Deus, vistas com o jogo rodando no navegador.

- Fragmentos: máscara de colisão justa (casco convexo da pedra). O obstáculo de luz usa a máscara; com o retângulo
  inteiro a sombra saía quadrada e aparecia uma caixa clara em volta da pedra.
- Halos do piscar: no escuro do espaço a luz sozinha quase não aparecia. Cada luz_halo ganha um halo_marca (sprite
  halo.png) do tamanho da zona segura (deus.halo_raio * 2), ligado pelo id, que some junto com a luz.
- Três Anéis e a fase final: os tiros de luz ficam deus.aneis_escala vezes maiores (eram pontinhos).
- Deus mais alto na tela (distancia_baixo) e órbita dos canalizadores menor (canal_orbita_raio): a metade de baixo da
  órbita ficava fora da tela, atrás da borda que queima. Luz do halo maior (halo_raio_luz) para iluminar o halo todo.
  Esses três valores só mudam se ainda estiverem no valor inicial (se você mudou, ficam).
Rodar uma vez:  python3 tools/t147_visual_deus.py
"""
import os
import numpy as np
from PIL import Image
from gd_mig import *

ids = Ids('t147')
d_ = 'deus'
HALO = 'assets/paraiso/deus/halo.png'
NOVOS = {'distancia_baixo': (330, 150), 'canal_orbita_raio': (400, 260), 'halo_raio_luz': (190, 300)}


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def casco(caminho, max_pontos=12):
    """casco convexo dos pixels opacos (cadeia monótona), reduzido a no máximo max_pontos vértices."""
    a = np.array(Image.open(caminho).convert('RGBA'))[:, :, 3] > 0
    ys, xs = np.nonzero(a)
    pts = sorted({(int(x), int(y)) for x, y in zip(xs, ys)} | {(int(x) + 1, int(y) + 1) for x, y in zip(xs, ys)})

    def cruz(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    baixo, cima = [], []
    for p in pts:
        while len(baixo) >= 2 and cruz(baixo[-2], baixo[-1], p) <= 0:
            baixo.pop()
        baixo.append(p)
    for p in reversed(pts):
        while len(cima) >= 2 and cruz(cima[-2], cima[-1], p) <= 0:
            cima.pop()
        cima.append(p)
    h = baixo[:-1] + cima[:-1]
    passo = max(1, -(-len(h) // max_pontos))
    return h[::passo]


def migra(d):
    o = {x['name']: x for x in d['objects']}
    # fragmentos com máscara justa
    for a in o['fragmento']['animations']:
        for sp in a['directions'][0]['sprites']:
            sp['hasCustomCollisionMask'] = True
            sp['customCollisionMask'] = [[{'x': x, 'y': y} for x, y in casco(os.path.join(RAIZ, sp['image']))]]
    # halo visível
    poe_recursos(d, [HALO])
    poe_objeto(d, sprite(ids, 'halo_marca', [('idle', [HALO], 1, 0.1, False)], [var(ids, 'halo_marca', 'id', 0)]),
               'inimigos/chefe')
    poe_vars(ids, o['luz_halo']['variables'], 'luz_halo', [('id', 0)])
    poe_vars(ids, o[d_]['variables'], d_, [('halo_seq', 0), ('halo_marca_opacidade', 210), ('aneis_escala', 2)])
    for v in o[d_]['variables']:
        if v['name'] in NOVOS and v.get('value') == NOVOS[v['name']][0]:
            v['value'] = NOVOS[v['name']][1]
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    evs = list(todos(deus['events']))
    nasce = next(e for e in evs if '"Create"}, "parameters": ["", "luz_halo"' in tx(e.get('actions', [])))
    nasce['actions'] += [
        setn(d_, 'halo_seq', '+', '1'), setn('luz_halo', 'id', '=', 'deus.halo_seq'),
        X('Create', '', 'halo_marca', 'luz_halo.X()', 'luz_halo.Y()', '""'), setn('halo_marca', 'id', '=', 'deus.halo_seq'),
        X('ResizableCapability::ResizableBehavior::SetWidth', 'halo_marca', 'Resizable', '=', 'deus.halo_raio * 2'),
        X('ResizableCapability::ResizableBehavior::SetHeight', 'halo_marca', 'Resizable', '=', 'deus.halo_raio * 2'),
        X('OpacityCapability::OpacityBehavior::SetValue', 'halo_marca', 'Opacity', '=', 'deus.halo_marca_opacidade'),
        X('ChangePlan', 'halo_marca', '=', 'deus.feixe_z')]
    for e in evs:
        acts = e.get('actions', [])
        k = next((i for i, a in enumerate(acts)
                  if a['type']['value'] == 'Delete' and a['parameters'][0] == 'luz_halo'), None)
        if k is not None:
            acts.insert(k + 1, X('Delete', 'halo_marca', ''))
    azul = acha(deus['events'], 'Anel azul: piscar')
    azul['events'].append(cada('halo_marca', [num('luz_halo', 'id', '=', 'halo_marca.id')],
                               [X('SetXY', 'halo_marca', '=', 'luz_halo.X() - halo_marca.Width() / 2', '=',
                                  'luz_halo.Y() - halo_marca.Height() / 2')]))
    # tiros de luz maiores
    for g in ('Três anéis', 'Fase final'):
        for e in todos(acha(deus['events'], g)['events']):
            acts = e.get('actions', [])
            k = next((i for i, a in enumerate(acts)
                      if a['type']['value'] == 'Create' and a['parameters'][1] == 'projetil_inimigo'), None)
            if k is not None:
                acts.insert(k + 1, X('ScalableCapability::ScalableBehavior::SetValue', 'projetil_inimigo', 'Scale', '=',
                                     'deus.aneis_escala'))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'halo_marca') is not None, 't147')
