"""Tarefa 94: cada inimigo com um golpe só (como na pesquisa do TBoI: um verbo por inimigo, a dificuldade vem de juntar
inimigos). Quem já tinha um golpe fica igual (condenado azul, em chamas, cabeça voadora, caveira azul, olho, mina,
moscas, voador, pigman, querubim, ofanim, roda do anjo). Os outros:

- condenado_inchado: fica igual (acelera perto do pato e explode; morto, estoura a bile em anel).
- caveira_gigante: fica a espiral de fogo. Sai a explosão de fogo em volta (aviso + fogo_raio).
- arvore_condenada: fica o leque de espinhos mirado. Sai o anel a cada anel_cada ataques.
- diabinho: fica o roubo (encosta, rouba até roubo_max moedas e foge; morto, solta as moedas). Em vez de orbitar e dar
  botes, voa direto até o pato na velocidade dele.
- sapo: fica a língua (avisa, machuca e puxa) e a cura dos outros inimigos. Sai o cuspe em arco.
- cutulu: fica o salto que cai com o anel de bolhas (e a fúria, que só acelera). Sai a investida.
- serafim: ficam os anéis com buraco. Sai a espiral.

As variáveis que só esses golpes usavam saem dos objetos (conferido: nenhum evento as usa mais).
Rodar uma vez:  python3 tools/t94_um_golpe_por_inimigo.py
"""
import json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOBRAS = {
    'caveira_gigante': ['fogo_inicio', 'fogo_fim', 'fogo_raio', 'fogo_empurrao', 'ataque_duracao', 'ataque_espera_extra'],
    'arvore_condenada': ['anel_cada', 'anel_qtd', 'anel_vel', 'ataques'],
    'diabinho': ['orbita_vel', 'orbita_raio', 'orbita_suave', 'bote_espera', 'bote_aviso', 'bote_vel', 'bote_tempo'],
    'sapo': ['cuspe_tempo', 'cuspe_gravidade', 'cuspe_dano', 'atacar_tempo'],
    'cutulu': ['investida_vel', 'investida_tempo'],
    'serafim': ['espiral_bracos', 'espiral_giro', 'espiral_cadencia', 'espiral_duracao', 'espiral_vel'],
}
NOMES = {'Sapo (cura, cuspe em arco e língua)': 'Sapo (cura e língua)'}
COMENTARIOS = {
    'Caveira gigante':
        'Mini-boss lento. De espiral_espera em espiral_espera s, com o pato a menos de espiral_alcance, para e gira uma '
        'espiral de bolas de fogo (espiral_bracos braços, espiral_giro graus por rajada) por espiral_duracao s.',
    'Árvore condenada (espinheiro)':
        'Parada; machuca no contato. Com o pato a menos de aggro_dist: treme por aviso_tempo s e atira um leque de '
        'espinho_qtd espinhos na direção dele.',
    'Diabinho (ladrão)':
        'Rói o osso até ver o pato; aí voa direto até ele. Encostar rouba até roubo_max moedas e ele foge rindo; se não '
        'for morto em fuga_tempo s, some com elas. Morto, solta as moedas roubadas.',
    'Sapo (cura e língua)':
        'Fica a dist_min..dist_max do pato. A cada cura_intervalo s cura os inimigos perto. Alinhado com ele a menos de lingua_alcance (|dy| < lingua_alt) avisa por '
        'lingua_aviso s e dá a língua: machuca e puxa o pato para perto (lingua_puxao).',
    'Cutulu (elite)':
        'Salta por cima do pato e cai com um anel de anel_qtd bolhas. Abaixo de furia_abaixo da vida entra em fúria: '
        'espera entre ataques * furia_fator e cor furia_cor.',
    'Serafim (padrões de luz)':
        'Paira altura_sobre_pato acima do pato. Descansa descanso s, avisa (aviso_tempo) e solta `aneis` anéis de '
        'anel_qtd orbes com um buraco de 2*anel_buraco_meio+1 orbes perto da direção do pato (± anel_desvio). Só ataca '
        'com o pato a menos de luz_alcance.',
}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def txt(x):
    return json.dumps(x, ensure_ascii=False)


def conds(e):
    return txt(e.get('conditions') or [])


def tira(lista, pred, n):
    """Tira de lista os eventos que batem com pred; confere que são n."""
    fora = [e for e in lista if pred(e)]
    assert len(fora) == n, (len(fora), n, [conds(e)[:160] for e in fora])
    lista[:] = [e for e in lista if not pred(e)]


def principal(g, obj):
    """O evento 'obj.morto = False' com os subeventos de estado."""
    return next(e for e in g['events'] if e['type'].endswith('Standard')
                and conds(e) == txt([{'type': {'value': 'BooleanObjectVariable'},
                                      'parameters': [obj, 'morto', 'False', '']}]))


