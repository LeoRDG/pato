"""Tarefa 131: folhas de eventos organizadas por assunto, só com grupos; cada grupo começa com uma frase curta.

Folhas (antes -> depois):
- Jogador + AplicarUpgrades -> Jogador (grupo Upgrades no fim; as cenas ligavam AplicarUpgrades logo depois de Jogador).
- Inimigos vira a folha genérica, de todo inimigo: Preparar inimigos, Paredes, Separação, Visão, Projéteis dos
  inimigos, Estados (terrestres) e Estados (voadores) (era Voadores (comum)). Paredes e Separação rodavam no fim,
  depois dos inimigos de cada reino, e passam para o começo (usam o que o quadro anterior deixou).
- Inimigos de cada reino na sua folha, ligada só nas cenas do reino (e no Teste), logo depois de Inimigos; cada inimigo
  vai para o reino da cena em que ele está:
  InimigosInferno: condenado azul, inchado e em chamas, caveira gigante e azul, cabeça voadora, diabinho, olho
    demoníaco, voador (bombardeiro) e Demônio chefe (comportamento, bolas de fogo, fumaça e rajada da fúria, que eram
    da folha Chefe).
  InimigosPurgatorio: pigman, sapo, árvore condenada, mina demoníaca, moscas (o cutulu as invoca) e Cutulu (Cutulu
    (elite) e a folha Cutulu).
  InimigosParaiso: querubim, serafim, ofanim, roda do anjo e morte dos anjos.
- HUD: Barras de chefe (do demônio, do cutulu e do mercador), depois do "esconder condicionais".
- CenarioInferno: Lava, Plataformas móveis, Fundo escuro e Sala do chefe (Arena, Fase 2, Câmera da luta e Moedas do
  chefe, que usam variáveis da cena Inferno e precisam rodar depois de Combate, como antes).
- CenarioPurgatorio: Plataformas radiais e Armadilhas. CenarioParaiso: Correntes de luz.
- Perigos: Espinhos e Poça de sangue (era Sangue), onde Espinhos e Sangue eram ligados.
- Combate, Loja e Portais ficam, com os eventos soltos em grupos.
Comentários: todos saem. Trechos soltos que um comentário separava viram grupos, e todo grupo começa com um único
comentário de uma frase dizendo o que ele faz. Nada de condição ou ação muda.
Rodar uma vez:  python3 tools/t131_organizar_eventos.py
"""
import copy, json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COR = (74, 176, 228)


def g(nome, evs):
    return {'type': 'BuiltinCommonInstructions::Group', 'colorB': COR[2], 'colorG': COR[1], 'colorR': COR[0],
            'creationTime': 0, 'name': nome, 'source': '', 'parameters': [], 'events': list(evs)}


def eh(e, t):
    return e.get('type') == 'BuiltinCommonInstructions::' + t


def link(alvo):
    return {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': alvo}


def coment(texto):
    return {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0,
            'textG': 0, 'textR': 0}, 'comment': texto, 'comment2': ''}


def por_comentario(evs, nomes):
    """trechos soltos: cada comentário abre um grupo com o nome dado (na ordem); grupos já prontos ficam."""
    out, atual, i = [], None, 0
    for e in evs:
        if eh(e, 'Comment'):
            atual = g(nomes[i], [e])
            out.append(atual)
            i += 1
        elif eh(e, 'Group'):
            out.append(e)
            atual = None
        else:
            if atual is None:
                raise ValueError('evento solto sem comentário antes')
            atual['events'].append(e)
    assert i == len(nomes), (i, nomes)
    return out


def tira(evs, nome):
    i = next(k for k, e in enumerate(evs) if e.get('name') == nome)
    return evs.pop(i)


