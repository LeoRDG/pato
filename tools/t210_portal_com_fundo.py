"""Tarefa 210: portais com contraste: um disco escuro e macio atrás das partículas de cada portal.

As partículas dos portais (claras, na cor de cada fase) somiam na névoa cinza-esverdeada dos hubs e pareciam chapadas.
Objeto novo portal_fundo (pasta gatilhos): disco branco com a borda sumindo aos poucos (assets/portais/fundo.png,
gerado aqui), tingido no jogo com portal.cor_fundo. Na Abertura de cada portal ele é criado no centro do portal,
atrás das partículas (plano do portal; espiral e braços ficam em +1, núcleo em +2), com diâmetro 2 * portal.fundo_raio
e opacidade portal.fundo_opacidade; entra no grupo PortalEfeito (raio, giro e inclina 0), então flutua junto.
Variáveis novas no portal: cor_fundo (texto "r;g;b"), fundo_raio (px), fundo_opacidade (0-255). Nos portais dos hubs
cor_fundo é a cor da fase bem escura (Inferno brasa, Purgatório verde-água, Paraíso azul-noite).
Rodar uma vez:  python3 tools/t210_portal_com_fundo.py
"""
import numpy as np
from PIL import Image
from gd_mig import *

IMG = 'assets/portais/fundo.png'
LADO = 256
PORTAL_VARS = [('cor_fundo', '25;12;45'), ('fundo_raio', 150), ('fundo_opacidade', 170)]
COR_FUNDO = {'Inferno': '45;10;4', 'Purgatorio': '4;34;30', 'Paraiso': '12;22;60'}
HUBS = ('Hub', 'HubPurgatorio', 'HubParaiso')


def gera_imagem():
    """disco branco: opacidade cheia no meio, cai devagar e some na borda (sem degrau)."""
    caminho = os.path.join(RAIZ, IMG)
    if os.path.exists(caminho):
        return
    y, x = np.mgrid[0:LADO, 0:LADO] + 0.5
    r = np.hypot(x - LADO / 2, y - LADO / 2) / (LADO / 2)
    a = np.clip(1 - r ** 2, 0, 1) ** 2
    out = np.dstack([np.full((LADO, LADO, 3), 255.0), a * 255]).round().astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(caminho)


def migra(d):
    ids = Ids('t210')
    gera_imagem()
    if not any(r['name'] == IMG for r in d['resources']['resources']):
        d['resources']['resources'].append(dict(recurso(IMG), smoothed=True))
    o = sprite(ids, 'portal_fundo', [('fundo', [IMG], 1, 0.1, False)],
               variaveis=[var(ids, 'portal_fundo', n, 0) for n in
                          ('base_x', 'base_y', 'raio', 'ang_orb', 'giro', 'inclina', 'flutua_amp', 'flutua_vel', 'fase')])
    q = o['animations'][0]['directions'][0]['sprites'][0]
    q['originPoint'].update(x=LADO / 2, y=LADO / 2)     # X/Y do grupo PortalEfeito são o centro, como nas partículas
    poe_objeto(d, o, 'gatilhos')
    poe_no_grupo(d, 'PortalEfeito', 'portal_fundo')

    portal = objeto(d, 'portal')
    poe_vars(ids, portal['variables'], 'portal', PORTAL_VARS)
    for h in HUBS:
        for i in cena(d, h)['instances']:
            if i['name'] != 'portal':
                continue
            iv = i.setdefault('initialVariables', [])
            fase = next(v['value'] for v in iv if v['name'] == 'cena')
            if fase in COR_FUNDO and not any(v['name'] == 'cor_fundo' for v in iv):
                iv.append({'name': 'cor_fundo', 'type': 'string', 'value': COR_FUNDO[fase]})

    abre = acha(folha(d, 'Portais')['events'], 'Abertura')['events'][0]
    assert abre['type'].endswith('ForEach') and abre['object'] == 'portal'
    F = 'portal_fundo'
    abre['events'].insert(0, ev([], [
        X('Create', '', F, 'portal.CenterX()', 'portal.CenterY()', ''),
        X('ChangeColor', F, 'portal.cor_fundo'),
        X('ResizableCapability::ResizableBehavior::SetSize', F, 'Resizable', 'portal.fundo_raio * 2', 'portal.fundo_raio * 2'),
        X('OpacityCapability::OpacityBehavior::SetValue', F, 'Opacity', '=', 'portal.fundo_opacidade'),
        X('ChangePlan', F, '=', 'portal.ZOrder()'),
        setn(F, 'base_x', '=', 'portal.CenterX()'),
        setn(F, 'base_y', '=', 'portal.CenterY()'),
        setn(F, 'raio', '=', '0'),
        setn(F, 'ang_orb', '=', '0'),
        setn(F, 'giro', '=', '0'),
        setn(F, 'inclina', '=', '0'),
        setn(F, 'flutua_amp', '=', 'portal.flutua_amp'),
        setn(F, 'flutua_vel', '=', 'portal.flutua_vel'),
        setn(F, 'fase', '=', 'portal.fase'),
    ]))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'portal_fundo') is not None, 't210')
