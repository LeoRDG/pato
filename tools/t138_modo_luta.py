"""Tarefa 138: modo de luta no alto do Paraíso (chefe final, parte 2).

Com as asas (checkpoint do Empíreo) e o guardião morto, chegar na área da saída começa a luta (luta = True):
- o pato voa (o comportamento de plataforma e as câmeras suaves desligam): A/D e W/S (ou espaço) em 8 direções,
  com aceleração e freio, e um dash próprio no LShift (o dash de plataforma não funciona voando);
- a câmera sobe sozinha a subida_vel, presa em luta_x; o pato não sai pelo topo nem pelos lados;
- a borda de baixo da tela é a luz de Deus: encostar queima (borda_dano) e empurra para cima;
- a camada de luz Luz (escondida até a luta) acende com luz_ambiente_normal, e o pato leva uma luz (luz_pato);
- no fundo, o céu escurece (bg_ceu_alto) e vira espaço com estrelas (bg_espaco) conforme a subida;
- "Queda do céu" não roda na luta; deus_criar = True pede o Deus (próxima tarefa).
Com chefe_final_morto a luta acaba: tudo volta ao normal e a saída leva adiante.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t138_modo_luta.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t138')
P = 'assets/paraiso/deus'
CAM = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
CX, CY, CW, CH = CAM
FX, FY, FW, FH = (c.replace('""', '"Fundo"') for c in CAM)
SUBIDA = f'(luta_y0 - {CY})'


def tecla(t, *acoes):
    return ev([X('KeyFromTextPressed', '', f'"{t}"')], acoes)


def luta(sim=True):
    return cbol('luta', sim)


def vivo():
    return bol('pato', 'morto', False)


def comeco():
    return grupo('Começo da luta', [
        ev([bol('pato', 'asas', True), cbol('guardiao_morto', True), luta(False), cbol('chefe_final_morto', False),
            vivo(), cmp('pato.CenterX()', '>=', 'saida_x_min'), cmp('pato.CenterX()', '<=', 'saida_x_max'),
            cmp('pato.Y() + pato.Height()', '<=', 'saida_y')],
           [csetb('luta', True), csetb('deus_criar', True), csetn('luta_y0', '=', CY),
            X('ActivateBehavior', 'pato', 'PlatformerObject', 'no'),
            X('ActivateBehavior', 'pato', 'SmoothCamera', 'no'),
            X('ActivateBehavior', 'pato', 'SmoothPlatformerCamera', 'no'),
            setn('pato', 'voo_vx', '=', '0'), setn('pato', 'voo_vy', '=', '0'), zera('pato', 'voo_dash'),
            luz.acao_mostra_camada('"Luz"'), luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_normal'),
            X('Create', '', 'luz_pato', 'pato.CenterX()', 'pato.CenterY()', '"Luz"'),
            luz.acao_raio_luz('luz_pato', 'luz_pato_raio'),
            X('Create', '', 'queima_borda', CX, CY, '""'), X('ChangePlan', 'queima_borda', '=', 'queima_borda.z'),
            X('Create', '', 'bg_ceu_alto', FX, FY, '"Fundo"'), X('ChangePlan', 'bg_ceu_alto', '=', 'bg_ceu_alto.z'),
            X('Create', '', 'bg_espaco', FX, FY, '"Fundo"'), X('ChangePlan', 'bg_espaco', '=', 'bg_espaco.z'),
            anim('asas_pato', 'bater'), som('som_luz.wav', 'pato.voo_som_volume')]),
    ])


def voo():
    dash_livre = timer('pato', 'voo_dash', '>', 'pato.voo_dash_tempo')
    mexe = cmp('abs(pato.voo_ix) + abs(pato.voo_iy)', '>', '0')
    parado = cmp('abs(pato.voo_ix) + abs(pato.voo_iy)', '=', '0')
    alvo_x, alvo_y = 'pato.voo_ix * pato.voo_vel / pato.voo_norm', 'pato.voo_iy * pato.voo_vel / pato.voo_norm'
    return grupo('Voo do pato', [
        ev([luta(), vivo()], [setn('pato', 'voo_ix', '=', '0'), setn('pato', 'voo_iy', '=', '0')], [
            tecla('a', setn('pato', 'voo_ix', '-', '1')),
            tecla('d', setn('pato', 'voo_ix', '+', '1')),
            tecla('w', setn('pato', 'voo_iy', '=', '-1')),
            tecla('Space', setn('pato', 'voo_iy', '=', '-1')),
            tecla('s', setn('pato', 'voo_iy', '+', '1')),
            ev([], [setn('pato', 'voo_norm', '=', 'max(1, sqrt(pato.voo_ix * pato.voo_ix + pato.voo_iy * pato.voo_iy))')]),
        ]),
        ev([luta(), vivo(), dash_livre, mexe],
           [setn('pato', 'voo_vx', '+', f'({alvo_x} - pato.voo_vx) * min(1, pato.voo_acel * TimeDelta())'),
            setn('pato', 'voo_vy', '+', f'({alvo_y} - pato.voo_vy) * min(1, pato.voo_acel * TimeDelta())')]),
        ev([luta(), vivo(), dash_livre, parado],
           [setn('pato', 'voo_vx', '-', 'pato.voo_vx * min(1, pato.voo_freio * TimeDelta())'),
            setn('pato', 'voo_vy', '-', 'pato.voo_vy * min(1, pato.voo_freio * TimeDelta())')]),
        ev([luta(), vivo(), X('KeyFromTextJustPressed', '', '"LShift"'),
            timer('pato', 'voo_dash', '>', 'pato.voo_dash_espera'), mexe],
           [setn('pato', 'voo_vx', '=', 'pato.voo_ix * pato.voo_dash_vel / pato.voo_norm'),
            setn('pato', 'voo_vy', '=', 'pato.voo_iy * pato.voo_dash_vel / pato.voo_norm'),
            zera('pato', 'voo_dash'), som('som_dash.wav', 'pato.voo_som_volume')]),
        ev([luta(), vivo()],
           [X('SetX', 'pato', '+', 'pato.voo_vx * TimeDelta()'), X('SetY', 'pato', '+', 'pato.voo_vy * TimeDelta()'),
            X('SetX', 'pato', '=', f'clamp(pato.X(), {CX} - {CW} / 2, {CX} + {CW} / 2 - pato.Width())'),
            X('SetY', 'pato', '=', f'max(pato.Y(), {CY} - {CH} / 2)'),
            X('SetXY', 'luz_pato', '=', 'pato.CenterX()', '=', 'pato.CenterY()')]),
        ev([luta(), vivo(), bol('pato', 'em_dano', False)], [anim('pato', 'Pulo')]),
    ])


def camera():
    return grupo('Câmera da subida', [
        ev([luta(), cbol('chefe_final_morto', False)],
           [X('SetCameraCenterY', '', '=', f'{CY} - subida_vel * TimeDelta()', '""', '0'),
            X('SetCameraCenterX', '', '=', 'luta_x', '""', '0')]),
    ])


def borda():
    zona = cmp('pato.Y() + pato.Height()', '>', f'{CY} + {CH} / 2 - borda_altura')
    return grupo('Borda queimando', [
        ev([luta()],
           [X('SetXY', 'queima_borda', '=', f'{CX} - {CW} / 2', '=', f'{CY} + {CH} / 2 - queima_borda.Height()'),
            X('ResizableCapability::ResizableBehavior::SetWidth', 'queima_borda', 'Resizable', '=', CW),
            X('TiledSpriteObject::XOffset', 'queima_borda', '+', 'queima_borda.rolagem * TimeDelta()')]),
        ev([luta(), vivo(), zona], [setn('pato', 'voo_vy', '=', '-borda_empurrao')]),
        ev([luta(), vivo(), bol('pato', 'invencivel', False), zona],
           [setn('pato', 'vida', '-', 'borda_dano'), setb('pato', 'invencivel', True), zera('pato', 'iframes'),
            sets('pato', 'ultimo_agressor', 'deus'), setn('pato', 'voo_vy', '=', '-borda_empurrao'),
            som('som_pato_dano.wav', 'pato.voo_som_volume')]),
    ])


def ceu():
    k = f'clamp({SUBIDA} / altura_espaco, 0, 1)'
    acoes = []
    for bg in ('bg_ceu_alto', 'bg_espaco'):
        acoes += [X('SetXY', bg, '=', f'{FX} - {FW} / 2', '=', f'{FY} - {FH} / 2'),
                  X('ResizableCapability::ResizableBehavior::SetWidth', bg, 'Resizable', '=', FW),
                  X('ResizableCapability::ResizableBehavior::SetHeight', bg, 'Resizable', '=', FH),
                  X('TiledSpriteObject::YOffset', bg, '=', f'-{SUBIDA} * {bg}.parallax')]
    acoes += [X('OpacityCapability::OpacityBehavior::SetValue', 'bg_ceu_alto', 'Opacity', '=',
                f'clamp({k} / bg_ceu_alto.ate, 0, 1) * bg_ceu_alto.opacidade_max'),
              X('OpacityCapability::OpacityBehavior::SetValue', 'bg_espaco', 'Opacity', '=',
                f'clamp(({k} - bg_espaco.desde) / (1 - bg_espaco.desde), 0, 1) * bg_espaco.opacidade_max')]
    return grupo('Céu para o espaço', [ev([luta()], acoes)])


def fim():
    return grupo('Fim da luta', [
        ev([luta(), cbol('chefe_final_morto', True)],
           [csetb('luta', False), X('ActivateBehavior', 'pato', 'PlatformerObject', 'yes'),
            X('ActivateBehavior', 'pato', 'SmoothCamera', 'yes'),
            X('ActivateBehavior', 'pato', 'SmoothPlatformerCamera', 'yes'),
            luz.acao_esconde_camada('"Luz"'), X('Delete', 'luz_pato', ''), X('Delete', 'queima_borda', ''),
            anim('asas_pato', 'idle')]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_recursos(d, [f'{P}/queima_borda.png', f'{P}/bg_espaco.png', f'{P}/bg_ceu_alto.png'])
    q = tiled(ids, 'queima_borda', f'{P}/queima_borda.png', 192, 96,
              [var(ids, 'queima_borda', 'z', 5000), var(ids, 'queima_borda', 'rolagem', 120)])
    poe_objeto(d, q, 'efeitos')
    for nome, ate_desde in (('bg_ceu_alto', ('ate', 0.5)), ('bg_espaco', ('desde', 0.4))):
        bg = tiled(ids, nome, f'{P}/{nome}.png', 1026, 1026,
                   [var(ids, nome, 'z', 10 if nome == 'bg_ceu_alto' else 11), var(ids, nome, 'parallax', 0.12),
                    var(ids, nome, 'opacidade_max', 255), var(ids, nome, *ate_desde)])
        poe_objeto(d, bg, 'cenario/bg')
    lp = {'name': 'luz_pato', 'persistentUuid': ids('obj/luz_pato'), 'type': luz.OBJ_LUZ, 'variables': [],
          'effects': [], 'behaviors': [], 'assetStoreId': '', 'content': dict(luz.CONTEUDO_LUZ, radius=260)}
    poe_objeto(d, lp, 'efeitos')

    poe_vars(ids, o['pato']['variables'], 'pato', [
        ('voo_vel', 900), ('voo_acel', 10), ('voo_freio', 6), ('voo_dash_vel', 2300), ('voo_dash_tempo', 0.14),
        ('voo_dash_espera', 0.45), ('voo_som_volume', 60),
        ('voo_vx', 0), ('voo_vy', 0), ('voo_ix', 0), ('voo_iy', 0), ('voo_norm', 1)])
    lay = cena(d, 'Paraiso')
    v = vars_cena(d, 'Paraiso')
    poe_vars(ids, lay['variables'], 'Paraiso', [
        ('luta', False), ('deus_criar', False), ('luta_y0', 0), ('luta_x', (v['saida_x_min'] + v['saida_x_max']) / 2 - 576),
        ('subida_vel', 140), ('borda_dano', 20), ('borda_empurrao', 1100), ('borda_altura', 96),
        ('luz_ambiente_normal', '175;175;205'), ('luz_ambiente_escuro', '14;14;30'), ('luz_pato_raio', 260),
        ('altura_espaco', 9000)])
    poe_vars(ids, cena(d, 'Teste')['variables'], 'Teste', [('luta', False), ('deus_criar', False)])

    if not any(c['name'] == 'Luz' for c in lay['layers']):
        base = next(c for c in lay['layers'] if c['name'] == '')
        camada = {k: v for k, v in base.items() if k not in ('effects',)}
        camada.update(luz.CAMADA_LUZ, name='Luz', visibility=False, effects=[])
        lay['layers'].insert([c['name'] for c in lay['layers']].index('HUD'), camada)

    queda = acha(lay['events'], 'Queda do céu')
    for e in queda['events']:
        e['conditions'].insert(0, cbol('luta', False))
    k = next(i for i, e in enumerate(lay['events']) if e.get('name') == 'Saída no Empíreo')
    lay['events'][k + 1:k + 1] = [comeco(), voo(), camera(), borda(), ceu(), fim()]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'luz_pato') is not None, 't138')