def estrutura(d):
    X = {x['name']: x for x in d['externalEvents']}
    L = {l['name']: l for l in d['layouts']}

    # Jogador + AplicarUpgrades
    up = [e for e in X['AplicarUpgrades']['events'] if eh(e, 'Group')]
    X['Jogador']['events'].append(g('Upgrades', [c for c in X['AplicarUpgrades']['events'] if eh(c, 'Comment')][:1] + up))

    # Inimigos
    ini = X['Inimigos']['events']
    voa = tira(ini, 'Voadores (comum)')
    voa['name'] = 'Estados (voadores)'
    ini.insert(next(k for k, e in enumerate(ini) if e.get('name') == 'Estados (terrestres)') + 1, voa)
    inf = next(e for e in ini if e.get('name') == 'Inferno')
    infv = tira(ini, 'Inferno (voadores)')
    inf['events'] += infv['events']
    chefe = {e['name']: e for e in X['Chefe']['events'] if eh(e, 'Group')}
    topo_chefe = [c for c in X['Chefe']['events'] if eh(c, 'Comment')][:1]
    nucleo = chefe['Demônio chefe']
    nucleo['name'] = 'Comportamento'
    inf['events'].append(g('Demônio chefe', topo_chefe + [nucleo, chefe['Bolas de fogo'], chefe['Fumaça da fúria'],
                                                         chefe['Rajada da fúria']]))
    pur = next(e for e in ini if e.get('name') == 'Purgatório')
    elite = next(e for e in pur['events'] if e.get('name') == 'Cutulu (elite)')
    cut = [e for e in X['Cutulu']['events'] if eh(e, 'Group')]
    barra_cut = next(e for e in cut if e['name'] == 'Barra do chefe')
    cut.remove(barra_cut)
    for e in cut:
        if e['name'] == 'Começo dos ataques novos':
            e['name'] = 'Começo dos ataques'
    base = g('Andar, salto e fúria', elite['events'])
    elite['name'] = 'Cutulu'
    elite['events'] = [c for c in X['Cutulu']['events'] if eh(c, 'Comment')][:1] + [base] + cut

    # Inimigos: folha genérica + uma folha por reino
    reinos = {e['name']: e for e in ini if e.get('name') in ('Inferno', 'Purgatório', 'Céu')}
    por_nome = {gr['name']: gr for r in reinos.values() for gr in r['events'] if eh(gr, 'Group')}
    assert set(por_nome) == {n for ns in REINO.values() for n in ns}, set(por_nome) ^ {n for ns in REINO.values() for n in ns}
    comum = {e['name']: e for e in ini if eh(e, 'Group') and e['name'] not in reinos}
    X['Inimigos']['events'] = [comum[n] for n in ('Preparar inimigos', 'Paredes', 'Separação', 'Visão',
                                                  'Projéteis dos inimigos', 'Estados (terrestres)',
                                                  'Estados (voadores)')]
    assert len(comum) == 7
    for folha, nomes in REINO.items():
        d['externalEvents'].append({'associatedLayout': folha[len('Inimigos'):], 'name': folha,
                                    'events': [por_nome[n] for n in nomes]})

    # HUD: barras de chefe
    hud = next(e for e in X['HUD']['events'] if e.get('name') == 'HUD')
    barra_dem = chefe['Barra do chefe']
    barra_dem['name'] = 'Demônio chefe'
    barra_cut['name'] = 'Cutulu'
    loja = X['Loja']['events']
    barra_trader = tira(loja, 'Barra do mercador')
    barra_trader['name'] = 'Mercador'
    hud['events'].append(g('Barras de chefe', [barra_dem, barra_cut, barra_trader]))

    # Combate > Projéteis: soltos em grupos
    proj = next(e for e in X['Combate']['events'] if e.get('name') == 'Projéteis')
    ev = proj['events']
    i_ric = next(k for k, e in enumerate(ev) if eh(e, 'Comment') and e['comment'].startswith('Ricochete'))
    i_inv = next(k for k, e in enumerate(ev) if eh(e, 'Comment') and e['comment'].startswith('Bala em inimigo invuln'))
    ric, terreno = ev[i_ric:i_ric + 2], ev[i_ric + 2:i_inv]
    inv, dano = ev[i_inv:i_inv + 2], ev[i_inv + 2:]
    assert len(terreno) == 3 and len(dano) == 2, (len(terreno), len(dano))
    proj['events'] = ev[:i_ric] + [g('Ricochete', ric), g('Balas no terreno', terreno),
                                   g('Bala em inimigo invulnerável', inv), g('Dano da bala', dano)]

    # Portais: soltos em grupos
    pe = X['Portais']['events'][1:]                     # o 1º comentário é o da folha
    X['Portais']['events'] = por_comentario(pe, ['Hub do reino', 'Ponto de volta', 'Abrir e usar', 'Partículas'])
    au = X['Portais']['events'][2]['events']            # [coment, 3 Standard, 3 ForEach]
    au_c, au_e = au[0], au[1:]
    assert len(au_e) == 6
    X['Portais']['events'][2:3] = [g('Liberação do portal final', [au_c] + au_e[:3]), g('Abertura', au_e[3:4]),
                                   g('Entrar no portal', au_e[4:])]

    # folhas de cenário e perigos
    def grupos_de(nome, novo_nome=None):
        evs = X[nome]['events']
        cs = [e for e in evs if eh(e, 'Comment')][:1]
        gs = [e for e in evs if eh(e, 'Group')]
        soltos = [e for e in evs if not eh(e, 'Group') and not eh(e, 'Comment')]
        if soltos:
            gs.append(g(novo_nome or nome, soltos))
        if len(gs) == 1:
            gs[0]['events'] = cs + gs[0]['events']
            if novo_nome:
                gs[0]['name'] = novo_nome
        return gs
    sala = g('Sala do chefe', topo_chefe[:0] + [chefe['Arena'], chefe['Fase 2'], chefe['Câmera da luta'],
                                                chefe['Moedas do chefe']])
    novas = {
        'CenarioInferno': ('Inferno', grupos_de('Lava') + grupos_de('Plataformas') + grupos_de('FundoEscuro') + [sala]),
        'CenarioPurgatorio': ('Purgatorio', grupos_de('PlataformasRadiais') + [g('Armadilhas', [c for c in X['Armadilhas']['events'] if eh(c, 'Comment')][:1] + [e for e in X['Armadilhas']['events'] if eh(e, 'Group')])]),
        'CenarioParaiso': ('Paraiso', grupos_de('CorrentesDeLuz', 'Correntes de luz')),
        'Perigos': ('Purgatorio', grupos_de('Espinhos') + grupos_de('Sangue')),
    }
    fora = ['AplicarUpgrades', 'Chefe', 'Cutulu', 'Lava', 'Plataformas', 'FundoEscuro', 'PlataformasRadiais',
            'Armadilhas', 'CorrentesDeLuz', 'Espinhos', 'Sangue']
    d['externalEvents'] = [x for x in d['externalEvents'] if x['name'] not in fora]
    for nome, (cena, evs) in novas.items():
        d['externalEvents'].append({'associatedLayout': cena, 'name': nome, 'events': evs})

    # links nas cenas: cada folha velha vira a nova no lugar da primeira delas; as outras saem
    troca = {'AplicarUpgrades': None, 'Chefe': None, 'Cutulu': None,
             'Lava': 'CenarioInferno', 'Plataformas': 'CenarioInferno', 'FundoEscuro': 'CenarioInferno',
             'PlataformasRadiais': 'CenarioPurgatorio', 'Armadilhas': 'CenarioPurgatorio',
             'CorrentesDeLuz': 'CenarioParaiso', 'Espinhos': 'Perigos', 'Sangue': 'Perigos'}
    for l in d['layouts']:
        novo, ja = [], set()
        for e in l['events']:
            if eh(e, 'Link') and e['target'] == 'Inimigos':
                novo.append(e)
                novo += [link(f) for f in REINOS_DA_CENA[l['name']]]
                continue
            if eh(e, 'Link') and e['target'] in troca:
                alvo = troca[e['target']]
                if alvo and alvo not in ja:
                    novo.append(link(alvo))
                    ja.add(alvo)
                continue
            novo.append(e)
        l['events'] = novo

    # eventos soltos das cenas em grupos
    for l in d['layouts']:
        evs = [e for e in l['events'] if not (eh(e, 'Comment') and e is l['events'][0])]
        out, i = [], 0
        while i < len(evs):
            e = evs[i]
            if eh(e, 'Comment') and i + 1 < len(evs) and evs[i + 1]['type'].endswith(('Standard', 'ForEach')):
                out.append(g('Queda da borda' if 'queda_y' in e['comment'] else 'Eventos', [e, evs[i + 1]]))
                i += 2
                continue
            if e['type'].endswith(('Standard', 'ForEach')):
                s = json.dumps(e)
                nome = ('Fundo em parallax' if 'bg_inferno_escuro' in s else
                        'Ir para o Hub' if l['name'] == 'Menu' else
                        'Placas das salas' if 'rotulo_teste' in s else 'Eventos')
                out.append(g(nome, [e]))
                i += 1
                continue
            out.append(e)
            i += 1
        l['events'] = out


