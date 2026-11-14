"""Tarefa 54: no Inferno o fundo troca, aos poucos, para o inferno escuro conforme o pato sobe (e volta ao descer).

A troca é pela ALTURA do pato, por isso vale nos dois sentidos sem guardar estado: abaixo de fundo_troca_y_baixo o
fundo é o normal, acima de fundo_troca_y_alto é o escuro, e no meio as quatro camadas escuras aparecem por cima das
normais na mesma proporção (opacidade), com a cor de fundo da cena indo junto. fundo_troca_suave amacia a mudança
para não acompanhar cada pulo. (No GDevelop, subir = Y menor: y_alto é um número MENOR que y_baixo.)

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - imagens assets/gandalf_hell/fundo_escuro/<camada>_3x.png (as 4 camadas do inferno escuro ampliadas 3x e
    completadas até 1080 px, como as do fundo normal);
  - objetos bg_inferno_noite_ceu / _fundo / _meio / _frente (cada um com a variável `parallax`), na pasta cenario/bg;
    os bg_inferno_escuro_* do Hub ficam como estão;
  - variáveis da cena Inferno: fundo_troca_y_baixo, fundo_troca_y_alto, fundo_troca_suave, fundo_mistura (de trabalho),
    fundo_cor_r/g/b (cor de fundo normal) e fundo_noite_cor_r/g/b (cor de fundo escura);
  - eventos externos "FundoEscuro", ligados na cena Inferno. As camadas escuras são criadas no começo da cena, por
    cima das normais, copiando posição e tamanho delas: não há instância nova para arrumar no editor.
"""
import json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = 'assets/gandalf_hell/fundo_escuro'
ESCALA, ALTURA = 3, 1080
CAMADAS = {'ceu': 0.03, 'fundo': 0.12, 'meio': 0.25, 'frente': 0.4}     # mesmo parallax das camadas normais
CENA = 'Inferno'


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t54/' + '/'.join(p)))


def imagem(nome):
    """3x sem suavizar, completado até 1080 px: o céu repete a linha de cima, as outras ganham topo transparente."""
    rel = f'{PASTA}/{nome}_{ESCALA}x.png'
    im = Image.open(os.path.join(RAIZ, PASTA, nome + '.png')).convert('RGBA')
    topo = im.getpixel((0, 0))
    if not os.path.exists(os.path.join(RAIZ, rel)):
        im = im.resize((im.width * ESCALA, im.height * ESCALA), Image.NEAREST)
        out = Image.new('RGBA', (im.width, ALTURA), (0, 0, 0, 0))
        falta = ALTURA - im.height
        if nome == 'ceu':
            out.paste(im.crop((0, 0, im.width, 1)).resize((im.width, falta)), (0, 0))
        out.paste(im, (0, falta))
        out.save(os.path.join(RAIZ, rel))
    return rel, topo


def I(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def E(conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def eventos():
    cria, some, desliza = [], [], []
    for k, nome in enumerate(CAMADAS):
        n, e = f'bg_inferno_{nome}', f'bg_inferno_noite_{nome}'
        cria += [I('Create', '', e, f'{n}.X()', f'{n}.Y()', '"Fundo"'),
                 I('ResizableCapability::ResizableBehavior::SetWidth', e, 'Resizable', '=', f'{n}.Width()'),
                 I('ResizableCapability::ResizableBehavior::SetHeight', e, 'Resizable', '=', f'{n}.Height()'),
                 I('ChangePlan', e, '=', f'bg_inferno_frente.ZOrder() + {k + 1}'),
                 I('OpacityCapability::OpacityBehavior::SetValue', e, 'Opacity', '=', '0')]
        some.append(I('OpacityCapability::OpacityBehavior::SetValue', e, 'Opacity', '=', '255 * fundo_mistura'))
        desliza.append(I('TiledSpriteObject::XOffset', e, '=', f'CameraCenterX() * {e}.parallax'))
    canal = lambda c: f'ToString(round(lerp(fundo_cor_{c}, fundo_noite_cor_{c}, fundo_mistura)))'
    alvo = 'clamp((fundo_troca_y_baixo - pato.CenterY()) / max(1, fundo_troca_y_baixo - fundo_troca_y_alto), 0, 1)'
    return [
        {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Troca do fundo pela altura do pato. fundo_mistura vai de 0 (inferno normal, pato abaixo de '
                    'fundo_troca_y_baixo) a 1 (inferno escuro, pato acima de fundo_troca_y_alto) e persegue esse alvo com a '
                    'suavidade de fundo_troca_suave. As camadas escuras (bg_inferno_noite_*) ficam por cima das normais com '
                    'opacidade 255 * fundo_mistura, e a cor de fundo da cena vai de fundo_cor_* a fundo_noite_cor_*. Como '
                    'depende só da altura, vale subindo e descendo.'},
        {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': 'Fundo escuro', 'source': '',
         'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': [
            E([I('SceneJustBegins', '')], cria + [I('SetNumberVariable', 'fundo_mistura', '=', alvo)]),
            E([I('SceneInstancesCount', '', 'pato', '>', '0')],
              [I('SetNumberVariable', 'fundo_mistura', '+',
                 f'({alvo} - fundo_mistura) * min(1, fundo_troca_suave * TimeDelta())')]),
            E([], some + desliza + [I('SceneBackground', '', ' + ";" + '.join(canal(c) for c in 'rgb'))]),
        ]},
    ]


def migra(d, topo_escuro):
    objs = {o['name'] for o in d['objects']}
    recursos = d['resources']['resources']
    tem = {r['name'] for r in recursos}
    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'bg'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox
    for nome, fator in CAMADAS.items():
        rel = f'{PASTA}/{nome}_{ESCALA}x.png'
        if rel not in tem:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})
        obj = f'bg_inferno_noite_{nome}'
        if obj not in objs:
            d['objects'].append({'assetStoreId': '', 'height': ALTURA, 'name': obj, 'persistentUuid': uid(obj), 'texture': rel,
                                 'type': 'TiledSpriteObject::TiledSprite', 'width': 3840,
                                 'variables': [{'name': 'parallax', 'persistentUuid': uid(obj, 'parallax'), 'type': 'number', 'value': fator}],
                                 'effects': [], 'behaviors': []})
            if not any(c.get('objectName') == obj for c in pasta.setdefault('children', [])):
                pasta['children'].append({'objectName': obj})
    cena = next(l for l in d['layouts'] if l['name'] == CENA)
    novas = {'fundo_troca_y_baixo': -400, 'fundo_troca_y_alto': -2000, 'fundo_troca_suave': 3, 'fundo_mistura': 0,
             'fundo_cor_r': cena.get('r', 0), 'fundo_cor_g': cena.get('v', 0), 'fundo_cor_b': cena.get('b', 0),
             'fundo_noite_cor_r': topo_escuro[0], 'fundo_noite_cor_g': topo_escuro[1], 'fundo_noite_cor_b': topo_escuro[2]}
    for k, v in novas.items():
        if not any(x['name'] == k for x in cena['variables']):
            cena['variables'].append({'name': k, 'persistentUuid': uid('cena', k), 'type': 'number', 'value': v})
    if not any(x['name'] == 'FundoEscuro' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': CENA, 'name': 'FundoEscuro', 'events': eventos()})
    if not any(e['type'].endswith('::Link') and e.get('target') == 'FundoEscuro' for e in cena['events']):
        cena['events'].append({'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'FundoEscuro'})


def main(caminho):
    topo = None
    for nome in CAMADAS:
        _, t = imagem(nome)
        if nome == 'ceu':
            topo = t
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d, topo)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
