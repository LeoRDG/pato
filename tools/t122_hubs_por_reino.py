"""Tarefa 122: um Hub por reino. Além do Hub (Inferno), entram HubPurgatorio e HubParaiso, e cada fase manda para o
hub do seu reino.

Variável de cena nova hub (texto) em toda cena que liga Jogador/Portais: para qual hub o pato vai dali.
  Hub, Inferno e Teste -> "Hub"; Purgatorio e HubPurgatorio -> "HubPurgatorio"; Paraiso e HubParaiso -> "HubParaiso".
"Hub" nos eventos e nas instâncias passa a querer dizer "o hub deste reino":
- Jogador: ao morrer, Scene(hub) (era Scene("Hub")).
- Portais: no começo da cena, portal com cena = "Hub" (o padrão do objeto) passa a cena = hub; o ponto de volta
  (waypoint) é guardado quando o portal leva a hub e a cena não é o próprio hub (era "Hub" escrito).
- Paraiso, grupo Saída no Empíreo: no começo, proxima_cena = "Hub" vira hub. Os valores do editor não mudam.
Cenas novas HubPurgatorio e HubParaiso: cópia do Hub (mesmo mapa, mercador, loja e os três portais), com o tilemap
do reino (tiles_purgatorio / tiles_ceu: os atlas têm o mesmo terreno no mesmo lugar e os mesmos tiles sólidos), a
cor de fundo da fase e o fundo dela na camada fundo, que anda com a câmera a fundo_parallax_x/y (variáveis novas da
cena, como nas fases): Purgatório com bg_purgatorio_longe/pilares/nevoa, Paraíso com bg_paraiso_nuvens e o sol
bg_paraiso_rosa. O fundo do Inferno (bg_inferno_escuro_*) e o evento dele não vão para as cópias.
Só adiciona o que não existe; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t122_hubs_por_reino.py
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB_DE = {'Hub': 'Hub', 'Inferno': 'Hub', 'Teste': 'Hub', 'Purgatorio': 'HubPurgatorio', 'Paraiso': 'HubParaiso'}
NOVOS = {
    'HubPurgatorio': dict(
        cor=(128, 138, 128), tiles='tiles_purgatorio', parallax=0.15,
        fundo=[('bg_purgatorio_longe', -2048, -1500, 4096, 3000, -3),
               ('bg_purgatorio_pilares', -2048, -1500, 4096, 3000, -2),
               ('bg_purgatorio_nevoa', -2048, -1500, 4096, 3000, -1)],
        comentario='Hub do Purgatório: cópia do Hub (mercador, loja e portais) com os tiles e o fundo do Purgatório. '
                   'O pato vem para cá ao morrer ou sair pelo portal no Purgatório (variável de cena hub).'),
    'HubParaiso': dict(
        cor=(172, 196, 232), tiles='tiles_ceu', parallax=0.12,
        fundo=[('bg_paraiso_nuvens', -2400, -2400, 7200, 4800, -2),
               ('bg_paraiso_rosa', -700, -600, None, None, -1)],
        comentario='Hub do Paraíso: cópia do Hub (mercador, loja e portais) com os tiles e o fundo do Paraíso. '
                   'O pato vem para cá ao morrer ou sair pelo portal no Paraíso (variável de cena hub).'),
}
FUNDO_INFERNO = ('bg_inferno_escuro_meio', 'bg_inferno_escuro_fundo', 'bg_inferno_escuro_frente',
                 'bg_inferno_escuro_ceu')


_N = [0]


def uid():                                       # determinístico: rodar no mesmo arquivo dá os mesmos ids
    _N[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogo/t122/{_N[0]}'))


def inst(o, a, *p):
    return {'type': {'value': a}, 'parameters': list(p)}


def var(nome, tipo, valor):
    return {'name': nome, 'persistentUuid': uid(), 'type': tipo, 'value': valor}


def comentario(texto):
    return {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0,
            'textG': 0, 'textR': 0}, 'comment': texto, 'comment2': ''}


def evento(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acoes}
    if filhos:
        e['events'] = filhos
    return e


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def poe_var(cena, nome, tipo, valor):
    if not any(v['name'] == nome for v in cena['variables']):
        cena['variables'].append(var(nome, tipo, valor))


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cenas = {l['name']: l for l in d['layouts']}
    if 'HubPurgatorio' in cenas or 'HubParaiso' in cenas:
        sys.exit('t122 já foi aplicada; não roda de novo.')
    ext = {x['name']: x for x in d['externalEvents']}

    # --- 1. variável hub nas cenas que já existem
    for nome, hub in HUB_DE.items():
        if nome in cenas:
            poe_var(cenas[nome], 'hub', 'string', hub)

    # --- 2. morrer leva ao hub da cena
    trocas = 0
    for e in todos(ext['Jogador']['events']):
        for a in e.get('actions', []):
            if a['type']['value'] == 'Scene' and a['parameters'][1] == '"Hub"':
                a['parameters'][1] = 'hub'
                trocas += 1
    assert trocas == 1, trocas

    # --- 3. portais: "Hub" quer dizer o hub da cena; ponto de volta compara com hub
    port = ext['Portais']['events']
    wp = 0
    for e in todos(port):
        cs = e.get('conditions', [])
        tipos = [c['type']['value'] for c in cs]
        if 'StringObjectVariable' in tipos and any(c['parameters'][-1] == '"Hub"' for c in cs):
            for c in cs:
                if c['type']['value'] == 'StringObjectVariable' and c['parameters'][1] == 'cena':
                    c['parameters'][3] = 'hub'
                if c['type']['value'] == 'BuiltinCommonInstructions::CompareStrings' and \
                        c['parameters'][0] == 'CurrentSceneName()':
                    c['parameters'][2] = 'hub'
            wp += 1
    assert wp == 1, wp
    i_coment = next(i for i, e in enumerate(port) if e.get('type') == 'BuiltinCommonInstructions::Comment')
    port[i_coment + 1:i_coment + 1] = [
        comentario('Cada reino tem o seu hub (variável de cena hub). Portal com cena = "Hub" (o padrão) leva ao hub '
                   'desta cena.'),
        evento([inst(0, 'DepartScene', ''),
                inst(0, 'StringObjectVariable', 'portal', 'cena', '=', '"Hub"')],
               [inst(0, 'SetStringObjectVariable', 'portal', 'cena', '=', 'hub')]),
    ]

    # --- 4. saída do Paraíso: proxima_cena "Hub" vira o hub
    g = next(e for e in cenas['Paraiso']['events'] if e.get('name') == 'Saída no Empíreo')
    g.setdefault('events', []).insert(0, evento(
        [inst(0, 'DepartScene', ''), inst(0, 'StringVariable', 'proxima_cena', '=', '"Hub"')],
        [inst(0, 'SetStringVariable', 'proxima_cena', '=', 'hub')]))

    # --- 5. as duas cenas novas, copiadas do Hub
    hub = cenas['Hub']
    pos = d['layouts'].index(hub) + 1
    for nome, cfg in NOVOS.items():
        c = copy.deepcopy(hub)
        c['name'] = c['mangledName'] = nome
        c['title'] = ''
        c['r'], c['v'], c['b'] = cfg['cor']
        c['objects'] = [o for o in c['objects'] if o['name'] != 'NewSprite']
        c['objectsFolderStructure'] = {'folderName': '__ROOT', 'children': [{'objectName': o['name']}
                                                                           for o in c['objects']]}
        c['instances'] = [i for i in c['instances'] if i['name'] not in FUNDO_INFERNO]
        for i in c['instances']:
            i['persistentUuid'] = uid()
            if i['name'] == 'tiles_inferno_escuro_':
                i['name'] = cfg['tiles']
        for (n, x, y, w, h, z) in cfg['fundo']:
            i = {'angle': 0, 'customSize': w is not None, 'height': h or 0, 'keepRatio': True, 'layer': 'fundo',
                 'name': n, 'persistentUuid': uid(), 'width': w or 0, 'x': x, 'y': y, 'zOrder': z,
                 'numberProperties': [], 'stringProperties': [], 'initialVariables': []}
            c['instances'].append(i)
        for v in c['variables']:
            v['persistentUuid'] = uid()
            if v['name'] == 'hub':
                v['value'] = nome
        poe_var(c, 'fundo_parallax_x', 'number', cfg['parallax'])
        poe_var(c, 'fundo_parallax_y', 'number', cfg['parallax'])
        poe_var(c, 'fundo_dx', 'number', 0)
        poe_var(c, 'fundo_dy', 'number', 0)
        # eventos: tira o do fundo do Inferno, troca o comentário, põe o grupo do fundo em parallax
        evs = [e for e in c['events'] if 'bg_inferno_escuro' not in json.dumps(e)]
        if evs and evs[0].get('type') == 'BuiltinCommonInstructions::Comment':
            evs[0]['comment'] = cfg['comentario']
        acoes = [inst(0, 'SetCameraCenterX', '', '=', 'CameraCenterX("", 0) * fundo_parallax_x + fundo_dx',
                      '"fundo"', '0'),
                 inst(0, 'SetCameraCenterY', '', '=', 'CameraCenterY("", 0) * fundo_parallax_y + fundo_dy',
                      '"fundo"', '0')]
        if nome == 'HubPurgatorio':
            for n in ('bg_purgatorio_longe', 'bg_purgatorio_pilares'):
                acoes.append(inst(0, 'TiledSpriteObject::XOffset', n, '=', f'CameraCenterX("", 0) * {n}.parallax_extra'))
                acoes.append(inst(0, 'TiledSpriteObject::YOffset', n, '=', f'CameraCenterY("", 0) * {n}.parallax_extra'))
            acoes.append(inst(0, 'TiledSpriteObject::XOffset', 'bg_purgatorio_nevoa', '=',
                              'TimeFromStart() * bg_purgatorio_nevoa.vel'))
        i_portais = next(i for i, e in enumerate(evs) if e.get('target') == 'Portais')
        evs.insert(i_portais, {'type': 'BuiltinCommonInstructions::Group', 'colorB': 228, 'colorG': 176,
                               'colorR': 74, 'creationTime': 0, 'name': 'Fundo em parallax', 'source': '',
                               'parameters': [], 'events': [evento([], acoes)]})
        c['events'] = evs
        d['layouts'].insert(pos, c)
        pos += 1

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('hubs:', ['Hub'] + list(NOVOS))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