def todos(evs, caminho=''):
    for e in evs:
        if eh(e, 'Group'):
            yield caminho + '/' + e['name'], e
            yield from todos(e.get('events') or [], caminho + '/' + e['name'])
        else:
            yield from todos(e.get('events') or [], caminho)


def primeira_frase(t):
    t = ' '.join(t.split())
    for sep in ('. ', ': '):
        if sep in t:
            t = t[:t.index(sep)]
    return t.rstrip('.')


def candidatos(d):
    out = {}
    for onde, evs in [('F:' + x['name'], x['events']) for x in d['externalEvents']] + \
                     [('C:' + l['name'], l['events']) for l in d['layouts']]:
        for cam, e in todos(evs, onde):
            c = next((x['comment'] for x in e['events'] if eh(x, 'Comment')), None)
            out[cam] = primeira_frase(c) if c else None
    return out


def sem_comentarios(evs):
    out = []
    for e in evs:
        if eh(e, 'Comment'):
            continue
        if e.get('events'):
            e['events'] = sem_comentarios(e['events'])
        out.append(e)
    return out


def main(caminho, so_listar=False):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(x['name'] == 'CenarioInferno' for x in d['externalEvents']):
        sys.exit('t131 já foi aplicada; não roda de novo.')
    estrutura(d)
    cand = candidatos(d)
    if so_listar:
        for k, v in cand.items():
            print(k, '=>', v)
        return
    faltam = [k for k in cand if k not in FRASES]
    assert not faltam, faltam
    for x in d['externalEvents']:
        x['events'] = sem_comentarios(x['events'])
    for l in d['layouts']:
        l['events'] = sem_comentarios(l['events'])
    for onde, evs in [('F:' + x['name'], x['events']) for x in d['externalEvents']] + \
                     [('C:' + l['name'], l['events']) for l in d['layouts']]:
        for cam, e in todos(evs, onde):
            e['events'].insert(0, coment(FRASES[cam]))

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('eventos organizados:', len(FRASES), 'grupos')


