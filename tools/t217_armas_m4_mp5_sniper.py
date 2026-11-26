"""Tarefa 217: três armas novas nos pedestais dos hubs (de graça, pegar com E como as outras): M4 (fuzil automático),
MP5 (submetralhadora, tiro muito rápido e fraco) e sniper (lenta, dano alto, atravessa vários inimigos).

- Objetos m4, mp5, sniper (pasta armas, grupo Arma), cópias da pistola com o FireBullet e as variáveis de arma
  ajustados; a escala na mão vem da variável nova `escala`, e o som do tiro de `som_vol`/`som_tom`.
- Animações m4/mp5/sniper em expositor_arma, hud_arma_icone e flash_cano (o flash reaproveita os existentes).
- Eventos: Criação das Armas (cria, escala e equipa pela arma_atual), sons de tiro e de recarga, HUD (ícone e nome),
  pegar no pedestal (Hubs) e nomes em stats_nome.
- Três pedestal_arma novos em cada hub (Hub, HubPurgatorio, HubParaiso).
Só adiciona; não roda de novo.  python3 tools/t217_armas_m4_mp5_sniper.py [jogo.json]
"""
import copy
from gd_mig import Ids, X, ev, acha, folha, cena, objeto, poe_objeto, poe_no_grupo, poe_recursos, var, inst, roda, \
    setb, txt

ids = Ids('t217')
NOVAS = ['m4', 'mp5', 'sniper']
NOMES = {'m4': 'M4', 'mp5': 'MP5', 'sniper': 'SNIPER'}
# FireBullet e variáveis (o resto vem da pistola)
COMPORTA = {
    'm4':     dict(FireCooldown=0.11, ShotsPerReload=30, ReloadDuration=1.6, AngleVariance=2.5, MaxAmmo=300, StartingAmmo=300),
    'mp5':    dict(FireCooldown=0.065, ShotsPerReload=32, ReloadDuration=1.2, AngleVariance=6, MaxAmmo=320, StartingAmmo=320),
    'sniper': dict(FireCooldown=1.1, ShotsPerReload=5, ReloadDuration=2.6, AngleVariance=0, MaxAmmo=60, StartingAmmo=60),
}
VARS = {
    'm4':     dict(valocidade_bala=2600, recuo=3, cooldown_base=0.11, recarga_base=1.6, dano=15, furos=0, repulsao=0.8,
                   disp_min=2.5, disp_max=2.5, vel_mov=0.92, kick=5, tremor=0.5, bocal_f=-0.237, flash_dur=0.04,
                   flash_escala=2.5, escala=1.3, som_vol=55, som_tom=0.85),
    'mp5':    dict(valocidade_bala=2000, recuo=2, cooldown_base=0.065, recarga_base=1.2, dano=8, furos=0, repulsao=0.5,
                   disp_min=6, disp_max=6, vel_mov=1.05, kick=3, tremor=0.3, bocal_f=-0.226, flash_dur=0.035,
                   flash_escala=2.2, escala=2.6, som_vol=50, som_tom=1.25),
    'sniper': dict(valocidade_bala=5000, recuo=18, cooldown_base=1.1, recarga_base=2.6, dano=95, furos=4, repulsao=3,
                   disp_min=0, disp_max=0, vel_mov=0.85, kick=24, tremor=0, bocal_f=-0.062, flash_dur=0.09,
                   flash_escala=4.5, escala=1.1, som_vol=100, som_tom=0.6),
}
SOM_TIRO = {'m4': 'som_minigun.wav', 'mp5': 'som_pistola.wav', 'sniper': 'som_doze.wav'}
SOM_RECARGA = {'m4': 'som_recarga_minigun.wav', 'mp5': 'som_recarga_pistola.wav', 'sniper': 'som_recarga_doze.wav'}
FLASH = {'m4': 'minigun', 'mp5': 'pistola', 'sniper': 'doze'}
# pedestal: escala do expositor, fase do balanço e posição x (y igual à dos outros pedestais)
PEDESTAL = {'m4': (1, 6, 20), 'mp5': (2, 7.5, -140), 'sniper': (0.8, 9, -300)}


def nova_arma(d, base, n):
    o = copy.deepcopy(base)
    o['name'] = n
    o['persistentUuid'] = ids('obj/' + n)
    img = f'assets/arma_{n}.png'
    from PIL import Image
    import os
    from gd_mig import RAIZ
    w, h = Image.open(os.path.join(RAIZ, img)).size
    q = o['animations'][0]['directions'][0]['sprites'][0]
    q['image'] = img
    q['customCollisionMask'] = [[{'x': 0, 'y': 0}, {'x': w, 'y': 0}, {'x': w, 'y': h}, {'x': 0, 'y': h}]]
    o['behaviors'][0].update(COMPORTA[n])
    vals = VARS[n]
    nv = []
    for v in o['variables']:
        v = dict(v, persistentUuid=ids(f'var/{n}/{v["name"]}'))
        if v['name'] in vals:
            v['value'] = vals[v['name']]
        nv.append(v)
    tem = {v['name'] for v in nv}
    nv += [var(ids, n, k, val) for k, val in vals.items() if k not in tem]
    o['variables'] = nv
    return o


