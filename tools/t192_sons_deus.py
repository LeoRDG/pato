"""Tarefa 192: sons próprios para o chefe final (Deus).
Antes quase todo golpe de Deus tocava som_luz.wav (o mesmo feitiço pequeno dos serafins), só mudando o tom; a troca de fase
e a morte não tinham som nenhum, e acertar a pupila só tocava o splat comum. Agora cada momento tem um som próprio, montado
com gravações CC0 do Freesound (sino, coro, trovão, impactos de cinema, vidro, feixe de energia):
- carga (o anel cintila e o golpe começa), trava (a investida mira), investida (Deus dispara), escudo (o escudo quebra e
  a pupila fica exposta), juízo (o feixe começa), suga (estrelas puxadas / puxão), aviso (sino ao contrário que cresce até
  o clarão), feixe (o raio sai), tele (o pato passa pelo buraco), horizonte (sino grave), anel (cada leva de anéis).
- pulso: enquanto carrega, um zumbido em laço no canal deus.som_canal sobe de volume e tom com a carga
  (deus.zumbido_volume, zumbido_tom_ini/fim) e para no disparo, que toca um estrondo (som_deus_pulso).
- fase (troca de fase), morte e dano (pupila acertada, com espera deus.dano_som_espera).
Volumes: deus.som_volume nos golpes, deus.som_forte_volume nos grandes (pulso, feixe, fase, morte), deus.dano_som_volume;
tom com variação deus.som_variacao. As variáveis *_tom antigas (feitas para variar som_luz) ficam, sem uso.
Rodar uma vez:  python3 tools/t192_sons_deus.py
"""
import numpy as np
from gd_mig import *
from sons_cc0 import SR, baixa, carrega_registro, corta, filtro, grava, le, mixa, salva_registro, tom

FONTES = dict(coro=274121, sino=76405, sino2=378799, trovao=188767, boom_cine=255111, boom_grave=268084, boom_jm=201571,
              golpe_dramatico=222517, subida=685256, inspira=181889, teleporte2=150950, rajada=369516, feixe_luz=362134,
              carga2=610562, vidro2=244238, woosh_fundo=245932, whoosh=60013)


def env(x, ini=0.0, fim=0.0):
    """fade linear de ini s no começo e fim s no final"""
    n = len(x)
    g = np.ones(n)
    if ini:
        k = min(n, int(ini * SR)); g[:k] = np.linspace(0, 1, k)
    if fim:
        k = min(n, int(fim * SR)); g[n - k:] *= np.linspace(1, 0, k)
    return x * g


def eco(x, tempo=1.2, mistura=0.3, seed=1):
    """reverberação simples: convolução com ruído que decai (cauda de tempo s)"""
    r = np.random.default_rng(seed)
    n = int(tempo * SR)
    ir = r.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir = filtro(ir, 200, 6000)
    ir /= np.sqrt((ir ** 2).sum())
    m = len(x) + n
    w = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)
    seco = np.concatenate([x, np.zeros(n)])
    return seco + mistura * w * (np.abs(seco).max() / (np.abs(w).max() + 1e-12))


def laco(x, cruza=0.3):
    """laço sem emenda: o final entra por cima do começo (crossfade de cruza s)"""
    k = int(cruza * SR)
    a, b = x[:-k].copy(), x[-k:]
    a[:k] = a[:k] * np.linspace(0, 1, k) + b * np.linspace(1, 0, k)
    return a


def ao_contrario(x):
    return x[::-1].copy()


