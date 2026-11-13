"""Ajudantes para migrações de uso único do jogo.json (tNN_*.py) que só ADICIONAM o que falta.

Regra (CLAUDE.md): nunca reescrever valores existentes; se algo já existe, mantém como está.
"""
import copy, json, os, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(RAIZ, 'jogo.json')


def carrega():
    return json.load(open(PATH, encoding='utf-8'))


def salva(d):
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


def _uid():
    return str(uuid.uuid4())


def var(nome, valor):
    if isinstance(valor, bool):
        tipo = 'boolean'
    elif isinstance(valor, str):
        tipo = 'string'
    else:
        tipo = 'number'
    return {'name': nome, 'persistentUuid': _uid(), 'type': tipo, 'value': valor}


def estrutura(nome, filhos):
    """filhos: dict nome -> valor (ou lista de dicts de variável já prontos)."""
    if isinstance(filhos, dict):
        filhos = [var(k, v) for k, v in filhos.items()]
    v = {'type': 'structure', 'persistentUuid': _uid(), 'children': filhos}
    if nome is not None:
        v = {'name': nome, **v}
    return v


def lista(nome, itens):
    """Array do GDevelop; os filhos de um array não têm nome."""
    return {'name': nome, 'persistentUuid': _uid(), 'type': 'array', 'children': itens}


def adiciona_var(lista_vars, v):
    """Adiciona a variável se o nome ainda não existe. Devolve True se adicionou."""
    if any(x['name'] == v['name'] for x in lista_vars):
        return False
    lista_vars.append(v)
    return True


def acha_var(lista_vars, nome):
    return next((x for x in lista_vars if x['name'] == nome), None)


def objeto(d, nome):
    return next((o for o in d['objects'] if o['name'] == nome), None)


def cena(d, nome):
    return next(l for l in d['layouts'] if l['name'] == nome)


def externo(d, nome):
    return next((x for x in d['externalEvents'] if x['name'] == nome), None)


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def copia_objeto(d, origem, nome, **mudancas):
    """Cria um objeto global copiando outro (se ainda não existe). Devolve o objeto (novo ou existente)."""
    ja = objeto(d, nome)
    if ja:
        return ja
    o = copy.deepcopy(objeto(d, origem))
    o['name'] = nome
    o['persistentUuid'] = _uid()
    for v in o.get('variables', []):
        v['persistentUuid'] = _uid()
    o.update(mudancas)
    d['objects'].append(o)
    return o


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


def grupo(nome, eventos):
    return {'type': 'BuiltinCommonInstructions::Group', 'name': nome, 'source': '', 'folded': False,
            'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'parameters': [], 'events': eventos}
