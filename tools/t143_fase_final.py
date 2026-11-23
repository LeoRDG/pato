"""Tarefa 143: Três Anéis, puxão e a fase final de Deus (chefe final, parte 7).

- Golpe "aneis" (Três Anéis): aneis_rodadas anéis de luz saem do olho, um a cada aneis_intervalo, cada um com um
  buraco (aneis_buraco_meio tiros a menos de cada lado) mirado perto do pato, por onde ele passa voando.
- Golpe "puxao": por puxao_tempo o olho puxa o pato para si (puxao_forca), contra a borda que queima e o corpo dele.
- Fase 4: os três anéis se soltam e orbitam o olho (orbita_raio, orbita_vel), girando rápido, e cada um atira
  sozinho, um de cada vez a cada aneis_final_intervalo, o seu próprio anel de luz com buraco; as pausas entre os
  golpes encurtam (fase4_pausa_fator).
- Os relógios do Deus começam na criação (comparar um relógio que nunca foi zerado não é confiável).
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t143_fase_final.py
"""
import re
from gd_mig import *

ids = Ids('t143')
d_ = 'deus'
ANEIS = ('deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa')


def tiros(x, y, qtd, vel, dano):
    """anel de projéteis de luz saindo de (x, y), começando em deus.i, ângulo a partir de deus.buraco_ang."""
    ang = f'deus.buraco_ang + deus.i * 360 / {qtd}'
    return [X('Create', '', 'projetil_inimigo', x, y, '""'),
            anim('projetil_inimigo', 'luz'),
            X('SetXY', 'projetil_inimigo', '=', f'{x} - projetil_inimigo.Width() / 2', '=', f'{y} - projetil_inimigo.Height() / 2'),
            X('AddForceAL', 'projetil_inimigo', ang, vel, '1'),
            X('SetAngle', 'projetil_inimigo', '=', ang),
            setn('projetil_inimigo', 'dano', '=', dano), sets('projetil_inimigo', 'origem', 'deus'),
            sets('projetil_inimigo', 'tipo', 'luz'), zera('projetil_inimigo', 'vida'),
            setn('projetil_inimigo', 'ttl', '=', 'deus.aneis_ttl'), setn(d_, 'i', '+', '1')]


def mira(x, y, desvio):
    return setn(d_, 'buraco_ang', '=', f'ToDeg(atan2(pato.CenterY() - {y}, pato.CenterX() - {x})) + RandomFloatInRange(-{desvio}, {desvio})')


def tres_aneis():
    no_golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'aneis')]
    return grupo('Três anéis', [
        ev(no_golpe + [txt(d_, 'etapa', '')],
           [sets(d_, 'etapa', 'aneis'), zera(d_, 'golpe'), setn(d_, 'aneis_feitos', '=', '0'), anim('deus_olho', 'carregar')]
           + [anim(a, 'cintila') for a in ANEIS]),
        ev(no_golpe + [txt(d_, 'etapa', 'aneis'), timer(d_, 'golpe', '>', 'deus.aneis_intervalo'),
                       cmp('deus.aneis_feitos', '<', 'deus.aneis_rodadas')],
           [zera(d_, 'golpe'), setn(d_, 'aneis_feitos', '+', '1'), mira('deus.cx', 'deus.cy', 'deus.aneis_desvio'),
            setn(d_, 'i', '=', 'deus.aneis_buraco_meio + 1'), som('som_luz.wav', 'deus.som_volume')],
           [repete('deus.aneis_qtd - 2 * deus.aneis_buraco_meio - 1',
                   tiros('deus.cx', 'deus.cy', 'deus.aneis_qtd', 'deus.aneis_vel', 'deus.aneis_dano'))]),
        ev(no_golpe + [txt(d_, 'etapa', 'aneis'), cmp('deus.aneis_feitos', '>=', 'deus.aneis_rodadas'),
                       timer(d_, 'golpe', '>', 'deus.aneis_fim')],
           [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), anim('deus_olho', 'idle')]
           + [anim(a, 'idle') for a in ANEIS]),
    ])