REINO = {
    'InimigosInferno': ['Condenado azul (investida)', 'Condenado inchado (bolsa de bile)', 'Caveira gigante',
                        'Condenado em chamas (frenesi)', 'Caveira azul (quica)', 'Cabeça voadora (investida mirada)',
                        'Diabinho (ladrão)', 'Olho demoníaco (raio)', 'Voador (bombardeiro)', 'Demônio chefe'],
    'InimigosPurgatorio': ['Pigman (pancada)', 'Sapo (cura e língua)', 'Árvore condenada (espinheiro)',
                           'Mina demoníaca (explode ao morrer)', 'Moscas (enxame com inércia)', 'Cutulu'],
    'InimigosParaiso': ['Querubim (arqueiro)', 'Serafim (padrões de luz)', 'Ofanim (roda de olhos)', 'Roda do anjo',
                        'Morte dos anjos (partículas de luz)'],
}
REINOS_DA_CENA = {'Inferno': ['InimigosInferno'], 'Purgatorio': ['InimigosPurgatorio'],
                  'Paraiso': ['InimigosParaiso'], 'Teste': list(REINO)}
FRASES = {
    'F:Jogador/Mouse preso': 'O primeiro clique trava o ponteiro; o mouse move um cursor virtual preso na tela.',
    'F:Jogador/Inicio da Cena': 'Prepara o pato no começo da cena.',
    'F:Jogador/Inicio da Cena/Preload dos sons': 'Carrega os sons antes de tocar.',
    'F:Jogador/Inicio da Cena/Criacao das Armas': 'Cria as armas e prende no pato.',
    'F:Jogador/Controle do Pato': 'Tudo o que o pato faz.',
    'F:Jogador/Controle do Pato/Movimento': 'Andar, pular e cair.',
    'F:Jogador/Controle do Pato/Movimento/pulo no ar e giro em direcao do movimento': 'Pulo no ar com giro para o lado do movimento.',
    'F:Jogador/Controle do Pato/Cagada no pulo e dash': 'Solta a cagada no pulo no ar e no dash.',
    'F:Jogador/Controle do Pato/Morte do Pato': 'Morte do pato e volta ao hub.',
    'F:Jogador/Controle do Pato/Feel do pato': 'Detalhes que deixam o controle gostoso.',
    'F:Jogador/Controle do Pato/Feel do pato/Buffer de pulo': 'Pulo apertado pouco antes de tocar o chão ainda vale.',
    'F:Jogador/Controle do Pato/Feel do pato/Poeira': 'Poeira ao pousar e correr.',
    'F:Jogador/Controle do Pato/Bunny hop': 'Pular logo ao pousar mantém e aumenta a velocidade.',
    'F:Jogador/Controle do Pato/Animacoes': 'Escolhe a animação do pato pelo que ele está fazendo.',
    'F:Jogador/Controle do Pato/Chao nao sai da camera': 'A câmera não deixa o chão mais baixo sair da tela.',
    'F:Jogador/Controle do Pato/Empurrão no pato': 'Empurrão de lado (coice_vx) que freia aos poucos.',
    'F:Jogador/Controle das Armas': 'Mira, troca, tiro e recarga das armas.',
    'F:Jogador/Controle das Armas/Mira e posicionamento': 'A arma segue a mira em volta do pato.',
    'F:Jogador/Controle das Armas/Mira e posicionamento/Angulo': 'Ângulo da arma até a mira.',
    'F:Jogador/Controle das Armas/Mira e posicionamento/Posicao da arma': 'Põe a arma na mão do pato.',
    'F:Jogador/Controle das Armas/Mira e posicionamento/Cano e alvo': 'Ponta do cano e alvo do tiro.',
    'F:Jogador/Controle das Armas/Mira e posicionamento/Recuo': 'Recuo visual da arma ao atirar.',
    'F:Jogador/Controle das Armas/Mira e posicionamento/Flipa a Arma para nao ficar de cabeca para baixo ao girar': 'Espelha a arma para não ficar de cabeça para baixo.',
    'F:Jogador/Controle das Armas/Mira e posicionamento/Clarão': 'Clarão na ponta do cano.',
    'F:Jogador/Controle das Armas/Troca de Arma': 'Troca de arma pelos números e pela rodinha.',
    'F:Jogador/Controle das Armas/Tiro': 'Dispara a arma equipada.',
    'F:Jogador/Controle das Armas/Recarga': 'Recarrega o pente.',
    'F:Jogador/Controle das Armas/Recuo': 'Empurra o pato para trás ao atirar.',
    'F:Jogador/Controle das Armas/Muzzle Flash': 'Fogo na boca do cano a cada tiro.',
    'F:Jogador/Controle das Armas/Giro da minigun': 'O cano da minigun gira antes de atirar.',
    'F:Jogador/Controle das Armas/Sons': 'Sons das armas.',
    'F:Jogador/Controle das Armas/Sons/Tiro': 'Som de cada tiro.',
    'F:Jogador/Controle das Armas/Sons/Recarga': 'Som de cada recarga.',
    'F:Jogador/Upgrades': 'Upgrades permanentes comprados na loja.',
    'F:Jogador/Upgrades/Aplicar upgrades': 'Aplica os níveis de upgrade no pato e nas armas no começo da cena.',
    'F:Jogador/Upgrades/Debug (remover antes da entrega)': 'F1 dá +500 moedas para testar a loja.',
    'F:Inimigos/Preparar inimigos': 'Zera cronômetros, guarda a posição inicial e ajusta a vida de cada inimigo.',
    'F:Inimigos/Visão': 've_pato: o inimigo está na tela e sem parede entre ele e o pato.',
    'F:Inimigos/Projéteis dos inimigos': 'Gravidade, giro, tempo de vida e bomba dos projéteis inimigos.',
    'F:Inimigos/Estados (terrestres)': 'Patrulha, perseguir, preparar, atacar e tranco dos inimigos de chão.',
    'F:Inimigos/Estados (voadores)': 'Perseguir, desistir e tranco dos inimigos que voam.',
    'F:Inimigos/Inferno': 'Inimigos do Inferno.',
    'F:Inimigos/Inferno/Condenado azul (investida)': 'Ruge e corre em linha reta até o pato, com soco no fim.',
    'F:Inimigos/Inferno/Condenado inchado (bolsa de bile)': 'Acelera perto do pato e explode em bile.',
    'F:Inimigos/Inferno/Árvore condenada (espinheiro)': 'Parada; treme e atira um leque de espinhos no pato.',
    'F:Inimigos/Inferno/Caveira gigante': 'Mini-chefe que voa em oito sobre o pato e cospe fogo.',
    'F:Inimigos/Inferno/Condenado em chamas (frenesi)': 'Com pouca vida se inflama e corre em frenesi.',
    'F:Inimigos/Inferno/Caveira azul (quica)': 'Quica em diagonal em volta do pato.',
    'F:Inimigos/Inferno/Cabeça voadora (investida mirada)': 'Paira, mira e dispara em linha reta no pato.',
    'F:Inimigos/Inferno/Diabinho (ladrão)': 'Rouba moedas e foge; morto, devolve.',
    'F:Inimigos/Inferno/Moscas (enxame com inércia)': 'Enxame que passa direto e faz a curva.',
    'F:Inimigos/Inferno/Olho demoníaco (raio)': 'Mira com uma linha fina e dispara um raio.',
    'F:Inimigos/Inferno/Mina demoníaca (explode ao morrer)': 'Vai até o pato e explode, também ao morrer.',
    'F:Inimigos/Inferno/Demônio chefe': 'Chefe do Inferno (a sala e a fase 2 ficam em CenarioInferno).',
    'F:Inimigos/Inferno/Demônio chefe/Comportamento': 'Passo, golpes de cutelo e explosão, e a fúria.',
    'F:Inimigos/Inferno/Demônio chefe/Bolas de fogo': 'Bolas de fogo soltas pelo demônio.',
    'F:Inimigos/Inferno/Demônio chefe/Fumaça da fúria': 'Fumaça que segue o demônio em fúria.',
    'F:Inimigos/Inferno/Demônio chefe/Rajada da fúria': 'Em fúria, a explosão vira uma rajada de anéis de fogo girando.',
    'F:Inimigos/Purgatório': 'Inimigos do Purgatório.',
    'F:Inimigos/Purgatório/Pigman (pancada)': 'Salta em cima do pato e solta ondas de choque ao cair.',
    'F:Inimigos/Purgatório/Sapo (cura e língua)': 'Cura os inimigos perto e puxa o pato com a língua.',
    'F:Inimigos/Purgatório/Cutulu': 'Chefe do Purgatório, em três fases.',
    'F:Inimigos/Purgatório/Cutulu/Andar, salto e fúria': 'Persegue, salta sobre o pato com anel de bile e entra em fúria.',
    'F:Inimigos/Purgatório/Cutulu/Preparo e fases': 'Vida de chefe, troca de fase e rugido.',
    'F:Inimigos/Purgatório/Cutulu/Escolha do ataque': 'Sorteia o próximo ataque, sem repetir, e mostra o aviso dele.',
    'F:Inimigos/Purgatório/Cutulu/Começo dos ataques': 'Começa o ataque sorteado quando o aviso acaba.',
    'F:Inimigos/Purgatório/Cutulu/Golpes': 'Rasgo de energia e chicote de tentáculos, com caixa de acerto à frente.',
    'F:Inimigos/Purgatório/Cutulu/Mergulho': 'Some no alto, a sombra segue o pato e ele despenca nela.',
    'F:Inimigos/Purgatório/Cutulu/Espiral de olhos': 'Paira e solta braços de olhos girando.',
    'F:Inimigos/Purgatório/Cutulu/Chuva de bile': 'Cospe bile em arco que cai em volta do pato.',
    'F:Inimigos/Purgatório/Cutulu/Invocação': 'Invoca moscas, que morrem junto com ele.',
    'F:Inimigos/Purgatório/Cutulu/Ondas do salto e combos': 'Ondas no chão ao pousar do salto e combos na fase 3.',
    'F:Inimigos/Purgatório/Cutulu/Postura': 'Tiro não o trava; cambaleia só de vez em quando.',
    'F:Inimigos/Purgatório/Voador (bombardeiro)': 'Passa sobre o pato soltando bombas.',
    'F:Inimigos/Céu': 'Inimigos do Paraíso.',
    'F:Inimigos/Céu/Querubim (arqueiro)': 'Atira flechas mirando onde o pato vai estar.',
    'F:Inimigos/Céu/Serafim (padrões de luz)': 'Solta anéis de luz com um buraco para passar.',
    'F:Inimigos/Céu/Ofanim (roda de olhos)': 'Fechado reflete as balas; aberto atira olhos.',
    'F:Inimigos/Céu/Roda do anjo': 'Rola até o pato e investe quando alinhada.',
    'F:Inimigos/Céu/Morte dos anjos (partículas de luz)': 'Estouro de luz quando um anjo morre.',
    'F:Inimigos/Paredes': 'Encostado numa parede: pula perseguindo, dá meia-volta patrulhando.',
    'F:Inimigos/Separação': 'Inimigos encostados uns nos outros se afastam.',
    'F:Combate/Dano e invencibilidade': 'Encostar em inimigo ou levar tiro tira vida, empurra e dá invencibilidade.',
    'F:Combate/Projéteis': 'Balas, granadas e ricochetes do jogador.',
    'F:Combate/Projéteis/Balas (alcance, queda e perfuração)': 'A bala copia os valores da arma e perde dano com a distância.',
    'F:Combate/Projéteis/Gravidade da granada': 'Granada cai em arco.',
    'F:Combate/Projéteis/Explosão da granada': 'Granada explode no chão ou num inimigo.',
    'F:Combate/Projéteis/Dano da explosão': 'Explosão tira vida de quem está perto, menos quanto mais longe.',
    'F:Combate/Projéteis/Ricochete': 'Bala com ricochete sobrando quica no terreno.',
    'F:Combate/Projéteis/Balas no terreno': 'Balas sem ricochete somem no terreno.',
    'F:Combate/Projéteis/Bala em inimigo invulnerável': 'Bala em inimigo invulnerável faz ping e pode voltar no pato.',
    'F:Combate/Projéteis/Dano da bala': 'Bala tira vida do inimigo, com sangue e som de acerto.',
    'F:Combate/Sons de dano': 'Quack quando o pato perde vida.',
    'F:Combate/Feedback': 'Números de dano e de moedas que sobem e somem.',
    'F:Combate/Morte do Inimigo': 'Marca o inimigo morto, solta moedas, anima e deleta.',
    'F:Combate/Barra de Vida': 'Barrinha de vida em cima de cada inimigo.',
    'F:Combate/Moeda': 'Moedas soltas pelos inimigos.',
    'F:Combate/Moeda/Aparência': 'Moeda de 1, 5 ou 10 pelo valor.',
    'F:Combate/Moeda/Física': 'Moedas pulam em arco e quicam até parar.',
    'F:Combate/Moeda/Ímã e sumiço': 'Perto do pato são puxadas; somem piscando depois de um tempo.',
    'F:Combate/Moeda/Coleta': 'Pegar soma as moedas e mostra +N.',
    'F:Combate/Eletricidade': 'Upgrade: raios entre as balas dão dano em quem está no meio.',
    'F:HUD/HUD': 'Interface na tela.',
    'F:HUD/HUD/Esconder condicionais': 'Esconde o que é condicional; os grupos abaixo mostram o que precisa.',
    'F:HUD/HUD/Vida e moedas': 'Barra de vida, moedas e vinheta de dano.',
    'F:HUD/HUD/Arma': 'Ícone, nome, munição e recarga da arma.',
    'F:HUD/HUD/Slots': 'Slot da arma equipada e cadeado nas bloqueadas.',
    'F:HUD/HUD/Tempo': 'Tempo de jogo.',
    'F:HUD/HUD/Barras de chefe': 'Barra de vida de chefe no alto da tela.',
    'F:HUD/HUD/Barras de chefe/Demônio chefe': 'Barra do demônio com o pato perto.',
    'F:HUD/HUD/Barras de chefe/Cutulu': 'Barra do cutulu com o pato perto.',
    'F:HUD/HUD/Barras de chefe/Mercador': 'Barra do mercador quando ele fica hostil.',
    'F:Loja/Dica': 'Mostra um E sobre o mercador com o pato perto.',
    'F:Loja/Abrir e fechar': 'E abre a loja perto do mercador; E ou Esc fecham.',
    'F:Loja/Menu': 'Monta as linhas do catálogo e escolhe com W/S ou o mouse.',
    'F:Loja/Compra': 'Compra a linha escolhida se der.',
    'F:Loja/Mercador': 'Mercador fica hostil se apanhar demais.',
    'F:Loja/Mercador/Ataques do trader': 'A fazer: ataques do mercador hostil.',
    'F:Loja/Mercador/Quando o trader morre': 'A decidir: o que muda quando o mercador morre.',
    'F:Portais/Hub do reino': 'Portal para "Hub" leva ao hub do reino da cena.',
    'F:Portais/Ponto de volta': 'Voltando para a fase, o pato começa onde entrou no portal.',
    'F:Portais/Liberação do portal final': 'O portal final só abre depois que o chefe morre.',
    'F:Portais/Abertura': 'Abre o portal liberado, com o nome em cima.',
    'F:Portais/Entrar no portal': 'Ficar dentro do portal por um tempo troca de cena.',
    'F:Portais/Partículas': 'Efeito de partículas girando em cada portal.',
    'F:CenarioInferno/Lava': 'Lava com brasas e bolhas.',
    'F:CenarioInferno/Plataformas móveis': 'Plataformas que vão e voltam.',
    'F:CenarioInferno/Fundo escuro': 'Troca para o fundo escuro conforme o pato sobe.',
    'F:CenarioInferno/Sala do chefe': 'A sala do demônio chefe e a luta na lava.',
    'F:CenarioInferno/Sala do chefe/Arena': 'Portões que trancam a luta e abrem quando o demônio morre.',
    'F:CenarioInferno/Sala do chefe/Fase 2': 'O piso quebra e a luta continua na lava.',
    'F:CenarioInferno/Sala do chefe/Câmera da luta': 'Na luta a câmera mira entre o pato e o demônio.',
    'F:CenarioInferno/Sala do chefe/Moedas do chefe': 'Moedas do demônio morto na lava voam para as pontes.',
    'F:CenarioPurgatorio/Plataformas radiais': 'Rodas de troncos girando.',
    'F:CenarioPurgatorio/Armadilhas': 'Armadilhas da escalada final.',
    'F:CenarioPurgatorio/Armadilhas/Lajes que somem': 'Laje pisada treme, some e volta.',
    'F:CenarioPurgatorio/Armadilhas/Jatos de fogo purificador': 'Jatos de fogo branco com aviso.',
    'F:CenarioPurgatorio/Armadilhas/Ácido': 'Ácido machuca quem encosta.',
    'F:CenarioParaiso/Correntes de luz': 'Colunas de luz que acendem e apagam em ciclo.',
    'F:Perigos/Espinhos': 'Espinhos machucam e jogam o pato para fora.',
    'F:Perigos/Poça de sangue': 'Quem anda no sangue fica lento.',
    'C:Menu/Ir para o Hub': 'Sem menu ainda: vai direto para o Hub.',
    'C:Hub/Saída': 'Desativado: a saída agora é pelos portais.',
    'C:Hub/Fundo em parallax': 'Fundo do Inferno anda com a câmera.',
    'C:Hub/Queda da borda': 'Cair da borda volta o pato para o lugar seguro.',
    'C:HubPurgatorio/Saída': 'Desativado: a saída agora é pelos portais.',
    'C:HubPurgatorio/Fundo em parallax': 'Fundo do Purgatório anda com a câmera.',
    'C:HubPurgatorio/Queda da borda': 'Cair da borda volta o pato para o lugar seguro.',
    'C:HubParaiso/Saída': 'Desativado: a saída agora é pelos portais.',
    'C:HubParaiso/Fundo em parallax': 'Fundo do Paraíso anda com a câmera.',
    'C:HubParaiso/Queda da borda': 'Cair da borda volta o pato para o lugar seguro.',
    'C:Inferno/Fundo em parallax': 'Fundo anda com a câmera.',
    'C:Purgatorio/Fundo em parallax': 'Fundo anda com a câmera, os planos de longe mais devagar.',
    'C:Purgatorio/Saída no cume': 'Vazio.',
    'C:Paraiso/Fundo em parallax': 'Fundo anda com a câmera.',
    'C:Paraiso/Queda do céu': 'Cair das nuvens tira vida e volta o pato para onde pisou.',
    'C:Paraiso/Saída no Empíreo': 'Chegar ao Empíreo leva para a próxima cena.',
    'C:Teste/Placas das salas': 'Cada placa mostra o texto da sua sala.',
}

def _remapeia(fr):
    folha_de = {n: f for f, ns in REINO.items() for n in ns}
    out = {}
    for k, v in fr.items():
        partes = k.split('/')
        if partes[0] == 'F:Inimigos' and partes[1] in ('Inferno', 'Purgatório', 'Céu'):
            if len(partes) == 2:
                continue
            k = '/'.join(['F:' + folha_de[partes[2]]] + partes[2:])
        out[k] = v
    return out


FRASES = _remapeia(FRASES)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--listar']
    main(args[0] if args else os.path.join(RAIZ, 'jogo.json'), '--listar' in sys.argv)
