"""Migração única: relógio da cena no canto superior direito do HUD, em mm:ss.

- Objeto de texto hud_tempo (mesma fonte/estilo de hud_vida_txt), na pasta hud, com as
  variáveis margem_x e margem_y (distância do canto superior direito, em px).
- Instância de hud_tempo na camada HUD de toda cena que já tem hud_vida_txt (Hub e Inferno).
- Grupo "Tempo" no fim do grupo HUD: zera o cronômetro "tempo_cena" quando a cena começa e,
  todo quadro, escreve mm:ss e prende o texto no canto superior direito.
Só adiciona: se hud_tempo já existir, não mexe em nada. Não rode de novo.
Uso: python3 tools/t33_hud_tempo.py [arquivo]  (padrão jogo.json)
"""
import copy
import json
import re
import sys
import uuid

PATH = sys.argv[1] if len(sys.argv) > 1 else 'jogo.json'
T = 'TimerElapsedTime("tempo_cena")'
TEXTO = ('SubStr(ToString(100 + floor(%s / 60)), 1, 2) + ":" + '
         'SubStr(ToString(100 + mod(floor(%s), 60)), 1, 2)') % (T, T)


def carrega():
    s = open(PATH, encoding='utf-8').read()
    return json.loads(s, parse_float=lambda t: '\x00F' + t + '\x00')


def salva(d):
    o = json.dumps(d, indent=2, ensure_ascii=False)
    o = re.sub(r'"\\u0000F(.*?)\\u0000"', r'\1', o)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(o + '\n')


_N = [0]


def uid():
    # Fixo (não aleatório): rodar no jogo.json ou numa cópia dá os mesmos ids.
    _N[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogo/t33_hud_tempo/%d' % _N[0]))


def acao(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def acha_pasta(p, nome):
    for c in p.get('children', []):
        if c.get('folderName') == nome:
            return c
        r = acha_pasta(c, nome)
        if r:
            return r


def main():
    d = carrega()
    if any(o['name'] == 'hud_tempo' for o in d['objects']):
        raise SystemExit('hud_tempo já existe; nada a fazer')

    # Objeto: cópia do estilo do número da vida.
    base = next(o for o in d['objects'] if o['name'] == 'hud_vida_txt')
    obj = copy.deepcopy(base)
    obj['name'] = 'hud_tempo'
    obj['persistentUuid'] = uid()
    obj['string'] = '00:00'
    obj['content']['text'] = '00:00'
    obj['variables'] = [
        {'name': 'margem_x', 'persistentUuid': uid(), 'type': 'number', 'value': 48},
        {'name': 'margem_y', 'persistentUuid': uid(), 'type': 'number', 'value': 18},
    ]
    d['objects'].insert(d['objects'].index(base) + 1, obj)

    # Pasta: junto das outras coisas do HUD (hud/).
    hud = acha_pasta(d['objectsFolderStructure'], 'hud')
    assert hud, 'pasta hud não encontrada'
    hud['children'].append({'objectName': 'hud_tempo'})

    # Instâncias: nas cenas que têm HUD.
    cenas = []
    for lay in d['layouts']:
        ref = next((i for i in lay['instances'] if i['name'] == 'hud_vida_txt'), None)
        if not ref:
            continue
        inst = copy.deepcopy(ref)
        inst.update(name='hud_tempo', persistentUuid=uid(), x=1920 - 48 - 90, y=18)
        lay['instances'].append(inst)
        cenas.append(lay['name'])
    assert cenas, 'nenhuma cena com HUD'

    # Eventos: grupo "Tempo" no fim do grupo HUD.
    ext = next(x for x in d['externalEvents'] if x['name'] == 'HUD')
    g = next(e for e in ext['events'] if e.get('name') == 'HUD')
    g['events'].append({
        'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0,
        'name': 'Tempo', 'source': '', 'type': 'BuiltinCommonInstructions::Group',
        'events': [
            {'type': 'BuiltinCommonInstructions::Standard',
             'conditions': [acao('SceneJustBegins', '')],
             'actions': [acao('ResetTimer', '', '"tempo_cena"')]},
            {'type': 'BuiltinCommonInstructions::Standard',
             'conditions': [],
             'actions': [
                 acao('TextContainerCapability::TextContainerBehavior::SetValue', 'hud_tempo', 'Text', '=', TEXTO),
                 acao('SetXY', 'hud_tempo',
                      '=', 'CameraCenterX("HUD") + CameraWidth("HUD") / 2 - hud_tempo.margem_x - hud_tempo.Width()',
                      '=', 'CameraCenterY("HUD") - CameraHeight("HUD") / 2 + hud_tempo.margem_y'),
             ]},
        ],
        'parameters': [],
    })
    salva(d)
    print('ok:', cenas)


if __name__ == '__main__':
    main()