def receitas(f):
    R = {}
    R['som_deus_carga.wav'] = ('Deus começa um golpe: carga com coro grave', [('carga2', '1,2 s'), ('coro', 'tom -25%, por baixo')],
        mixa((env(corta(f('carga2'), dur=1.2), 0, 0.4), 0, 1), (env(tom(corta(f('coro'), 0.2, 1.2), 0.75), 0.3, 0.4), 0, 0.6)),
        {'fade_out': 0.3})
    zum = mixa((tom(corta(f('coro'), 0.45, 2.4, auto=False), 0.6), 0, 1),
               (filtro(corta(f('boom_grave'), 1.5, 4.0, auto=False), None, 220), 0, 0.7))
    R['som_deus_zumbido.wav'] = ('zumbido em laço enquanto o pulso carrega', [('coro', '2,4 s a partir de 0,45 s, tom -40%'),
                                 ('boom_grave', 'trecho do meio, só o grave')], laco(zum[:int(3.2 * SR)]),
        {'fade_in': 0, 'fade_out': 0, 'ataque': 0})
    R['som_deus_pulso.wav'] = ('pulso de luz sai do olho', [('boom_cine', '2,4 s'), ('trovao', 'estalo, 2 s'), ('sino2', 'tom -20%')],
        eco(mixa((corta(f('boom_cine'), dur=2.4), 0, 1), (corta(f('trovao'), 0.15, 2.0), 0, 0.7),
                 (tom(corta(f('sino2'), dur=2.5), 0.8), 0, 0.45)), 1.5, 0.25), {'fade_out': 1.0, 'satura': 0.6})
    R['som_deus_trava.wav'] = ('investida trava a mira', [('sino2', 'tom +40%, 0,6 s'), ('boom_jm', '0,3 s, só o grave')],
        mixa((tom(corta(f('sino2'), dur=0.8), 1.4), 0, 0.8), (filtro(corta(f('boom_jm'), dur=0.3), None, 300), 0, 0.7)),
        {'fade_out': 0.25})
    R['som_deus_investida.wav'] = ('Deus dispara na investida', [('woosh_fundo', '0,9 s, tom -20%'), ('boom_jm', '0,4 s, só o grave')],
        mixa((tom(corta(f('woosh_fundo'), dur=0.75), 0.8), 0, 1), (filtro(corta(f('boom_jm'), dur=0.45), None, 400), 0, 0.8)),
        {'fade_out': 0.25, 'satura': 0.3})
    R['som_deus_escudo.wav'] = ('escudo de Deus quebra', [('vidro2', '1,3 s a partir do estouro'), ('golpe_dramatico', '1,5 s'),
                                ('sino2', 'tom -30%')],
        eco(mixa((corta(f('vidro2'), 0.25, 1.3), 0, 1), (corta(f('golpe_dramatico'), dur=1.5), 0, 0.8),
                 (tom(corta(f('sino2'), dur=1.5), 0.7), 0, 0.35)), 1.0, 0.2), {'fade_out': 0.6})
    R['som_deus_juizo.wav'] = ('o Juízo começa', [('coro', '2,5 s, tom -45%'), ('boom_grave', '2,5 s, só o grave')],
        mixa((env(tom(corta(f('coro'), dur=1.5), 0.55), 0.05, 0.8), 0, 1), (filtro(corta(f('boom_grave'), dur=2.5), None, 160), 0, 0.6)),
        {'fade_out': 0.8})
    R['som_deus_suga.wav'] = ('as estrelas são sugadas / o puxão', [('inspira', '1,8 s a partir de 0,3 s'), ('subida', 'tom +10%, por baixo')],
        mixa((corta(f('inspira'), 0.3, 1.8, auto=False), 0, 1), (tom(corta(f('subida'), 1.2, 1.9, auto=False), 1.1), 0, 0.5)),
        {'fade_out': 0.25, 'ataque': 0})
    sobe = mixa((corta(f('subida'), 1.95, 1.05, auto=False), 0, 1), (ao_contrario(tom(corta(f('sino2'), dur=1.05), 0.9)), 0, 0.8))
    R['som_deus_aviso.wav'] = ('aviso: sobe até o clarão do Juízo', [('subida', 'o último 1,05 s'), ('sino2', 'ao contrário, tom -10%')],
        sobe, {'fade_in': 0.02, 'fade_out': 0.02, 'ataque': 0})
    R['som_deus_feixe.wav'] = ('o feixe do Juízo sai', [('feixe_luz', '1,9 s'), ('boom_cine', '2 s'), ('rajada', '2,4 s'),
                               ('coro', 'tom -20%, por baixo')],
        eco(mixa((corta(f('feixe_luz'), dur=1.9), 0, 0.55), (corta(f('boom_cine'), dur=2.0), 0, 1),
                 (corta(f('rajada'), 0.1, 2.4), 0, 0.7), (env(tom(corta(f('coro'), 0.3, 1.8), 0.8), 0.05, 0.8), 0, 0.5)),
            1.6, 0.25), {'fade_out': 1.0, 'satura': 0.5})
    R['som_deus_tele.wav'] = ('o pato passa pelo buraco', [('teleporte2', 'inteiro, tom -10%'), ('boom_jm', '0,3 s, só o grave')],
        mixa((tom(corta(f('teleporte2')), 0.9), 0, 1), (filtro(corta(f('boom_jm'), dur=0.3), None, 300), 0, 0.5)), {'fade_out': 0.2})
    R['som_deus_horizonte.wav'] = ('o horizonte negro aparece', [('sino', '3 s, tom -20%')],
        tom(corta(f('sino'), dur=2.4), 0.8), {'fade_out': 1.0})
    R['som_deus_anel.wav'] = ('leva de anéis de luz', [('sino2', '0,7 s, tom +20%'), ('whoosh', 'tom -30%'), ('boom_jm', '0,25 s, só o grave')],
        mixa((tom(corta(f('sino2'), dur=0.85), 1.2), 0, 0.6), (tom(corta(f('whoosh')), 0.7), 0, 0.8),
             (filtro(corta(f('boom_jm'), dur=0.25), None, 250), 0, 0.6)), {'fade_out': 0.3})
    R['som_deus_fase.wav'] = ('Deus muda de fase', [('golpe_dramatico', '3 s'), ('coro', 'tom -30%'), ('sino', 'tom -40%'), ('trovao', '2 s')],
        eco(mixa((corta(f('golpe_dramatico'), dur=3.0), 0, 1), (env(tom(corta(f('coro'), 0.3, 1.8), 0.7), 0.1, 1.0), 0.1, 0.6),
                 (tom(corta(f('sino'), dur=1.8), 0.6), 0, 0.5), (corta(f('trovao'), 0.15, 2.0), 0, 0.6)), 1.8, 0.2),
        {'fade_out': 1.2, 'satura': 0.4})
    R['som_deus_morte.wav'] = ('Deus morre', [('boom_grave', '5 s'), ('trovao', 'inteiro'), ('golpe_dramatico', '4 s'),
                               ('vidro2', 'estouro'), ('coro', 'inteiro, entra a 0,4 s'), ('sino', 'tom -30%, aos 1,2 s')],
        eco(mixa((corta(f('boom_grave'), dur=5.0), 0, 1), (corta(f('trovao'), 0.15), 0, 0.7), (corta(f('golpe_dramatico'), dur=4.0), 0, 0.7),
                 (corta(f('vidro2'), 0.25, 1.3), 0, 0.6), (env(corta(f('coro'), 0.2, 4.0), 0.3, 1.5), 0.4, 0.6),
                 (tom(corta(f('sino'), dur=3.0), 0.7), 1.2, 0.45)), 2.2, 0.3), {'fade_out': 2.0, 'satura': 0.4})
    R['som_deus_dano.wav'] = ('a pupila de Deus é acertada', [('boom_jm', '0,25 s, sem agudo'), ('vidro2', 'um estalo, tom +30%')],
        mixa((filtro(corta(f('boom_jm'), dur=0.25), None, 900), 0, 1), (tom(corta(f('vidro2'), 0.27, 0.15), 1.3), 0, 0.4)),
        {'fade_out': 0.1})
    return R


