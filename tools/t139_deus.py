"""Tarefa 139: Deus, o olho de luz (chefe final, parte 3): corpo, dano, fases, escolha dos golpes e morte.

- Partes com o mesmo centro (deus.cx, deus.cy): aura, os três anéis (giram), o olho (esclera e pálpebras), o escudo
  (escondido; o anel rosa usa) e a pupila. A pupila é o objeto `deus`: é ela que está nos grupos Inimigo, Chefes e
  Personagem, então TODO dano (balas, explosão, ricochete, eletricidade) vem de Combate e respeita invulneravel.
  invulneravel = não vulneravel; vulneravel só abre em janelas. Bala que bate nas outras partes passa.
- Nasce quando a luta pede (deus_criar), sobe de baixo da tela e fica deus.distancia_baixo abaixo do centro da
  câmera, seguindo o pato em x; a pupila olha para o pato (até pupila_alcance).
- Fases pela vida (fase2_abaixo, fase3_abaixo, fase4_abaixo): os anéis quebram e voltam, a subida acelera
  (subida_2..4). Golpes por fase, sem repetir: 1 olhar, 2 piscar, 3 amor, 4 juizo, 5 aneis, 6 puxao
  (golpes_1..4 = quantos valem em cada fase). Cada golpe (próximas tarefas) começa com estado "atacar" e o golpe dele
  e termina pondo estado "fim_golpe"; antes da fase 3 ele então abre (vulneravel por aberto_tempo); depois, pausa.
- Morte: o olho fecha e clareia, anéis quebram, some tudo o que machuca, a luz volta ao normal; depois de
  morte_tempo as partes somem, e só então a luta acaba (Fim da luta espera o olho sumir; a saída espera luta False).
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t139_deus.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t139')
D = 'assets/inimigos/ceu/deus'
P = 'assets/paraiso/deus'
PARTES = ('deus_aura', 'deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa', 'deus_olho', 'deus_escudo')
ANEIS = ('deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa')
GOLPES = ('olhar', 'piscar', 'amor', 'juizo', 'aneis', 'puxao')
CY, CH, CX = 'CameraCenterY("", 0)', 'CameraHeight("", 0)', 'CameraCenterX("", 0)'
d_ = 'deus'


def octogono(c, r):
    import math
    return [(round(c + r * math.cos(math.pi / 8 + k * math.pi / 4)), round(c + r * math.sin(math.pi / 8 + k * math.pi / 4)))
            for k in range(8)]


def objetos(d, ids):
    anims_olho = [('idle', 8, 0.12, True), ('piscar', 8, 0.06, False), ('fechado', 1, 0.1, True),
                  ('carregar', 8, 0.08, False), ('juizo', 12, 0.1, True), ('juizo_falha', 6, 0.08, False),
                  ('dano', 2, 0.06, False), ('fase', 10, 0.08, False), ('morte', 14, 0.12, False)]
    novos = [
        ('deus_olho', [(a, f'{D}/olho', n, t, l) for a, n, t, l in anims_olho]),
        ('deus_aura', [('idle', f'{D}/aura', 8, 0.12, True)]),
        ('deus_escudo', [('idle', f'{D}/escudo', 6, 0.08, True)]),
        ('canalizador', [('idle', 'assets/inimigos/ceu/canalizador', 6, 0.1, True),
                         ('canalizar', 'assets/inimigos/ceu/canalizador', 6, 0.08, True),
                         ('morte', 'assets/inimigos/ceu/canalizador', 8, 0.08, False)]),
        ('fragmento', [(f'f{k}', [f'{P}/fragmento_{k}.png'], 1, 0.1, False) for k in (1, 2, 3)]),
    ] + [(a, [('idle', f'{D}/{a[5:]}', 1, 0.1, True), ('cintila', f'{D}/{a[5:]}', 4, 0.08, True),
              ('quebra', f'{D}/{a[5:]}', 8, 0.07, False)]) for a in ANEIS]
    imgs = []
    for nome, anims in novos:
        for a, pasta, n, *_ in anims:
            imgs += pasta if isinstance(pasta, list) else quadros(pasta, a, n)
    imgs += quadros(f'{D}/pupila', 'idle', 4) + quadros(f'{D}/pupila', 'contrai', 6) + quadros(f'{D}/pupila', 'dano', 2)
    imgs += [f'{P}/feixe.png']
    poe_recursos(d, imgs)
    for nome, anims in novos:
        poe_objeto(d, sprite(ids, nome, anims), 'inimigos/chefe')
    pup = sprite(ids, 'deus', [('idle', f'{D}/pupila', 4, 0.15, True), ('contrai', f'{D}/pupila', 6, 0.06, False),
                               ('dano', f'{D}/pupila', 2, 0.06, False)], mascara=octogono(90, 69))
    poe_objeto(d, pup, 'inimigos/chefe')
    poe_objeto(d, tiled(ids, 'feixe_olhar', f'{P}/feixe.png', 66, 66), 'inimigos/chefe')
    for nome, raio in (('luz_olhar', 420), ('luz_halo', 220)):
        poe_objeto(d, {'name': nome, 'persistentUuid': ids('obj/' + nome), 'type': luz.OBJ_LUZ, 'variables': [],
                       'effects': [], 'behaviors': [], 'assetStoreId': '',
                       'content': dict(luz.CONTEUDO_LUZ, radius=raio)}, 'inimigos/chefe')


def variaveis(d):
    o = {x['name']: x for x in d['objects']}
    cut = {v['name']: v['value'] for v in o['cutulu']['variables']}
    proprias = [
        ('nome', 'DEUS'), ('barra_ativa', True), ('barra_dist', 100000), ('barra_largura', cut['barra_largura']),
        ('barra_rastro_vel', cut['barra_rastro_vel']), ('chefe_final', True), ('firme', True), ('invulneravel', True),
        ('reflete', False), ('vulneravel', False), ('escudo', False), ('qtd_moedas', 0), ('sangue', 'azul'),
        ('tem_barra_de_vida', False), ('vida', 1250), ('max_vida', 1250), ('vida_chefe_mult', 2), ('dano', 25),
        ('chefe_preparado', False), ('estado', 'entrada'), ('golpe', ''), ('ultimo_golpe', 0), ('sorteio', 0),
        ('golpes_max', 1), ('golpes_1', 1), ('golpes_2', 2), ('golpes_3', 4), ('golpes_4', 6),
        ('fase', 1), ('fase_vista', 1), ('fase2_abaixo', 0.75), ('fase3_abaixo', 0.5), ('fase4_abaixo', 0.25),
        ('fase_tempo', 1.6), ('subida_2', 165), ('subida_3', 190), ('subida_4', 220),
        ('entrada_tempo', 2.5), ('pausa_tempo', 1.4), ('aberto_tempo', 3.2), ('morte_tempo', 2.6), ('morte_iniciada', False),
        ('cx', 0), ('cy', 0), ('px', 0), ('py', 0), ('entrada_abaixo', 700), ('distancia_baixo', 330),
        ('segue_x', 0.9), ('subir_suave', 1.6), ('pupila_alcance', 36), ('pupila_suave', 7), ('olhar_ang', 0),
        ('anel_giro_ouro', 28), ('anel_giro_azul', -22), ('anel_giro_rosa', 16), ('z_base', 2600)]
    nomes = {n for n, _ in proprias}
    herdadas = [(v['name'], v['value']) for v in o['ofanim']['variables']
                if v['name'] not in nomes and 'value' in v and not v['name'].startswith('guardiao')]
    if not objeto(d, 'deus')['variables']:
        poe_vars(ids, objeto(d, 'deus')['variables'], 'deus', proprias + herdadas)
    for nome in ('Paraiso', 'Teste'):
        cv = cena(d, 'Paraiso')['variables']
        vals = {v['name']: v['value'] for v in cv}
        poe_vars(ids, cena(d, nome)['variables'], nome,
                 [(n, vals[n]) for n in ('luta', 'deus_criar', 'subida_vel', 'luz_ambiente_normal')])
    for gr in ('Inimigo', 'Chefes', 'Personagem'):
        poe_no_grupo(d, gr, 'deus')


def eventos():
    cria = [X('Create', '', p, CX, f'{CY} + {CH}', '""') for p in PARTES + ('deus',)]
    cria += [X('ChangePlan', p, '=', f'deus.z_base + {k}') for k, p in
             enumerate(('deus_aura', 'deus_anel_rosa', 'deus_anel_azul', 'deus_anel_ouro', 'deus_olho', 'deus'))]
    cria += [X('ChangePlan', 'deus_escudo', '=', 'deus.z_base + 6'), X('Hide', 'deus_escudo'),
             setn(d_, 'cx', '=', CX), setn(d_, 'cy', '=', f'{CY} + {CH} / 2 + deus.entrada_abaixo'),
             setn(d_, 'px', '=', 'deus.cx'), setn(d_, 'py', '=', 'deus.cy'),
             sets(d_, 'estado', 'entrada'), zera(d_, 'estado'), csetb('deus_criar', False),
             X('Create', '', 'luz_olhar', CX, CY, '"Luz"'), luz.acao_raio_luz('luz_olhar', '0')]
    criacao = grupo('Criação', [ev([cbol('deus_criar', True)], cria)])

    preparo = grupo('Preparo', [
        ev([bol(d_, 'preparado', True), bol(d_, 'chefe_preparado', False)],
           [setb(d_, 'chefe_preparado', True), setn(d_, 'max_vida', '*', 'deus.vida_chefe_mult'),
            setn(d_, 'vida', '=', 'deus.max_vida'), setn(d_, 'vida_controle', '=', 'deus.vida'),
            setb(d_, 'firme', True)])])

    pos = [X('SetXY', p, '=', f'deus.cx - {p}.Width() / 2', '=', f'deus.cy - {p}.Height() / 2') for p in PARTES]
    corpo = grupo('Corpo', [
        ev([bol(d_, 'morto', False)],
           [setn(d_, 'cx', '+', '(pato.CenterX() - deus.cx) * min(1, deus.segue_x * TimeDelta())'),
            setn(d_, 'cy', '+', f'({CY} + deus.distancia_baixo - deus.cy) * min(1, deus.subir_suave * TimeDelta())'),
            setn(d_, 'olhar_ang', '=', 'atan2(pato.CenterY() - deus.cy, pato.CenterX() - deus.cx)'),
            setn(d_, 'px', '+', '(deus.cx + cos(deus.olhar_ang) * deus.pupila_alcance - deus.px) * min(1, deus.pupila_suave * TimeDelta())'),
            setn(d_, 'py', '+', '(deus.cy + sin(deus.olhar_ang) * deus.pupila_alcance - deus.py) * min(1, deus.pupila_suave * TimeDelta())')]),
        ev([], pos + [X('SetXY', d_, '=', 'deus.px - deus.Width() / 2', '=', 'deus.py - deus.Height() / 2')]),
        ev([num(d_, 'fase', '<', '4'), bol(d_, 'morto', False)],
           [X('SetAngle', a, '+', f'deus.anel_giro_{a.split("_")[-1]} * TimeDelta()') for a in ANEIS]),
    ])

    dano = grupo('Dano na pupila', [
        ev([bol(d_, 'vulneravel', True), bol(d_, 'morto', False)], [setb(d_, 'invulneravel', False)]),
        ev([bol(d_, 'vulneravel', False)], [setb(d_, 'invulneravel', True)]),
        ev([bol(d_, 'acertado', True)], [setb(d_, 'acertado', False), anim(d_, 'dano')]),
        ev([X('AnimatableCapability::AnimatableBehavior::Name', d_, 'Animation', '=', '"dano"'),
            X('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', d_, 'Animation')], [anim(d_, 'idle')]),
    ])

    fases = []
    for k in (2, 3, 4):
        fases.append(ev([bol(d_, 'morto', False), num(d_, 'fase', '<', str(k)),
                         cmp('deus.vida', '<', f'deus.max_vida * deus.fase{k}_abaixo')],
                        [setn(d_, 'fase', '=', str(k)), csetn('subida_vel', '=', f'deus.subida_{k}')]))
    fases.append(ev([bol(d_, 'morto', False), cmp('deus.fase', '>', 'deus.fase_vista')],
                    [setn(d_, 'fase_vista', '=', 'deus.fase'), sets(d_, 'estado', 'fase'), zera(d_, 'estado'),
                     setb(d_, 'vulneravel', False), setb(d_, 'escudo', False), anim('deus_olho', 'fase')]
                    + [anim(a, 'quebra') for a in ANEIS]))
    fases.append(ev([bol(d_, 'morto', False), txt(d_, 'estado', 'fase'), timer(d_, 'estado', '>', 'deus.fase_tempo')],
                    [sets(d_, 'estado', 'pausa'), zera(d_, 'estado'), anim('deus_olho', 'idle')]
                    + [anim(a, 'idle') for a in ANEIS]))
    fases = grupo('Fases', fases)

    entrada = grupo('Entrada', [
        ev([bol(d_, 'morto', False), txt(d_, 'estado', 'entrada'), timer(d_, 'estado', '>', 'deus.entrada_tempo')],
           [sets(d_, 'estado', 'pausa'), zera(d_, 'estado')])])

    escolha = [ev([num(d_, 'fase', '=', str(k))], [setn(d_, 'golpes_max', '=', f'deus.golpes_{k}')]) for k in (1, 2, 3, 4)]
    escolha.append(ev([bol(d_, 'morto', False), txt(d_, 'estado', 'pausa'), timer(d_, 'estado', '>', 'deus.pausa_tempo')],
                      [setn(d_, 'sorteio', '=', 'RandomInRange(1, deus.golpes_max)')], [
        ev([cmp('deus.sorteio', '=', 'deus.ultimo_golpe'), cmp('deus.golpes_max', '>', '1')],
           [setn(d_, 'sorteio', '=', 'mod(deus.sorteio, deus.golpes_max) + 1')]),
        ev([], [setn(d_, 'ultimo_golpe', '=', 'deus.sorteio'), sets(d_, 'estado', 'atacar'), zera(d_, 'estado')]),
    ] + [ev([num(d_, 'sorteio', '=', str(k))], [sets(d_, 'golpe', golpe)]) for k, golpe in enumerate(GOLPES, 1)]))
    escolha = grupo('Escolha do golpe', escolha)

    janela = grupo('Janela aberta', [
        ev([bol(d_, 'morto', False), txt(d_, 'estado', 'fim_golpe'), num(d_, 'fase', '<', '3')],
           [sets(d_, 'estado', 'aberto'), zera(d_, 'estado'), setb(d_, 'vulneravel', True), anim(d_, 'contrai')]),
        ev([bol(d_, 'morto', False), txt(d_, 'estado', 'fim_golpe'), num(d_, 'fase', '>=', '3')],
           [sets(d_, 'estado', 'pausa'), zera(d_, 'estado')]),
        ev([bol(d_, 'morto', False), txt(d_, 'estado', 'aberto'), timer(d_, 'estado', '>', 'deus.aberto_tempo')],
           [sets(d_, 'estado', 'pausa'), zera(d_, 'estado'), setb(d_, 'vulneravel', False), anim(d_, 'idle')]),
    ])

    morte = grupo('Morte', [
        ev([bol(d_, 'morto', True), bol(d_, 'morte_iniciada', False)],
           [setb(d_, 'morte_iniciada', True), setb(d_, 'vulneravel', False), zera(d_, 'morte_deus'),
            anim('deus_olho', 'morte'), X('Hide', d_), X('Hide', 'deus_escudo')] + [anim(a, 'quebra') for a in ANEIS]
           + [X('Delete', o, '') for o in ('canalizador', 'luz_halo', 'fragmento', 'feixe_olhar', 'luz_olhar',
                                            'projetil_inimigo')]
           + [luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_normal'), luz.acao_raio_luz('luz_pato', 'luz_pato_raio')]),
        ev([bol(d_, 'morte_iniciada', True), timer(d_, 'morte_deus', '>', 'deus.morte_tempo')],
           [X('Delete', o, '') for o in PARTES + ('deus',)]),
    ])
    return grupo('Deus', [criacao, preparo, corpo, dano, fases, entrada, escolha, janela, morte])


def migra(d):
    objetos(d, ids)
    variaveis(d)
    ip = folha(d, 'InimigosParaiso')['events']
    k = next(i for i, e in enumerate(ip) if e.get('name') == 'Ofanim guardião')
    ip.insert(k + 1, eventos())
    lay = cena(d, 'Paraiso')
    fim = acha(lay['events'], 'Fim da luta')['events'][0]
    fim['conditions'].append(X('SceneInstancesCount', '', 'deus_olho', '=', '0'))
    saida = acha(lay['events'], 'Saída no Empíreo')
    sai = next(e for e in todos(saida['events']) if any(a['type']['value'] == 'Scene' for a in e['actions']))
    sai['conditions'].append(cbol('luta', False))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'deus') is not None, 't139')
