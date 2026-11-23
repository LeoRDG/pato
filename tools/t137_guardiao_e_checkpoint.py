"""Tarefa 137: ofanim guardião, barreira de luz e checkpoint do Empíreo (chefe final, parte 1).

1. O ofanim do Paraíso (variável de instância guardiao = True) vira o guardião do Empíreo: barra de chefe (entra no
   grupo Chefes; a barra agora só aparece para quem tem barra_ativa = True, então os outros ofanins ficam sem barra),
   vida * guardiao_vida_mult uma vez, firme (não cambaleia), e abaixo de guardiao_fase_abaixo da vida fica aberto e
   fechado por menos tempo (* guardiao_aberto_fator). Morto, liga guardiao_morto (variável da cena).
2. No alto do Paraíso, uma parede de luz (barreira_empireo, sólida, no grupo Terreno) fecha o caminho para a saída
   enquanto o guardião vive. A saída só termina a fase com chefe_final_morto.
3. Antes da barreira, o checkpoint do Empíreo: com o guardião morto, tocar nele dá as asas (pato.asas, só visuais;
   asas_pato segue o pato) e grava o ponto de volta waypoints.Paraiso (ativo, x, y e guardiao). Voltando do hub
   para esse ponto, o pato já começa com as asas, o guardião não aparece e a barreira some.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t137_guardiao_e_checkpoint.py
"""
from gd_mig import *

ids = Ids('t137')
CHAO = -4096                      # topo da nuvem do alto do Paraíso (tiles_ceu)
CHECK_X, CHECK_W = 10750, 192
BARREIRA_X, BARREIRA_W, BARREIRA_H = 11200, 66, 2048
PASTA_ART = 'assets/paraiso/deus'


def eventos_guardiao():
    g = 'ofanim'
    return grupo('Ofanim guardião', [
        cada(g, [bol(g, 'guardiao', True), bol(g, 'morto', False), bol(g, 'chefe_preparado', False)],
             [setb(g, 'chefe_preparado', True), setn(g, 'max_vida', '*', 'ofanim.guardiao_vida_mult'),
              setn(g, 'vida', '=', 'ofanim.max_vida'), setn(g, 'vida_controle', '=', 'ofanim.vida'),
              setb(g, 'barra_ativa', True), setb(g, 'firme', True)]),
        cada(g, [bol(g, 'guardiao', True), bol(g, 'morto', False), bol(g, 'guardiao_rapido', False),
                 cmp('ofanim.vida', '<', 'ofanim.max_vida * ofanim.guardiao_fase_abaixo')],
             [setb(g, 'guardiao_rapido', True), setn(g, 'aberto_tempo', '*', 'ofanim.guardiao_aberto_fator'),
              setn(g, 'fechado_tempo', '*', 'ofanim.guardiao_aberto_fator')]),
        ev([cbol('guardiao_morto', False), bol(g, 'guardiao', True), bol(g, 'morto', True)],
           [csetb('guardiao_morto', True)]),
    ])


