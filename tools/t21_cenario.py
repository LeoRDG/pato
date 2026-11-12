"""Tarefa 21: fundo do inferno em parallax, mira sem limite de ângulo, pato sem brilho.

  - Fundo: as 4 camadas do GandalfHardcore Hell (céu, fundo, meio, frente) ampliadas 3x (pixel art, vizinho mais próximo) e
    completadas até 1080 px de altura (o céu repete a linha de cima; as outras ganham topo transparente).
    Na cena Inferno ficam numa camada nova "Fundo", atrás de tudo, com câmera parada; a cada quadro o deslocamento da textura
    de cada uma acompanha a câmera da camada base com um fator (céu quase parado, frente mais rápida): é o parallax.
    O sprite antigo `bg` sai da cena Inferno.
  - Mira: sem o clamp de ±55 graus (a arma gira até a vertical).
  - Pato: sem o efeito AdvancedBloom ("brilho").
Rodar:  python3 tools/t21_cenario.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import copy, json, os, uuid
from PIL import Image
from t12_armas import A, E, comentario, grupo, PATH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENA, CAMADA = 'Inferno', 'Fundo'
ESCALA, ALTURA = 3, 1080
FATOR = {'ceu': 0.03, 'fundo': 0.12, 'meio': 0.25, 'frente': 0.4}   # fração do movimento da câmera
LARGURA = 3840          # cobre telas mais largas que 1920 (a resolução se adapta à largura)


def imagem(nome):
    rel = f'assets/gandalf_hell/fundo/{nome}_{ESCALA}x.png'
    im = Image.open(os.path.join(ROOT, 'assets/gandalf_hell/fundo', nome + '.png')).convert('RGBA')
    im = im.resize((im.width * ESCALA, im.height * ESCALA), Image.NEAREST)
    out = Image.new('RGBA', (im.width, ALTURA), (0, 0, 0, 0))
    falta = ALTURA - im.height
    if nome == 'ceu':
        out.paste(im.crop((0, 0, im.width, 1)).resize((im.width, falta)), (0, 0))
    out.paste(im, (0, falta))
    out.save(os.path.join(ROOT, rel))
    return rel, im.getpixel((0, 0))


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    objs = {o['name']: o for o in d['objects']}
    rec = d['resources']['resources']
    cena = next(l for l in d['layouts'] if l['name'] == CENA)

    # fundo
    for n in FATOR:
        rel, cor = imagem(n)
        if not any(r['name'] == rel for r in rec):
            rec.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})
        o = objs[f'bg_inferno_{n}']
        o['texture'], o['width'], o['height'] = rel, LARGURA, ALTURA
        if n == 'ceu':
            cena['r'], cena['v'], cena['b'] = cor[:3]
    if not any(L['name'] == CAMADA for L in cena['layers']):
        L = copy.deepcopy(next(L for L in cena['layers'] if L['name'] == ''))
        L['name'], L['effects'], L['followBaseLayerCamera'] = CAMADA, [], False
        cena['layers'].insert(0, L)
    cena['instances'] = [i for i in cena['instances'] if i['name'] != 'bg' and i['layer'] != CAMADA]
    for z, n in enumerate(FATOR):
        cena['instances'].append({'angle': 0, 'customSize': True, 'height': ALTURA, 'keepRatio': True, 'layer': CAMADA,
                                  'name': f'bg_inferno_{n}', 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'fundo-' + n)),
                                  'width': LARGURA, 'x': (1920 - LARGURA) / 2, 'y': 0, 'zOrder': z + 1,
                                  'numberProperties': [], 'stringProperties': [], 'initialVariables': []})
    cena['events'] = [e for e in cena['events'] if e.get('name') != 'Fundo em parallax']
    cena['events'].append(grupo('Fundo em parallax', [
        comentario('Cada camada do fundo desloca a textura com uma fração do movimento da câmera: as de trás andam menos.'),
        E([], [A('TiledSpriteObject::XOffset', f'bg_inferno_{n}', '=', f'CameraCenterX() * {f}') for n, f in FATOR.items()]),
    ]))

    # mira sem limite de ângulo
    def anda(evs):
        for e in evs:
            yield e
            yield from anda(e.get('events') or [])
    for x in d['externalEvents']:
        for e in anda(x['events']):
            for a in e.get('actions') or []:
                if a['type']['value'] == 'SetNumberVariable' and a['parameters'][0] == 'mira_a' and a['parameters'][2].startswith('clamp('):
                    a['parameters'][2] = 'atan2(MouseY() - Arma.CenterY(), abs(MouseX() - Arma.CenterX())) - ToRad(recuo)'

    # pato sem brilho
    objs['pato']['effects'] = [e for e in objs['pato']['effects'] if e.get('effectType') != 'AdvancedBloom']

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