def puxao():
    no_golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'puxao')]
    a = 'atan2(deus.cy - pato.CenterY(), deus.cx - pato.CenterX())'
    return grupo('Puxão', [
        ev(no_golpe + [txt(d_, 'etapa', '')],
           [sets(d_, 'etapa', 'puxao'), zera(d_, 'golpe'), anim('deus_olho', 'carregar'), anim(d_, 'contrai'),
            som('som_luz.wav', 'deus.som_volume', 'deus.puxao_tom')]),
        ev(no_golpe + [txt(d_, 'etapa', 'puxao'), cbol('luta', True), bol('pato', 'morto', False)],
           [setn('pato', 'voo_vx', '+', f'cos({a}) * deus.puxao_forca * TimeDelta()'),
            setn('pato', 'voo_vy', '+', f'sin({a}) * deus.puxao_forca * TimeDelta()')]),
        ev(no_golpe + [txt(d_, 'etapa', 'puxao'), timer(d_, 'golpe', '>', 'deus.puxao_tempo')],
           [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), anim('deus_olho', 'idle'),
            anim(d_, 'idle')]),
    ])


def fase_final():
    f4 = [bol(d_, 'morto', False), num(d_, 'fase', '=', '4')]
    orbita = []
    for k, anel in enumerate(ANEIS):
        ang = f'deus.orbita_ang + {k} * deus.orbita_passo' if k else 'deus.orbita_ang'
        orbita += [X('SetXY', anel, '=', f'deus.cx + cos({ang}) * deus.orbita_raio - {anel}.Width() / 2', '=',
                     f'deus.cy + sin({ang}) * deus.orbita_raio - {anel}.Height() / 2'),
                   X('SetAngle', anel, '+', 'deus.anel_giro_final * TimeDelta()')]
    evs = [
        ev(f4 + [bol(d_, 'final_iniciado', False)],
           [setb(d_, 'final_iniciado', True), zera(d_, 'anel_final'), setn(d_, 'pausa_tempo', '*', 'deus.fase4_pausa_fator')]),
        ev(f4, [setn(d_, 'orbita_ang', '+', 'deus.orbita_vel * TimeDelta()')] + orbita),
    ]
    for k, anel in enumerate(ANEIS):
        x, y = f'{anel}.CenterX()', f'{anel}.CenterY()'
        evs.append(ev(f4 + [timer(d_, 'anel_final', '>', 'deus.aneis_final_intervalo'), num(d_, 'anel_vez', '=', str(k))],
                      [zera(d_, 'anel_final'), setn(d_, 'anel_vez', '=', str((k + 1) % 3)), anim(anel, 'cintila'),
                       mira(x, y, 'deus.aneis_desvio'), setn(d_, 'i', '=', 'deus.final_buraco_meio + 1'),
                       som('som_luz.wav', 'deus.som_volume')],
                      [repete('deus.final_qtd - 2 * deus.final_buraco_meio - 1',
                              tiros(x, y, 'deus.final_qtd', 'deus.aneis_vel', 'deus.aneis_dano'))]))
    return grupo('Fase final', evs)


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('aneis_intervalo', 0.7), ('aneis_rodadas', 3), ('aneis_qtd', 22), ('aneis_buraco_meio', 2), ('aneis_vel', 420),
        ('aneis_desvio', 25), ('aneis_dano', 20), ('aneis_ttl', 6), ('aneis_fim', 0.8), ('aneis_feitos', 0),
        ('buraco_ang', 0), ('i', 0), ('puxao_forca', 1400), ('puxao_tempo', 2.5), ('puxao_tom', 0.7),
        ('orbita_ang', 0), ('orbita_vel', 0.9), ('orbita_raio', 260), ('orbita_passo', 2.094), ('anel_giro_final', 90),
        ('aneis_final_intervalo', 1.2), ('anel_vez', 0), ('final_qtd', 14), ('final_buraco_meio', 2),
        ('final_iniciado', False), ('fase4_pausa_fator', 0.6)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Janela aberta')
    deus['events'][k:k] = [tres_aneis(), puxao(), fase_final()]
    # relógios do Deus zerados na criação
    texto = json.dumps(deus, ensure_ascii=False)
    comparados = sorted(set(re.findall(r'"CompareObjectTimer"\}, "parameters": \["deus", "\\"(\w+)\\""', texto)))
    cria = acha(deus['events'], 'Criação')['events'][0]
    ja = set(re.findall(r'"ResetObjectTimer"\}, "parameters": \["deus", "\\"(\w+)\\""', json.dumps(cria, ensure_ascii=False)))
    cria['actions'] += [zera(d_, n) for n in comparados if n not in ja]


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Fase final') is not None, 't143')