def eventos_checkpoint():
    wp = 'waypoints[CurrentSceneName()]'
    cria_asas = X('Create', '', 'asas_pato', 'pato.X()', 'pato.Y()', '')
    return grupo('Checkpoint do Empíreo', [
        ev([X('DepartScene', ''), cbol(f'{wp}.guardiao', True)],
           [csetb('guardiao_morto', True), setb('pato', 'asas', True), cria_asas],
           [ev([bol('ofanim', 'guardiao', True)], [X('Delete', 'ofanim', '')])]),
        ev([cbol('guardiao_morto', True)], [X('Delete', 'barreira_empireo', '')]),
        ev([X('CollisionNP', 'pato', 'checkpoint_empireo', '', '', ''), cbol('guardiao_morto', True),
            bol('pato', 'asas', False), bol('pato', 'morto', False)],
           [setb('pato', 'asas', True), cria_asas, csetb(f'{wp}.ativo', True),
            csetn(f'{wp}.x', '=', 'checkpoint_empireo.CenterX()'), csetn(f'{wp}.y', '=', 'checkpoint_empireo.CenterY()'),
            csetb(f'{wp}.guardiao', True), som('som_luz.wav', 'checkpoint_empireo.som_volume'),
            anim('checkpoint_empireo', 'idle')]),
        ev([bol('pato', 'asas', True)],
           [X('ScalableCapability::ScalableBehavior::SetValue', 'asas_pato', 'Scale', '=', 'asas_pato.escala'),
            X('SetXY', 'asas_pato', '=', 'pato.CenterX() - asas_pato.Width() / 2', '=',
              'pato.CenterY() - asas_pato.Height() / 2 + asas_pato.dy'),
            X('ChangePlan', 'asas_pato', '=', 'pato.ZOrder() - 1')]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    cut = {v['name']: v['value'] for v in o['cutulu']['variables']}

    # objetos novos
    poe_recursos(d, quadros(f'{PASTA_ART}/checkpoint_empireo', 'idle', 8) + quadros(f'{PASTA_ART}/asas_pato', 'idle', 6)
                 + quadros(f'{PASTA_ART}/asas_pato', 'bater', 6) + [f'{PASTA_ART}/feixe.png'])
    poe_objeto(d, sprite(ids, 'checkpoint_empireo', [('idle', f'{PASTA_ART}/checkpoint_empireo', 8, 0.1, True)],
                         [var(ids, 'checkpoint_empireo', 'som_volume', 80)]), 'cenario')
    poe_objeto(d, sprite(ids, 'asas_pato', [('idle', f'{PASTA_ART}/asas_pato', 6, 0.12, True),
                                             ('bater', f'{PASTA_ART}/asas_pato', 6, 0.06, True)],
                         [var(ids, 'asas_pato', 'escala', 4), var(ids, 'asas_pato', 'dy', -10)]), 'jogador')
    bar = tiled(ids, 'barreira_empireo', f'{PASTA_ART}/feixe.png', BARREIRA_W, BARREIRA_W)
    bar['behaviors'] = [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False,
                         'platformType': 'NormalPlatform', 'yGrabOffset': 0}]
    poe_objeto(d, bar, 'cenario')
    poe_no_grupo(d, 'Terreno', 'barreira_empireo')

    # variáveis
    poe_vars(ids, o['ofanim']['variables'], 'ofanim', [
        ('guardiao', False), ('nome', 'OFANIM, O GUARDIÃO'), ('barra_ativa', False), ('barra_dist', cut['barra_dist']),
        ('barra_largura', cut['barra_largura']), ('barra_rastro_vel', cut['barra_rastro_vel']),
        ('chefe_preparado', False), ('guardiao_rapido', False), ('guardiao_vida_mult', 15),
        ('guardiao_aberto_fator', 0.6), ('guardiao_fase_abaixo', 0.5)])
    for chefe in ('demonio_chefe', 'cutulu'):
        poe_vars(ids, o[chefe]['variables'], chefe, [('barra_ativa', True)])
    poe_vars(ids, o['pato']['variables'], 'pato', [('asas', False)])
    poe_no_grupo(d, 'Chefes', 'ofanim')
    for nome in ('Paraiso', 'Teste'):
        poe_vars(ids, cena(d, nome)['variables'], nome, [('guardiao_morto', False)])
    wp = next(v for v in d['variables'] if v['name'] == 'waypoints')
    par = next(c for c in wp['children'] if c['name'] == 'Paraiso')
    poe_vars(ids, par['children'], 'waypoints.Paraiso', [('guardiao', False)])

    # instâncias
    lay = cena(d, 'Paraiso')
    of = [i for i in lay['instances'] if i['name'] == 'ofanim']
    assert len(of) == 1, 'esperava um ofanim no Paraíso'
    poe_vars(ids, of[0]['initialVariables'], 'inst/ofanim', [('guardiao', True)])
    z = next(i['zOrder'] for i in lay['instances'] if i['name'] == 'pato')
    lay['instances'].append(inst(ids, 'checkpoint_empireo', 'checkpoint', CHECK_X, CHAO - CHECK_W, z - 2))
    lay['instances'].append(inst(ids, 'barreira_empireo', 'barreira', BARREIRA_X, CHAO - BARREIRA_H, z - 1,
                                 w=BARREIRA_W, h=BARREIRA_H))

    # eventos
    ip = folha(d, 'InimigosParaiso')['events']
    k = next(i for i, e in enumerate(ip) if e.get('name') == 'Ofanim (roda de olhos)')
    ip.insert(k + 1, eventos_guardiao())
    barras = acha(folha(d, 'HUD')['events'], 'Barras de chefe')
    chefes = acha(barras['events'], 'Chefes')['events'][0]
    chefes['conditions'].insert(0, bol('Chefes', 'barra_ativa', True))
    saida = acha(lay['events'], 'Saída no Empíreo')
    sai = next(e for e in todos(saida['events']) if any(a['type']['value'] == 'Scene' for a in e['actions']))
    sai['conditions'].append(cbol('chefe_final_morto', True))
    k = next(i for i, e in enumerate(lay['events']) if e.get('name') == 'Saída no Empíreo')
    lay['events'].insert(k, eventos_checkpoint())


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'checkpoint_empireo') is not None, 't137')
