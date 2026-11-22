"""Tarefa 90: sai o soco (luva no botão direito) e o coice do soco no terreno (pulo da luva), por completo.

- Jogador: o grupo Soco sai inteiro (Início, Teto, Golpe, Luva e rastro, KNOCKBACK, Coice na parede, Guarda a altura).
  No lugar dele fica o grupo "Empurrão no pato", só com os dois eventos que aplicam e freiam pato.coice_vx: os inimigos
  (projétil, condenado azul, inchado, olho, mina, sapo) e os espinhos usam essa variável para empurrar o pato de lado.
  Por isso ficam no pato coice_vx, coice_parede_freio (o freio do empurrão) e coice_decai (o recuo da arma).
- Saem o PreloadSound de som_soco.wav e som_soco_acerto.wav.
- Saem os objetos soco e soco_rastro (e da pasta jogador), os recursos soco_luva.png, soco_rastro_1..4.png, som_soco.wav e
  som_soco_acerto.wav, as variáveis de cena soco_rx/soco_ry, as do pato só do soco (soco_*, coice_y, coice_guarda,
  coice_parede_x/y, rmb_antes, y_antes) e as dos inimigos socado/soco_dir.
- Caveira azul: só o soco a machucava (invulneravel = True); sem soco ela ficaria imortal, então invulneravel = False e a
  bala machuca como nos outros. Comentários que falavam do soco são ajustados.
Rodar uma vez:  python3 tools/t90_remove_soco.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICAM = {'coice_vx', 'coice_parede_freio', 'coice_decai'}
PATO_SAI = {'rmb_antes', 'y_antes', 'coice_y', 'coice_guarda', 'coice_parede_x', 'coice_parede_y'}
RECURSOS = {'soco_luva.png', 'soco_rastro_1.png', 'soco_rastro_2.png', 'soco_rastro_3.png', 'soco_rastro_4.png',
            'som_soco.wav', 'som_soco_acerto.wav'}
COMENTARIOS = [
    ('invulneravel = bala não machuca (só o soco)', 'invulneravel = bala não machuca'),
    (' invulneravel: bala ricocheteia, só o soco machuca.', ''),
    (' O soco sempre machuca.', ''),
    ('(bala, explosão ou soco)', '(bala ou explosão)'),
    (' Estão no grupo Terreno, então socar dá o coice da parede.', ''),
]


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def acha_lista(evs, alvo):
    """Lista de eventos que contém alvo (para trocar no mesmo lugar)."""
    for i, e in enumerate(evs):
        if e is alvo:
            return evs, i
        r = acha_lista(e.get('events') or [], alvo)
        if r:
            return r


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
    soco = next((e for e in todos(jog) if e.get('name') == 'Soco' and e['type'].endswith('Group')), None)
    if soco is None:
        sys.exit('t90 já foi aplicada (não há grupo Soco); não roda de novo.')

    # Empurrão no pato: os dois eventos de coice_vx que não dependem do soco
    coice = next(e for e in soco['events'] if e.get('name') == 'Coice na parede')
    empurra = [e for e in coice['events']
               if any(a['parameters'][:2] == ['pato', 'coice_vx'] for a in e.get('actions') or [])
               and 'coice_guarda' not in json.dumps(e)]
    assert len(empurra) == 2, empurra
    lista, i = acha_lista(jog, soco)
    novo_grupo = dict(soco)
    novo_grupo.update({'name': 'Empurrão no pato', 'events': [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'pato.coice_vx (px/s) empurra o pato de lado por SetX, fora do limite de velocidade, e some a '
                    'pato.coice_parede_freio px/s². Quem põe valor: projéteis e inimigos que empurram, espinhos. '
                    'O dash zera.'}] + empurra})
    lista[i] = novo_grupo

    # Preload dos sons do soco
    for x in d['externalEvents']:
        for e in todos(x['events']):
            if e.get('actions'):
                e['actions'] = [a for a in e['actions'] if not (a['type']['value'] == 'PreloadSound'
                                                                and a['parameters'][1] in RECURSOS)]

    # Objetos, pasta e recursos
    d['objects'] = [o for o in d['objects'] if o['name'] not in ('soco', 'soco_rastro')]

    def poda(no):
        if 'children' in no:
            no['children'] = [c for c in no['children'] if c.get('objectName') not in ('soco', 'soco_rastro')]
            for c in no['children']:
                poda(c)
    poda(d['objectsFolderStructure'])
    d['resources']['resources'] = [r for r in d['resources']['resources'] if r['name'] not in RECURSOS]

    for l in d['layouts']:
        l['variables'] = [v for v in l['variables'] if v['name'] not in ('soco_rx', 'soco_ry')]

    for o in d['objects']:
        vs = o.get('variables') or []
        if o['name'] == 'pato':
            o['variables'] = [v for v in vs if v['name'] in FICAM
                              or not (v['name'].startswith('soco_') or v['name'] in PATO_SAI)]
        else:
            o['variables'] = [v for v in vs if v['name'] not in ('socado', 'soco_dir')]
        if o['name'] == 'caveira_azul':
            for v in o['variables']:
                if v['name'] == 'invulneravel':
                    v['value'] = False

    for x in d['externalEvents']:
        for e in todos(x['events']):
            if e.get('name') == 'Caveira azul (quica e só morre no soco)':
                e['name'] = 'Caveira azul (quica)'
            if e.get('comment'):
                for velho, novo in COMENTARIOS:
                    e['comment'] = e['comment'].replace(velho, novo)

    sobra = json.dumps(d, ensure_ascii=False)
    for nome in list(RECURSOS) + ['"soco"', '"soco_rastro"', 'soco_rx', 'pato.soco_', 'soco_vy', 'coice_guarda']:
        assert nome not in sobra, nome

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('soco e coice do soco removidos')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