def faz_sons():
    reg = carrega_registro()
    nomes = {k: baixa(k, v, reg) for k, v in FONTES.items()}
    cache = {}
    f = lambda k: cache.setdefault(k, le(nomes.get(k, k)))
    usos = []
    for som, (desc, fontes, x, op) in receitas(f).items():
        grava(x, som, **op)
        usos.append((som, desc, [(nomes[a], t) for a, t in fontes]))
    salva_registro(reg, usos, 'sons do chefe final, tools/t192_sons_deus.py')
    return list(receitas(f))


SONS = ['som_deus_carga.wav', 'som_deus_zumbido.wav', 'som_deus_pulso.wav', 'som_deus_trava.wav', 'som_deus_investida.wav',
        'som_deus_escudo.wav', 'som_deus_juizo.wav', 'som_deus_suga.wav', 'som_deus_aviso.wav', 'som_deus_feixe.wav',
        'som_deus_tele.wav', 'som_deus_horizonte.wav', 'som_deus_anel.wav', 'som_deus_fase.wav', 'som_deus_morte.wav',
        'som_deus_dano.wav']
TOM = 'RandomFloatInRange(1 - deus.som_variacao, 1 + deus.som_variacao)'
FORTES = {'som_deus_pulso.wav', 'som_deus_feixe.wav'}
# grupo -> sons novos, na ordem em que os PlaySound antigos (som_luz / som_dash) aparecem nele
TROCAS = {
    'Sinal de vulnerável': ['escudo'],
    'Anel de ouro: o pulso': ['carga', 'pulso'],
    'Anel azul: investida': ['carga', 'trava', 'investida'],
    'Anel rosa: amor': ['escudo'],
    'Juízo: o feixe': ['juizo', 'suga', 'aviso', 'feixe', 'tele', 'horizonte'],
    'Três anéis': ['anel'],
    'Puxão': ['suga'],
    'Fase final': ['anel', 'anel', 'anel'],
}


def para_zumbido():
    return X('StopSoundCanal', '', 'deus.som_canal')


