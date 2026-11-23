"""Ricochete: bala do jogador quica no terreno como num espelho, perde dano a cada ricochete; 1 nível = 1 ricochete."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def obj(nome):
    return next(o for o in JOGO['objects'] if o['name'] == nome)


def v(o, nome):
    return next(x for x in o['variables'] if x['name'] == nome)


def glob(nome):
    return next(x for x in JOGO['variables'] if x['name'] == nome)


PROJ = next(e for e in next(x for x in JOGO['externalEvents'] if x['name'] == 'Combate')['events'] if e.get('name') == 'Projéteis')
# t131 juntou os eventos soltos de Projéteis em grupos; aqui eles voltam a ficar em sequência, na mesma ordem
_SOLTOS = {'Ricochete', 'Balas no terreno', 'Bala em inimigo invulnerável', 'Dano da bala'}
PROJ = dict(PROJ, events=[x for e in PROJ['events']
                          for x in (e['events'] if e.get('name') in _SOLTOS else [e])
                          if not x['type'].endswith('Comment')])


def test_upgrade_no_catalogo():
    itens = [{c['name']: c['value'] for c in i['children']} for i in glob('loja_catalogo')['children']]
    ric = [i for i in itens if i['id'] == 'ricochete']
    assert len(ric) == 1 and ric[0]['tipo'] == 'upgrade' and ric[0]['nivel_max'] >= 1
    assert any(c['name'] == 'ricochete' for c in glob('upgrades')['children'])
    assert 0 < v(obj('pato'), 'ricochete_perda')['value'] < 1


def test_sem_limite_de_alcance():
    # o alcance some, mas a queda de dano continua terminando onde terminava (queda_fim = alcance antigo)
    for arma, fim in (('pistola', 99999), ('doze', 450), ('minigun', 700), ('lanca', 99999)):
        assert v(obj(arma), 'alcance')['value'] >= 99999, arma
        assert v(obj(arma), 'queda_fim')['value'] == fim, arma


def test_queda_pelo_caminho_percorrido():
    balas = next(e for e in PROJ['events'] if e.get('name') == 'Balas (alcance, queda e perfuração)')
    texto = json.dumps(balas)
    assert 'projetil.ox, projetil.oy' not in texto
    assert texto.count('projetil.percorrido') >= 2
    assert 'max(1, projetil.queda_fim - projetil.queda_ini)' in texto
    nasce = balas['events'][0]
    assert any(a['parameters'][:4] == ['projetil', 'ricochetes', '=', 'GlobalVariable(upgrades.ricochete)'] for a in nasce['actions'])
    assert any(a['parameters'][:4] == ['projetil', 'queda_fim', '=', 'Arma.queda_fim'] for a in nasce['actions'])


def test_ricochete_antes_de_apagar_no_terreno():
    evs = PROJ['events']
    apaga = next(i for i, e in enumerate(evs) if e.get('type') == 'BuiltinCommonInstructions::Standard'
                 and any(c['parameters'][:2] == ['projetil', 'Terreno'] for c in e.get('conditions') or [])
                 and any(a['type']['value'] == 'Delete' for a in e['actions']))
    ric = next(i for i, e in enumerate(evs) if any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or []))
    assert ric < apaga
    e = evs[ric]
    assert e['type'] == 'BuiltinCommonInstructions::ForEach'
    assert not any(c['parameters'][:2] == ['projetil', 'raio'] for c in e['conditions'])  # a granada também quica
    tudo = json.dumps(e)
    assert '"gy", "*", "1 - 2 * projetil.ric_y"' in tudo  # espelha a gravidade da granada
    assert '"dano_explosao", "*", "1 - pato.ricochete_perda"' in tudo
    assert '"Arreter"' in tudo and '"AddForceXY"' in tudo
    assert '1 - pato.ricochete_perda' in tudo
    assert '"ricochetes", "-", "1"' in tudo
    # posição anterior guardada no fim do quadro, depois de tudo que usa ela
    guarda = next(i for i, x in enumerate(evs) if any(a['parameters'][:4] == ['projetil', 'px', '=', 'projetil.X()'] for a in x.get('actions') or []))
    assert guarda > apaga


def test_granada_explode_a_cada_ricochete_sem_sumir():
    exp = next(e for e in PROJ['events'] if e.get('name') == 'Explosão da granada')['events']
    boom = next(i for i, e in enumerate(exp) if any(c['parameters'][:3] == ['projetil', 'boom', 'True'] for c in e.get('conditions') or []))
    marca = next(i for i, e in enumerate(exp) if any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or []))
    assert marca < boom
    m = exp[marca]
    assert m['type'] == 'BuiltinCommonInstructions::ForEach'
    assert any(c['parameters'][:3] == ['projetil', 'raio', '>'] for c in m['conditions'])
    assert any(c['parameters'][:2] == ['projetil', 'Terreno'] for c in m['conditions'])
    assert {tuple(a['parameters'][:3]) for a in m['actions']} >= {('projetil', 'quica', 'True'), ('projetil', 'boom', 'True')}
    b = exp[boom]
    assert not any(a['type']['value'] == 'Delete' for a in b['actions'])  # só some quando não vai quicar
    subs = b['events']
    apaga = next(s for s in subs if any(c['parameters'][:3] == ['projetil', 'quica', 'False'] for c in s['conditions']))
    assert any(a['type']['value'] == 'Delete' for a in apaga['actions'])
    fica = next(s for s in subs if any(c['parameters'][:3] == ['projetil', 'quica', 'True'] for c in s['conditions']))
    assert {tuple(a['parameters'][:3]) for a in fica['actions']} >= {('projetil', 'boom', 'False'), ('projetil', 'quica', 'False')}
    assert any(x['name'] == 'quica' for x in obj('projetil')['variables'])


def test_angulo_do_ricochete_nao_enfia_a_mascara_no_terreno():
    # a máscara fica na frente do sprite: girar pela força sem a gravidade enfiava a granada no chão e ela era apagada
    ric = next(e for e in PROJ['events'] if e.get('type') == 'BuiltinCommonInstructions::ForEach'
               and any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or []))
    final = ric['events'][-1]
    gira = [a for a in final['actions'] if a['type']['value'] == 'SetAngle']
    assert [a['parameters'][2] for a in gira] == ['ToDeg(atan2(projetil.fy + projetil.gy, projetil.fx))']
    nomes = [a['parameters'][:2] for a in final['actions']]
    assert nomes.index(['projetil', 'gy']) < final['actions'].index(gira[0])  # gravidade já espelhada
    assert final['actions'][final['actions'].index(gira[0]) - 1]['parameters'][:4] == ['projetil', 'ang', '=', 'projetil.Angle()']
    volta = final['events'][-1]
    assert volta['conditions'][0]['parameters'][:2] == ['projetil', 'Terreno']
    assert volta['actions'][0]['parameters'] == ['projetil', '=', 'projetil.ang']


def test_granada_perde_velocidade_ao_quicar():
    assert v(obj('lanca'), 'ricochete_vel')['value'] < 1
    for arma in ('pistola', 'doze', 'minigun'):
        assert 0 < v(obj(arma), 'ricochete_vel')['value'] <= 1, arma
    balas = next(e for e in PROJ['events'] if e.get('name') == 'Balas (alcance, queda e perfuração)')
    assert any(a['parameters'][:4] == ['projetil', 'ricochete_vel', '=', 'Arma.ricochete_vel'] for a in balas['events'][0]['actions'])
    ric = next(e for e in PROJ['events'] if e.get('type') == 'BuiltinCommonInstructions::ForEach'
               and any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or []))
    acts = [a['parameters'][:4] for a in ric['events'][-1]['actions']]
    for nome in ('fx', 'fy', 'gy'):
        assert ['projetil', nome, '*', 'projetil.ricochete_vel'] in acts, nome
    # amortece antes de aplicar a força nova
    assert acts.index(['projetil', 'fy', '*', 'projetil.ricochete_vel']) < next(
        i for i, a in enumerate(ric['events'][-1]['actions']) if a['type']['value'] == 'AddForceXY')


def test_usa_expressoes_de_forca_que_existem():
    # GDevelop chama de ForceX()/ForceY(); TotalForceX() não existe e vale 0 (a bala parava no chão)
    tudo = json.dumps(PROJ)
    assert 'TotalForce' not in tudo
    assert 'projetil.ForceX() * (1 - 2 * projetil.ric_x)' in tudo and 'projetil.ForceY() * (1 - 2 * projetil.ric_y)' in tudo
