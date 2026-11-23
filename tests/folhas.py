"""Onde ficou cada folha de eventos antiga depois da reorganização (tools/t131_organizar_eventos.py).

folha(d, nome) devolve a lista de eventos do assunto da folha antiga, com os grupos de topo com o nome antigo (cópias
rasas), para os testes continuarem procurando os mesmos grupos.
"""
import copy


def _acha(evs, nome):
    for e in evs:
        if e.get('name') == nome:
            return e
        r = _acha(e.get('events') or [], nome)
        if r:
            return r
    return None


def _grupo(evs, nome):
    r = _acha(evs, nome)
    if r is None:
        raise KeyError(nome)
    return r


def _com_nome(g, nome):
    c = copy.copy(g)
    c['name'] = nome
    return c


def _filhos(g):
    return [e for e in g['events'] if not e.get('type', '').endswith('Comment')]


def folha(d, nome):
    X = {x['name']: x['events'] for x in d['externalEvents']}
    if nome in X:
        return X[nome]
    if nome == 'Chefe':
        dem = _grupo(X['InimigosInferno'], 'Demônio chefe')
        sala = _grupo(X['CenarioInferno'], 'Sala do chefe')
        return ([_com_nome(_grupo(dem['events'], 'Comportamento'), 'Demônio chefe')]
                + [g for g in _filhos(dem) if g['name'] != 'Comportamento'] + _filhos(sala))
    if nome == 'Cutulu':
        cut = _grupo(X['InimigosPurgatorio'], 'Cutulu')
        return [g for g in _filhos(cut) if g['name'] != 'Andar, salto e fúria']
    simples = {'Lava': ('CenarioInferno', 'Lava'), 'Plataformas': ('CenarioInferno', 'Plataformas móveis'),
               'FundoEscuro': ('CenarioInferno', 'Fundo escuro'), 'Sangue': ('CenarioInferno', 'Poça de sangue'),
               'Espinhos': ('CenarioPurgatorio', 'Espinhos'), 'PlataformasRadiais': ('CenarioPurgatorio', 'Plataformas radiais')}
    if nome in simples:
        f, g = simples[nome]
        return [_grupo(X[f], g)]
    if nome == 'Armadilhas':
        return _filhos(_grupo(X['CenarioPurgatorio'], 'Armadilhas'))
    if nome == 'CorrentesDeLuz':
        cena = next(l for l in d['layouts'] if l['name'] == 'Paraiso')
        return _filhos(_grupo(cena['events'], 'Correntes de luz'))
    if nome == 'AplicarUpgrades':
        return _filhos(_grupo(X['Jogador'], 'Upgrades'))
    raise KeyError(nome)


def inimigos_todos(d):
    """a folha Inimigos antiga: a genérica e as dos reinos."""
    X = {x['name']: x['events'] for x in d['externalEvents']}
    return X['Inimigos'] + X['InimigosInferno'] + X['InimigosPurgatorio'] + X['InimigosParaiso']