def migra(d):
    ids = Ids('t192')
    for s in SONS:
        if s not in {r['name'] for r in d['resources']['resources']}:
            d['resources']['resources'].append({'file': f'assets/{s}', 'kind': 'audio', 'metadata': '', 'name': s,
                                                'preloadAsMusic': False, 'preloadAsSound': True, 'preloadInCache': False,
                                                'userAdded': True})
    deus = objeto(d, 'deus')
    poe_vars(ids, deus['variables'], 'deus', [
        ('som_forte_volume', 100), ('som_variacao', 0.03), ('som_canal', 7), ('zumbido_volume', 55),
        ('zumbido_tom_ini', 0.7), ('zumbido_tom_fim', 1.25), ('dano_som_volume', 50), ('dano_som_espera', 0.12)])

    evs = folha(d, 'InimigosParaiso')['events']
    for nome, novos in TROCAS.items():
        g = acha(evs, nome)
        acs = [a for e in todos(g['events']) for a in e.get('actions', [])
               if a['type']['value'] == 'PlaySound' and a['parameters'][1] in ('som_luz.wav', 'som_dash.wav')]
        assert len(acs) == len(novos), (nome, len(acs))
        for a, n in zip(acs, novos):
            s = f'som_deus_{n}.wav'
            a['parameters'][1] = s
            a['parameters'][3] = 'deus.som_forte_volume' if s in FORTES else 'deus.som_volume'
            a['parameters'][4] = TOM

    # pulso: zumbido em laço durante a carga, para no disparo
    pulso = acha(evs, 'Anel de ouro: o pulso')
    comeca = next(e for e in todos(pulso['events']) if any(a['parameters'][1:2] == ['som_deus_carga.wav'] for a in e.get('actions', [])
                                                           if a['type']['value'] == 'PlaySound'))
    comeca['actions'].append(X('PlaySoundOnChannel', '', 'som_deus_zumbido.wav', 'deus.som_canal', 'yes', '0', 'deus.zumbido_tom_ini'))
    carrega = next(e for e in pulso['events'] if 'conv_ang' in json.dumps(e.get('actions', [])))
    prog = 'min(1, deus.ObjectTimerElapsedTime("golpe") / deus.pulso_carga)'
    carrega['actions'] += [
        X('SetSoundChannelVolume', '', 'deus.som_canal', '=', f'deus.zumbido_volume * sqrt({prog})'),
        X('SetSoundChannelPitch', '', 'deus.som_canal', '=', f'deus.zumbido_tom_ini + (deus.zumbido_tom_fim - deus.zumbido_tom_ini) * {prog}')]
    dispara = next(e for e in todos(pulso['events']) if any(a['parameters'][1:2] == ['som_deus_pulso.wav'] for a in e.get('actions', [])
                                                            if a['type']['value'] == 'PlaySound'))
    dispara['actions'].append(para_zumbido())

    fases = acha(evs, 'Fases')
    muda = next(e for e in fases['events'] if '"fase_vista", "=", "deus.fase"' in json.dumps(e.get('actions', [])))
    muda['actions'] += [para_zumbido(), som('som_deus_fase.wav', 'deus.som_forte_volume', TOM)]
    morte = acha(evs, 'Morte')['events'][0]
    morte['actions'] += [para_zumbido(), som('som_deus_morte.wav', 'deus.som_forte_volume', TOM)]
    dano = next(e for e in acha(evs, 'Dano na pupila')['events'] if '"deus", "acertado", "True"' in json.dumps(e.get('conditions', [])))
    dano['events'] = (dano.get('events') or []) + [
        ev([timer('deus', 'som_dano', '>', 'deus.dano_som_espera')],
           [som('som_deus_dano.wav', 'deus.dano_som_volume', TOM), zera('deus', 'som_dano')])]
    cria = acha(evs, 'Criação')
    next(e for e in todos(cria['events']) if '"ResetObjectTimer"}, "parameters": ["deus"' in json.dumps(e.get('actions', [])))['actions'].append(zera('deus', 'som_dano'))

    pre = next(e for e in todos(folha(d, 'Jogador')['events']) if sum(a['type']['value'] == 'PreloadSound' for a in e.get('actions', [])) > 10)
    tem = {a['parameters'][1] for a in pre['actions'] if a['type']['value'] == 'PreloadSound'}
    pre['actions'] += [X('PreloadSound', '', s) for s in SONS if s not in tem]


if __name__ == '__main__':
    faz_sons()
    roda(migra, lambda d: any(r['name'] == 'som_deus_pulso.wav' for r in d['resources']['resources']), 't192')
