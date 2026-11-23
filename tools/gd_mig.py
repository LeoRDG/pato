"""Peças comuns das migrações do chefe final (t137 em diante). Só ajudam a ADICIONAR ao jogo.json."""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COR_GRUPO = (74, 176, 228)


class Ids:
    """ids determinísticos por chave: rodar no mesmo arquivo dá os mesmos ids."""
    def __init__(self, tag):
        self.tag = tag

    def __call__(self, chave):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogo/{self.tag}/{chave}'))


# ---------------- eventos ----------------
def X(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def NAO(t, *p):
    c = X(t, *p)
    c['type']['inverted'] = True
    return c


def ev(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': list(conds), 'actions': list(acoes)}
    if filhos:
        e['events'] = list(filhos)
    return e


def cada(obj, conds, acoes, filhos=None):
    e = ev(conds, acoes, filhos)
    e['type'] = 'BuiltinCommonInstructions::ForEach'
    e['object'] = obj
    return e


def repete(expr, acoes, filhos=None):
    e = ev([], acoes, filhos)
    e['type'] = 'BuiltinCommonInstructions::Repeat'
    e['repeatExpression'] = expr
    return e


def grupo(nome, evs):
    r, g, b = COR_GRUPO
    return {'type': 'BuiltinCommonInstructions::Group', 'colorB': b, 'colorG': g, 'colorR': r,
            'creationTime': 0, 'name': nome, 'source': '', 'parameters': [], 'events': list(evs)}


def acha(evs, nome):
    for e in evs:
        if e.get('name') == nome:
            return e
        r = acha(e.get('events') or [], nome)
        if r:
            return r
    return None


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


# atalhos de instruções (objeto o)
def bol(o, v, val):        return X('BooleanObjectVariable', o, v, 'True' if val else 'False', '')
def num(o, v, op, val):    return X('NumberObjectVariable', o, v, op, val)
def txt(o, v, val, op='='): return X('StringObjectVariable', o, v, op, f'"{val}"')
def cmp(a, op, b):         return X('BuiltinCommonInstructions::CompareNumbers', a, op, b)
def timer(o, n, op, v):    return X('CompareObjectTimer', o, f'"{n}"', op, v)
def setn(o, v, op, val):   return X('SetNumberObjectVariable', o, v, op, val)
def sets(o, v, val):       return X('SetStringObjectVariable', o, v, '=', f'"{val}"')
def setb(o, v, val):       return X('SetBooleanObjectVariable', o, v, 'True' if val else 'False', '')
def zera(o, n):            return X('ResetObjectTimer', o, f'"{n}"')
def anim(o, n):            return X('AnimatableCapability::AnimatableBehavior::SetName', o, 'Animation', '=', f'"{n}"')
def som(s, vol, tom='1'):  return X('PlaySound', '', s, '', vol, tom)
def cbol(v, val):          return X('BooleanVariable', v, 'True' if val else 'False', '')
def csetb(v, val):         return X('SetBooleanVariable', v, 'True' if val else 'False', '')
def csetn(v, op, val):     return X('SetNumberVariable', v, op, val)
def cnum(v, op, val):      return X('NumberVariable', v, op, val)


# ---------------- variáveis ----------------
def var(ids, dono, nome, valor):
    tipo = 'boolean' if isinstance(valor, bool) else 'string' if isinstance(valor, str) else 'number'
    return {'name': nome, 'persistentUuid': ids(f'var/{dono}/{nome}'), 'type': tipo, 'value': valor}


def poe_vars(ids, lista, dono, pares):
    """adiciona as que faltam; as que já existem ficam com o valor atual."""
    tem = {v['name'] for v in lista}
    for nome, valor in pares:
        if nome not in tem:
            lista.append(var(ids, dono, nome, valor))


# ---------------- objetos e recursos ----------------
def recurso(caminho):
    return {'file': caminho, 'kind': 'image', 'metadata': '', 'name': caminho, 'smoothed': False, 'userAdded': True}


def poe_recursos(d, caminhos):
    tem = {r['name'] for r in d['resources']['resources']}
    for c in caminhos:
        if c not in tem:
            d['resources']['resources'].append(recurso(c))
            tem.add(c)


def quadros(pasta, anim_, n):
    return [f'{pasta}/{anim_}_{i:02d}.png' for i in range(n)]


def sprite(ids, nome, anims, variaveis=(), mascara=None, efeitos=()):
    """anims: [(nome, pasta ou lista de imagens, n_quadros, tempo, repete)]; mascara: [(x,y),...] em pixels."""
    def quadro(img):
        q = {'hasCustomCollisionMask': mascara is not None, 'image': img, 'points': [],
             'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
             'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': []}
        if mascara:
            q['customCollisionMask'] = [[{'x': x, 'y': y} for x, y in mascara]]
        return q
    return {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': nome, 'persistentUuid': ids('obj/' + nome),
            'type': 'Sprite', 'updateIfNotVisible': False, 'variables': list(variaveis), 'effects': list(efeitos),
            'behaviors': [], 'animations': [
                {'name': a, 'useMultipleDirections': False, 'directions': [{
                    'looping': loop, 'timeBetweenFrames': tempo,
                    'sprites': [quadro(i) for i in (pasta if isinstance(pasta, list) else quadros(pasta, a, n))]}]}
                for a, pasta, n, tempo, loop in anims]}


def tiled(ids, nome, textura, w, h, variaveis=()):
    return {'assetStoreId': '', 'height': h, 'name': nome, 'persistentUuid': ids('obj/' + nome), 'texture': textura,
            'type': 'TiledSpriteObject::TiledSprite', 'width': w, 'variables': list(variaveis), 'effects': [], 'behaviors': []}


def efeito(tipo, nome, doubles=None, strings=None, bools=None):
    return {'effectType': tipo, 'name': nome, 'doubleParameters': dict(doubles or {}),
            'stringParameters': dict(strings or {}), 'booleanParameters': dict(bools or {})}


def objeto(d, nome):
    return next((o for o in d['objects'] if o['name'] == nome), None)


def poe_objeto(d, obj, pasta):
    """adiciona o objeto global (se não existir) e põe na pasta do editor (caminho 'inimigos/ceu')."""
    if objeto(d, obj['name']):
        return objeto(d, obj['name'])
    d['objects'].append(obj)
    f = d['objectsFolderStructure']
    for parte in pasta.split('/'):
        g = next((c for c in f['children'] if c.get('folderName') == parte), None)
        if g is None:
            g = {'folderName': parte, 'children': []}
            f['children'].append(g)
        f = g
    f['children'].append({'objectName': obj['name']})
    return obj


def poe_no_grupo(d, grupo_, nome):
    g = next(g for g in d['objectsGroups'] if g['name'] == grupo_)
    if nome not in [o['name'] for o in g['objects']]:
        g['objects'].append({'name': nome})


def inst(ids, nome, chave, x, y, z, camada='', w=None, h=None, variaveis=()):
    return {'angle': 0, 'customSize': w is not None, 'height': h or 0, 'keepRatio': True, 'layer': camada, 'name': nome,
            'persistentUuid': ids('inst/' + chave), 'width': w or 0, 'x': x, 'y': y, 'zOrder': z, 'numberProperties': [],
            'stringProperties': [], 'initialVariables': list(variaveis)}


def cena(d, nome):
    return next(l for l in d['layouts'] if l['name'] == nome)


def folha(d, nome):
    return next(x for x in d['externalEvents'] if x['name'] == nome)


def vars_cena(d, nome):
    return {v['name']: v.get('value') for v in cena(d, nome)['variables']}


# ---------------- arquivo ----------------
def roda(migra, ja_aplicada, nome):
    caminho = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json')
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if ja_aplicada(d):
        sys.exit(f'{nome} já foi aplicada; não roda de novo.')
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print(f'{nome} aplicada em {caminho}')