def estado(e, s):
    return f'"estado", "=", "\\"{s}\\""' in conds(e)


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    G = {e['name']: e for e in todos(ini) if e['type'].endswith('Group')}
    if 'Sapo (cura e língua)' in G:
        sys.exit('t94 já foi aplicada (grupo Sapo (cura e língua) existe); não roda de novo.')

    # caveira_gigante: sai o fogo em volta (gatilho, preparar, dano, fim)
    m = principal(G['Caveira gigante'], 'caveira_gigante')
    tira(m['events'], lambda e: 'ataque_espera_extra' in conds(e) or estado(e, 'preparar') or estado(e, 'atacar'), 4)

    # arvore_condenada: só o leque
    disparo = next(e for e in G['Árvore condenada (espinheiro)']['events']
                   if e['type'].endswith('ForEach') and estado(e, 'preparar'))
    disparo['actions'] = [a for a in disparo['actions'] if a['parameters'][:2] != ['arvore_condenada', 'ataques']]
    tira(disparo['events'], lambda e: '"=", "0"' in conds(e) and 'anel_cada' in conds(e), 1)
    leque = next(e for e in disparo['events'] if 'anel_cada' in conds(e))
    leque['conditions'] = []

    # diabinho: voa direto e rouba
    m = principal(G['Diabinho (ladrão)'], 'diabinho')
    per = next(e for e in m['events'] if estado(e, 'perseguir') and 'bote_espera' not in conds(e))
    ang = 'atan2(pato.CenterY() - diabinho.CenterY(), pato.CenterX() - diabinho.CenterX())'
    per['actions'] = [a for a in per['actions'] if 'orbita' not in txt(a) and a['parameters'][:2] != ['diabinho', 'ang']]
    per['actions'] += [
        {'type': {'value': 'SetX'}, 'parameters': ['diabinho', '+', f'cos({ang}) * diabinho.velocidade * TimeDelta()']},
        {'type': {'value': 'SetY'}, 'parameters': ['diabinho', '+', f'sin({ang}) * diabinho.velocidade * TimeDelta()']}]
    tira(m['events'], lambda e: 'bote_espera' in conds(e) or estado(e, 'preparar') or estado(e, 'atacar'), 4)

    # sapo: a língua e a cura; sai o cuspe
    g = G['Sapo (cura, cuspe em arco e língua)']
    m = principal(g, 'sapo')
    tira(m['events'], lambda e: '"sapo.ataque_espera"' in conds(e) or estado(e, 'atacar'), 2)
    tira(g['events'], lambda e: e['type'].endswith('ForEach') and 'preparar' in conds(e), 1)

    # cutulu: só o salto
    g = G['Cutulu (elite)']
    m = principal(g, 'cutulu')
    for e in todos(m['events']):
        for a in e.get('actions') or []:
            if a['parameters'][:2] == ['cutulu', 'escolha'] and a['parameters'][3] == '3 - cutulu.escolha':
                a['parameters'][3] = '2'
    um = lambda e: '"escolha", "=", "1"' in conds(e)
    for e in todos(m['events']):
        if e.get('events'):
            e['events'] = [x for x in e['events'] if not um(x)]
    tira(m['events'], um, 1)

    # serafim: só os anéis
    g = G['Serafim (padrões de luz)']
    m = principal(g, 'serafim')
    for e in todos(m['events']):
        for a in e.get('actions') or []:
            if a['parameters'][:2] == ['serafim', 'padrao'] and a['parameters'][3] == '3 - serafim.padrao':
                a['parameters'][3] = '2'
    p1 = lambda e: '"padrao", "=", "1"' in conds(e)
    tira(m['events'], p1, 1)
    tira(g['events'], p1, 1)

    # nomes e comentários
    for velho, novo in NOMES.items():
        G[velho]['name'] = novo
    G = {e['name']: e for e in todos(ini) if e['type'].endswith('Group')}
    for nome, c in COMENTARIOS.items():
        coms = [e for e in G[nome]['events'] if e['type'].endswith('Comment')]
        coms[0]['comment'] = c
        G[nome]['events'] = [e for e in G[nome]['events'] if e not in coms[1:]]

    # variáveis que ficaram sem uso
    usado = txt([x['events'] for x in d['externalEvents']] + [l['events'] for l in d['layouts']])
    objs = {o['name']: o for o in d['objects']}
    for obj, nomes in SOBRAS.items():
        for v in nomes:
            if re.search(r'\b' + obj + r'\.' + v + r'\b', usado):
                sys.exit(f'{obj}.{v} ainda é usada; não removo')
        objs[obj]['variables'] = [x for x in objs[obj]['variables'] if x['name'] not in nomes]

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('um golpe por inimigo')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
