"""Tarefa 18: tiles do cenário do inferno (GandalfHardcore Hell Asset Pack 32x32) prontos para pintar no GDevelop.

As imagens já estavam no projeto, mas os tile maps não tinham colisão, nem comportamento de plataforma, e eram de 32 px
(o pato tem 180 px). Este script:
  - gera o atlas ampliado ESCALA x (vizinho mais próximo), para todo tile map novo já nascer no tamanho certo;
  - tiles_inferno / tiles_inferno_escuro: terreno sólido (hit box nos blocos + comportamento Platform);
  - tiles_inferno_ponte / ..._escuro_ponte: as plataformas finas, atravessáveis por baixo (Jumpthru);
  - tiles_inferno_decor / ..._escuro_decor: mesma imagem, sem colisão (parede de fundo, colunas, lápides, pedras, espinhos);
  - grupo Terreno (chao + tiles sólidos): tiros, laser, granada, moedas e mergulhadores tratam os tiles como chão.
Rodar:  python3 tools/t18_tiles.py        (pode rodar de novo)
Salve e feche o projeto no GDevelop antes, senão ele sobrescreve o jogo.json.
"""
import copy, json, os, uuid
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'jogo.json')
PASTA = 'assets/gandalf_hell/tiles'
ESCALA = 2              # 32 px -> 64 px (os inimigos do pacote estão em ~2x)
TILE, COLS, LINS = 32, 17, 9
PALETAS = {'tiles_inferno': 'tiles_inferno', 'tiles_inferno_escuro': 'tiles_inferno_escuro'}   # objeto base -> imagem
PONTE = [108, 109, 110, 125, 126, 127, 142]     # plataformas finas (o desenho começa no topo do tile)
PREENCHIMENTO = [144]                            # tile preto liso (miolo do terreno)
GRUPO = 'Terreno'


def solidos():
    """Blocos de terreno: colunas 0-12, linhas 0-5 (os tiles vazios do meio ficam de fora) + o preenchimento preto."""
    alfa = Image.open(os.path.join(ROOT, PASTA, 'tiles_inferno.png')).convert('RGBA').split()[3]
    ids = [l * COLS + c for l in range(6) for c in range(13)
           if alfa.crop((c * TILE, l * TILE, (c + 1) * TILE, (l + 1) * TILE)).getbbox()]
    return sorted(ids + PREENCHIMENTO)


def plataforma(tipo):
    return {'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False, 'platformType': tipo, 'yGrabOffset': 0}


def troca_chao(evs):
    """Troca o objeto chao pelo grupo Terreno nas instruções dos eventos."""
    n = 0
    def instr(lst):
        nonlocal n
        for i in lst or []:
            if 'chao' in i.get('parameters', []):
                i['parameters'] = [GRUPO if x == 'chao' else x for x in i['parameters']]
                n += 1
            instr(i.get('subInstructions'))
    for e in evs:
        for k in ('conditions', 'actions', 'whileConditions'):
            instr(e.get(k))
        n += troca_chao(e.get('events') or [])
    return n


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    nomes_rec = {r['name'] for r in recursos}
    lado = TILE * ESCALA
    solido = ','.join(map(str, solidos()))

    pasta = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'cenario')
    pasta = next(c for c in pasta['children'] if c.get('folderName') == 'plataformas')

    for base, img in PALETAS.items():
        # atlas ampliado
        rel = f'{PASTA}/{img}_{ESCALA}x.png'
        orig = Image.open(os.path.join(ROOT, PASTA, img + '.png')).convert('RGBA')
        orig.resize((orig.width * ESCALA, orig.height * ESCALA), Image.NEAREST).save(os.path.join(ROOT, rel))
        if rel not in nomes_rec:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})
            nomes_rec.add(rel)

        for sufixo, hit, comp in (('', solido, [plataforma('NormalPlatform')]),
                                  ('_ponte', ','.join(map(str, PONTE)), [plataforma('Jumpthru')]),
                                  ('_decor', '', [])):
            nome = base + sufixo
            o = objs.get(nome)
            if o is None:
                o = copy.deepcopy(objs[base])
                o['name'], o['persistentUuid'] = nome, str(uuid.uuid4())
                d['objects'].insert(d['objects'].index(objs[base + ('' if sufixo == '_ponte' else '_ponte')]) + 1, o)
                objs[nome] = o
            o['content'].update(atlasImage=rel, rowCount=LINS, columnCount=COLS, tileSize=lado, tilesWithHitBox=hit)
            o['behaviors'] = [b for b in o['behaviors'] if b['type'] != 'PlatformBehavior::PlatformBehavior'] + comp
            if not any(c.get('objectName') == nome for c in pasta['children']):
                pasta['children'].append({'objectName': nome})

    # grupo Terreno: tudo o que é chão sólido
    g = next((x for x in d['objectsGroups'] if x['name'] == GRUPO), None)
    if g is None:
        g = {'name': GRUPO, 'objects': []}
        d['objectsGroups'].append(g)
    g['objects'] = [{'name': n} for n in ['chao'] + list(PALETAS)]

    n = sum(troca_chao(x['events']) for x in d['layouts'] + d['externalEvents'])
    print(f'tiles sólidos: {len(solido.split(","))}; instruções trocadas para {GRUPO}: {n}')

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