def anima(obj, nome, img, modelo=None):
    if nome in [a['name'] for a in obj['animations']]:
        return
    a = copy.deepcopy(modelo or obj['animations'][0])
    a['name'] = nome
    a['directions'][0]['sprites'][0]['image'] = img
    obj['animations'].append(a)


def migra(d):
    poe_recursos(d, [f'assets/arma_{n}.png' for n in NOVAS] + [f'assets/hud/arma_{n}.png' for n in NOVAS])
    base = objeto(d, 'pistola')
    for n in NOVAS:
        poe_objeto(d, nova_arma(d, base, n), 'armas')
        poe_no_grupo(d, 'Arma', n)
        anima(objeto(d, 'expositor_arma'), n, f'assets/arma_{n}.png')
        anima(objeto(d, 'hud_arma_icone'), n, f'assets/hud/arma_{n}.png')
        flash = objeto(d, 'flash_cano')
        modelo = next(a for a in flash['animations'] if a['name'] == FLASH[n])
        anima(flash, n, modelo['directions'][0]['sprites'][0]['image'], modelo)

    stats = next(v for v in d['variables'] if v['name'] == 'stats_nome')
    tem = {c['name'] for c in stats['children']}
    stats['children'] += [var(ids, 'stats_nome', n, NOMES[n]) for n in NOVAS if n not in tem]

    jog = folha(d, 'Jogador')['events']
    cria = acha(jog, 'Criacao das Armas')['events'][0]
    i = next(k for k, a in enumerate(cria['actions']) if a['type']['value'] == 'Hide')
    cria['actions'][i:i] = [X('Create', '', n, 'pato.X()', 'pato.Y()', '') for n in NOVAS] + \
        [X('ScalableCapability::ScalableBehavior::SetValue', n, 'Scale', '=', f'{n}.escala') for n in NOVAS]
    cria['events'] += [ev([X('StringVariable', 'arma_atual', '=', f'"{n}"')],
                          [setb(n, 'equipada', True), X('Show', n, '')]) for n in NOVAS]

    sons = acha(jog, 'Sons')
    tiro = acha(sons['events'], 'Tiro')
    tiro['events'] += [ev([X('FireBullet::FireBullet::HasJustFired', n, 'FireBullet', '')],
                          [X('PlaySoundOnChannel', '', SOM_TIRO[n], '1', '80', f'{n}.som_vol', f'{n}.som_tom'),
                           X('SetSoundChannelPitch', '', '1', '*', 'RandomFloatInRange(.96, 1.04)')]) for n in NOVAS]
    rec = acha(sons['events'], 'Recarga')
    for n in NOVAS:
        rec['events'].append(ev(
            [X('FireBullet::FireBullet::IsReloadInProgress', n, 'FireBullet', ''), X('BooleanObjectVariable', n, 'som_recarga', 'False', '')],
            [setb(n, 'som_recarga', True), X('PlaySoundOnChannel', '', SOM_RECARGA[n], '6', '', '80', '1'),
             X('SetSoundChannelPitch', '', '6', '=',
               f'clamp({n}.recarga_base / max(0.01, {n}.FireBullet::ReloadDuration()), 1, 2)')]))
        fim = X('FireBullet::FireBullet::IsReloadInProgress', n, 'FireBullet', '')
        fim['type']['inverted'] = True
        rec['events'].append(ev([fim], [setb(n, 'som_recarga', False)]))

    hud = acha(folha(d, 'HUD')['events'], 'Arma')['events'][0]
    hud['events'] += [ev([X('BooleanObjectVariable', n, 'equipada', 'True', '')],
                         [X('AnimatableCapability::AnimatableBehavior::SetName', 'hud_arma_icone', 'Animation', '=', f'"{n}"'),
                          X('TextContainerCapability::TextContainerBehavior::SetValue', 'hud_arma_nome', 'Text', '=',
                            f'"{NOMES[n]}"')]) for n in NOVAS]

    hub = acha(folha(d, 'Hubs')['events'], 'Armas no hub')
    pega = next(e for e in hub['events'] if any(c['type']['value'] == 'PickNearest' for c in e.get('conditions', [])))
    troca = next(e for e in pega['events'] if any(c['type']['value'] == 'BuiltinCommonInstructions::Or'
                                                   for c in e.get('conditions', [])))
    troca['events'] += [ev([txt('expositor_arma', 'arma', n)],
                           [setb(n, 'equipada', True), X('Show', n, ''), X('SetStringVariable', 'arma_atual', '=', f'"{n}"')])
                        for n in NOVAS]

    for nome in ('Hub', 'HubPurgatorio', 'HubParaiso'):
        c = cena(d, nome)
        ped = next(i for i in c['instances'] if i['name'] == 'pedestal_arma')
        for n in NOVAS:
            esc, fase, x = PEDESTAL[n]
            iv = [var(ids, f'{nome}/{n}', k, v) for k, v in
                  (('arma', n), ('nome', NOMES[n]), ('escala', esc), ('fase', fase))]
            c['instances'].append(inst(ids, 'pedestal_arma', f'{nome}/{n}', x, ped['y'], ped['zOrder'], ped['layer'],
                                       variaveis=iv))


roda(migra, lambda d: objeto(d, 'm4') is not None, 't217')
