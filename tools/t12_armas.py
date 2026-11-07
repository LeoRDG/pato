"""Tarefa 12: reforma das armas (alcance, queda de dano, perfuração, dispersão, lentidão ao atirar) e balanceamento.

Rodar:  python3 tools/t12_armas.py        (pode rodar de novo: refaz tudo do zero, sem duplicar)
Feche o projeto no GDevelop antes (ou reabra depois sem salvar), senão ele sobrescreve o jogo.json.

Orçamento: cada arma rende ~80-95 de dano por segundo (recarga incluída) acertando tudo; o que muda é o quanto custa acertar.
Dano por acerto = dano da arma x queda por distância x aleatório(0,85 a 1,15) x mult_dano.
"""
import json, os, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'jogo.json')

# ------------------------------------------------------------------ valores por arma
# dano, balas por tiro, cooldown, pente, recarga, reserva (balas), alcance (px), queda_ini (px), queda_min (fração),
# furos (inimigos extras que a bala atravessa), repulsão, dispersão mínima/máxima (graus), velocidade ao atirar
ARMAS = {
    'pistola': dict(dano=26, balas=1, cooldown=0.25, pente=12, recarga=1.0, reserva=108, alcance=99999, queda_ini=0, queda_min=1,
                    furos=1, repulsao=1, disp_min=3, disp_max=3, vel_mov=1, arco=45),
    'doze':    dict(dano=11, balas=8, cooldown=0.7, pente=6, recarga=2.2, reserva=32, alcance=450, queda_ini=150, queda_min=0.4,
                    furos=0, repulsao=2, disp_min=0, disp_max=0, vel_mov=1, arco=30),
    'minigun': dict(dano=8, balas=1, cooldown=0.08, pente=100, recarga=2.5, reserva=350, alcance=700, queda_ini=0, queda_min=1,
                    furos=0, repulsao=0.5, disp_min=2, disp_max=10, vel_mov=0.65, arco=45),
}
GRUPO = 'Balas (alcance, queda e perfuração)'
DIST = 'DistanceBetweenPositions(projetil.CenterX(), projetil.CenterY(), projetil.ox, projetil.oy)'


def var(nome, valor):
    tipo = 'boolean' if isinstance(valor, bool) else 'number'
    return {'name': nome, 'persistentUuid': str(uuid.uuid4()), 'type': tipo, 'value': valor}


def upsert(lista, nome, valor):
    for v in lista:
        if v['name'] == nome:
            v['value'] = valor
            return
    lista.append(var(nome, valor))


def C(tipo, *params, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(params)}


