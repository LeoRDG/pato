"""Tarefa 140: anel de ouro, o olhar (chefe final, parte 4).

- Fragmentos de nuvem e pedra caem pela subida (nascem acima da tela a cada fragmento_intervalo e somem abaixo).
  Eles têm o comportamento de obstáculo de luz: a luz da pupila (luz_olhar) projeta a sombra deles.
- Golpe "olhar": mira (a luz da pupila cresce até olhar_raio_luz), trava (a pupila contrai, o olho carrega e um
  feixe fraco mostra de onde o raio sai) e varre (o feixe acende e gira olhar_varre_ang graus em olhar_varre s).
  O feixe queima o pato (olhar_dano) quando passa por ele, a não ser que um fragmento esteja entre a pupila e o pato
  (raio de visão contra os fragmentos): a única proteção é a sombra. Termina em fim_golpe.
- A aura ganha o efeito Godray (raios de luz), que a última tarefa intensifica por fase.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t140_anel_ouro.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t140')
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
d_ = 'deus'
T_GOLPE = 'deus.ObjectTimerElapsedTime("golpe")'


def fragmentos():
    return grupo('Fragmentos', [
        ev([cbol('luta', True), bol(d_, 'morto', False), timer(d_, 'fragmento', '>', 'deus.fragmento_intervalo')],
           [zera(d_, 'fragmento'),
            X('Create', '', 'fragmento',
              f'RandomInRange({CX} - {CW} / 2 + deus.fragmento_folga, {CX} + {CW} / 2 - deus.fragmento_folga)',
              f'{CY} - {CH} / 2 - deus.fragmento_acima', '""'),
            X('AnimatableCapability::AnimatableBehavior::SetName', 'fragmento', 'Animation', '=',
              '"f" + ToString(RandomInRange(1, 3))'),
            setn('fragmento', 'vy', '=', 'RandomInRange(deus.fragmento_vel_min, deus.fragmento_vel_max)'),
            X('ChangePlan', 'fragmento', '=', 'deus.fragmento_z')]),
        ev([cbol('luta', True)], [X('SetY', 'fragmento', '+', 'fragmento.vy * TimeDelta()')]),
        ev([cbol('luta', True), X('PosY', 'fragmento', '>', f'{CY} + {CH} / 2 + deus.fragmento_fora')],
           [X('Delete', 'fragmento', '')]),
    ])


def feixe():
    return [X('SetAngle', 'feixe_olhar', '=', 'ToDeg(deus.olhar_a) - 90'),
            X('ResizableCapability::ResizableBehavior::SetWidth', 'feixe_olhar', 'Resizable', '=', 'deus.olhar_largura * 2'),
            X('ResizableCapability::ResizableBehavior::SetHeight', 'feixe_olhar', 'Resizable', '=', 'deus.olhar_alcance'),
            X('SetXY', 'feixe_olhar', '=', 'deus.px + cos(deus.olhar_a) * deus.olhar_alcance / 2 - feixe_olhar.Width() / 2',
              '=', 'deus.py + sin(deus.olhar_a) * deus.olhar_alcance / 2 - feixe_olhar.Height() / 2')]


def olhar():
    no_golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'olhar')]
    dx, dy = '(pato.CenterX() - deus.px)', '(pato.CenterY() - deus.py)'
    queima = ev([bol('pato', 'invencivel', False), bol('pato', 'morto', False),
                 cmp(f'{dx} * cos(deus.olhar_a) + {dy} * sin(deus.olhar_a)', '>', '0'),
                 cmp(f'abs({dy} * cos(deus.olhar_a) - {dx} * sin(deus.olhar_a))', '<', 'deus.olhar_largura'),
                 NAO('RaycastToPosition', 'fragmento', 'deus.px', 'deus.py', 'pato.CenterX()', 'pato.CenterY()',
                     'olhar_rx', 'olhar_ry', '')],
                [setn('pato', 'vida', '-', 'deus.olhar_dano'), setb('pato', 'invencivel', True), zera('pato', 'iframes'),
                 sets('pato', 'ultimo_agressor', 'deus')])
    return grupo('Anel de ouro: o olhar', [
        ev([bol(d_, 'morto', False)], [X('SetXY', 'luz_olhar', '=', 'deus.px', '=', 'deus.py')]),
        ev([bol(d_, 'morto', False), txt(d_, 'etapa', '')], [luz.acao_raio_luz('luz_olhar', 'deus.olhar_raio_idle')]),
        ev(no_golpe + [txt(d_, 'etapa', '')],
           [sets(d_, 'etapa', 'mira'), zera(d_, 'golpe'), luz.acao_cor_luz('luz_olhar', 'deus.olhar_cor'),
            anim('deus_anel_ouro', 'cintila'), som('som_luz.wav', 'deus.som_volume')]),
        ev(no_golpe + [txt(d_, 'etapa', 'mira')],
           [luz.acao_raio_luz('luz_olhar', f'deus.olhar_raio_idle + (deus.olhar_raio_luz - deus.olhar_raio_idle) * min(1, {T_GOLPE} / deus.olhar_mira)')],
           [ev([timer(d_, 'golpe', '>', 'deus.olhar_mira')],
               [sets(d_, 'etapa', 'trava'), zera(d_, 'golpe'), setn(d_, 'olhar_fixo', '=', 'deus.olhar_ang'),
                setn(d_, 'olhar_dir', '=', 'RandomInRange(0, 1) * 2 - 1'),
                setn(d_, 'olhar_a', '=', 'deus.olhar_fixo - deus.olhar_dir * ToRad(deus.olhar_varre_ang) / 2'),
                anim(d_, 'contrai'), anim('deus_olho', 'carregar'),
                X('Create', '', 'feixe_olhar', 'deus.px', 'deus.py', '""'),
                X('ChangePlan', 'feixe_olhar', '=', 'deus.feixe_z'),
                X('OpacityCapability::OpacityBehavior::SetValue', 'feixe_olhar', 'Opacity', '=', 'deus.olhar_aviso_opacidade')]
               + feixe())]),
        ev(no_golpe + [txt(d_, 'etapa', 'trava')], feixe(),
           [ev([timer(d_, 'golpe', '>', 'deus.olhar_trava')],
               [sets(d_, 'etapa', 'varre'), zera(d_, 'golpe'), som('som_luz.wav', 'deus.som_volume'),
                X('OpacityCapability::OpacityBehavior::SetValue', 'feixe_olhar', 'Opacity', '=', 'deus.opacidade_max')])]),
        ev(no_golpe + [txt(d_, 'etapa', 'varre')],
           [setn(d_, 'olhar_a', '=',
                 f'deus.olhar_fixo + deus.olhar_dir * ToRad(deus.olhar_varre_ang) * (min(1, {T_GOLPE} / deus.olhar_varre) * 2 - 1) / 2')]
           + feixe(),
           [queima,
            ev([timer(d_, 'golpe', '>', 'deus.olhar_varre')],
               [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), X('Delete', 'feixe_olhar', ''),
                anim(d_, 'idle'), anim('deus_olho', 'idle'), anim('deus_anel_ouro', 'idle')])]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    frag = o['fragmento']
    if not any(b['type'] == luz.COMP_SOMBRA for b in frag['behaviors']):
        frag['behaviors'].append({'name': 'Sombra', 'type': luz.COMP_SOMBRA})
    poe_vars(ids, frag['variables'], 'fragmento', [('vy', 0)])
    aura = o['deus_aura']
    if not any(e['effectType'] == 'Godray' for e in aura['effects']):
        aura['effects'].append(efeito('Godray', 'Raios',
                                      {'lacunarity': 2.75, 'angle': 30, 'gain': 0.45, 'light': 30, 'x': 0, 'y': 0,
                                       'animationSpeed': 1, 'padding': 0}, bools={'parallel': True}))
    poe_vars(ids, o['deus']['variables'], 'deus', [
        ('etapa', ''), ('som_volume', 70), ('opacidade_max', 255),
        ('fragmento_intervalo', 0.8), ('fragmento_vel_min', 60), ('fragmento_vel_max', 170), ('fragmento_folga', 120),
        ('fragmento_acima', 200), ('fragmento_fora', 300), ('fragmento_z', 2610), ('feixe_z', 2620),
        ('olhar_mira', 1.3), ('olhar_trava', 0.6), ('olhar_varre', 1.5), ('olhar_varre_ang', 110),
        ('olhar_dano', 30), ('olhar_largura', 70), ('olhar_alcance', 2600), ('olhar_raio_idle', 260),
        ('olhar_raio_luz', 1500), ('olhar_cor', '255;226;150'), ('olhar_aviso_opacidade', 90),
        ('olhar_fixo', 0), ('olhar_dir', 1), ('olhar_a', 0)])
    for nome in ('Paraiso', 'Teste'):
        poe_vars(ids, cena(d, nome)['variables'], nome, [('olhar_rx', 0), ('olhar_ry', 0)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Janela aberta')
    deus['events'][k:k] = [fragmentos(), olhar()]


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Anel de ouro: o olhar') is not None, 't140')