def A(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def E(conds, acts, subs=None, tipo='BuiltinCommonInstructions::Standard', **extra):
    return {'type': tipo, 'conditions': conds, 'actions': acts, 'events': subs or [], **extra}


def comentario(txt):
    return {'type': 'BuiltinCommonInstructions::Comment', 'comment': txt,
            'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0}}


def grupo(nome, subs):
    return {'type': 'BuiltinCommonInstructions::Group', 'name': nome, 'source': '', 'creationTime': 0,
            'colorR': 74, 'colorG': 176, 'colorB': 228, 'parameters': [], 'events': subs}


def procura(evs, nome):
    for e in evs:
        if e.get('name') == nome:
            return e
        r = procura(e.get('events', []), nome)
        if r:
            return r
    return None


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    obj = {o['name']: o for o in d['objects']}
    ext = lambda n: [e for e in d['externalEvents'] if e['name'] == n][0]

    # ---------------------------------------------------------- variáveis globais
    upsert(d['variables'], 'serie_bala', 0)
    armas = [v for v in d['variables'] if v['name'] == 'armas'][0]
    for f in armas['children']:  # doze e minigun ficam liberadas por enquanto
        f['value'] = True

    # ---------------------------------------------------------- objetos das armas
    for nome, a in ARMAS.items():
        o = obj[nome]
        for k in ('dano', 'alcance', 'queda_ini', 'queda_min', 'furos', 'repulsao', 'disp_min', 'disp_max', 'vel_mov'):
            upsert(o['variables'], k, a[k])
        upsert(o['variables'], 'cooldown_base', a['cooldown'])
        upsert(o['variables'], 'recarga_base', a['recarga'])
        b = [b for b in o['behaviors'] if b['type'] == 'FireBullet::FireBullet'][0]
        b.update(FireCooldown=a['cooldown'], BulletQuantity=a['balas'], FiringArc=a['arco'], AngleVariance=a['disp_min'],
                 ShotsPerReload=a['pente'], ReloadDuration=a['recarga'], MaxAmmo=a['reserva'], StartingAmmo=a['reserva'])

    # ---------------------------------------------------------- bala
    for k, v in dict(alcance=99999, queda_ini=0, queda_min=1, furos=0, repulsao=1, ox=0, oy=0, serie=0, fator=1).items():
        upsert(obj['projetil']['variables'], k, v)
    upsert(obj['projetil']['variables'], 'iniciado', False)

    # cada inimigo guarda a série da última bala que o atravessou (uma bala não acerta o mesmo inimigo duas vezes)
    for g in [g for g in d['objectsGroups'] if g['name'] == 'Inimigo']:
        for m in g['objects']:
            upsert(obj[m['name']]['variables'], 'bala_serie', 0)

    # ---------------------------------------------------------- eventos de combate
    proj = procura(ext('Combate')['events'], 'Projéteis')
    proj['events'] = [e for e in proj['events'] if e.get('name') != GRUPO]
    hit = [e for e in proj['events'] if e['type'] == 'BuiltinCommonInstructions::ForEach' and e.get('object') == 'projetil'][0]

    nova = grupo(GRUPO, [
        comentario('Quando a bala nasce, copia os valores da arma equipada (dano, alcance, queda, perfuração, repulsão) e o ponto de partida. '
                   'Depois a queda de dano depende da distância percorrida e a bala some ao passar do alcance.'),
        E([C('BooleanObjectVariable', 'projetil', 'iniciado', 'False', ''), C('BooleanObjectVariable', 'Arma', 'equipada', 'True', '')], [
            A('SetNumberVariable', 'serie_bala', '+', '1'),
            A('SetNumberObjectVariable', 'projetil', 'serie', '=', 'GlobalVariable(serie_bala)'),
            A('SetNumberObjectVariable', 'projetil', 'dano', '=', 'Arma.dano'),
            A('SetNumberObjectVariable', 'projetil', 'alcance', '=', 'Arma.alcance'),
            A('SetNumberObjectVariable', 'projetil', 'queda_ini', '=', 'Arma.queda_ini'),
            A('SetNumberObjectVariable', 'projetil', 'queda_min', '=', 'Arma.queda_min'),
            A('SetNumberObjectVariable', 'projetil', 'furos', '=', 'Arma.furos'),
            A('SetNumberObjectVariable', 'projetil', 'repulsao', '=', 'Arma.repulsao'),
            A('SetNumberObjectVariable', 'projetil', 'ox', '=', 'projetil.CenterX()'),
            A('SetNumberObjectVariable', 'projetil', 'oy', '=', 'projetil.CenterY()'),
            A('SetBooleanObjectVariable', 'projetil', 'iniciado', 'True', ''),
        ], tipo='BuiltinCommonInstructions::ForEach', object='projetil'),
        E([C('BooleanObjectVariable', 'projetil', 'iniciado', 'True', '')], [
            A('SetNumberObjectVariable', 'projetil', 'fator', '=',
              f'1 - (1 - projetil.queda_min) * clamp(({DIST} - projetil.queda_ini) / max(1, projetil.alcance - projetil.queda_ini), 0, 1)'),
        ], [
            E([C('BuiltinCommonInstructions::CompareNumbers', DIST, '>', 'projetil.alcance')], [A('Delete', 'projetil', '')]),
        ], tipo='BuiltinCommonInstructions::ForEach', object='projetil'),
    ])
    proj['events'].insert(1, nova)

    # acerto: dano da bala x queda x variação, repulsão da bala, perfuração
    acoes = hit['actions']
    for a in acoes:
        p = a['parameters']
        if a['type']['value'] == 'SetNumberObjectVariable' and p[:2] == ['Inimigo', 'vida']:
            p[3] = 'projetil.dano * projetil.fator * RandomFloatInRange(0.85, 1.15) * GlobalVariable(mult_dano)'
        elif a['type']['value'] == 'SetNumberObjectVariable' and p[:2] == ['Inimigo', 'kb_dir']:
            p[3] = 'sign(Inimigo.CenterX() - projetil.CenterX()) * projetil.repulsao * projetil.fator'
    for k, a in enumerate(acoes):
        if a['type']['value'] == 'Delete' and a['parameters'][0] == 'projetil':
            acoes[k] = A('SetNumberObjectVariable', 'Inimigo', 'bala_serie', '=', 'projetil.serie')
    if not any(c['parameters'][:3] == ['Inimigo', 'bala_serie', '!='] for c in hit['conditions']):
        hit['conditions'].append(C('NumberObjectVariable', 'Inimigo', 'bala_serie', '!=', 'projetil.serie'))
    hit['events'] = [e for e in hit['events'] if not any(a['type']['value'] == 'Delete' and a['parameters'][0] == 'projetil'
                                                         for a in e.get('actions', []))
                     and not any(c['parameters'][:2] == ['projetil', 'furos'] for c in e.get('conditions', []))]
    hit['events'] += [
        E([C('NumberObjectVariable', 'projetil', 'furos', '<=', '0')], [A('Delete', 'projetil', '')]),
        E([C('NumberObjectVariable', 'projetil', 'furos', '>', '0')], [A('SetNumberObjectVariable', 'projetil', 'furos', '-', '1')]),
    ]

    # o número de dano fica branco nos acertos fracos (antes: dano base + 10)
    for e in walk(ext('Combate')['events']):
        for a in e.get('actions', []):
            pass
        for c in e.get('conditions', []):
            if c['parameters'][-1:] == ['(projetil.dano + 10)']:
                c['parameters'][-1] = '(projetil.dano * 1.05)'

    # ---------------------------------------------------------- dispersão e lentidão da arma equipada
    ctrl = procura(ext('Jogador')['events'], 'Controle das Armas')
    equipada = [e for e in ctrl['events'] if e['type'] == 'BuiltinCommonInstructions::Standard'][0]
    equipada['events'] = [e for e in equipada['events'] if e.get('name') != 'Dispersão e lentidão']
    atirando = C('MouseButtonFromTextPressed', '', '"Left"')
    base = '289 * (1 + 0.1 * GlobalVariable(upgrades.velocidade))'
    equipada['events'].append(grupo('Dispersão e lentidão', [
        comentario('Segurando o gatilho, a dispersão sobe de disp_min a disp_max em 2,5 s (só o minigun tem os dois diferentes). '
                   'Atirando sem recarregar, o pato anda na velocidade vel_mov da arma.'),
        E([C('MouseButtonFromTextPressed', '', '"Left"', inv=True)], [A('ResetTimer', '', '"fogo"')]),
        E([], [A('FireBullet::FireBullet::SetAngleVariance', 'Arma', 'FireBullet',
                 'Arma.disp_min + (Arma.disp_max - Arma.disp_min) * min(1, TimerElapsedTime("fogo") / 2.5)', '')]),
        E([atirando, C('FireBullet::FireBullet::IsReloadInProgress', 'Arma', 'FireBullet', '', inv=True)],
          [A('PlatformBehavior::MaxSpeed', 'pato', 'PlatformerObject', '=', f'{base} * Arma.vel_mov')]),
        E([C('MouseButtonFromTextPressed', '', '"Left"', inv=True)],
          [A('PlatformBehavior::MaxSpeed', 'pato', 'PlatformerObject', '=', base)]),
        E([C('FireBullet::FireBullet::IsReloadInProgress', 'Arma', 'FireBullet', '')],
          [A('PlatformBehavior::MaxSpeed', 'pato', 'PlatformerObject', '=', base)]),
    ]))
    # grupo 'Dispersão e lentidão' precisa do nome no evento para a idempotência acima
    equipada['events'][-1]['name'] = 'Dispersão e lentidão'

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events', []))


if __name__ == '__main__':
    main()
