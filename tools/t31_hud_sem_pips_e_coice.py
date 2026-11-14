"""Migração única: tira do HUD as balinhas de munição (hud_pips_*) e o coice do ícone da arma ao atirar.

- Objetos hud_pips_pistola, hud_pips_doze, hud_pips_minigun, hud_pips_lanca: somem do projeto,
  das cenas (objetos, instâncias, pastas) e de todas as ações que os citam.
- Imagens hud/pip_*.png: saem da lista de recursos (os arquivos são apagados com git rm).
- Evento "Arma acabou de atirar -> ícone gira -6 e volta (tween "coice")" no HUD: removido.
O contador de munição (municao / max_municao), o ícone e o nome da arma continuam. Não rode de novo.
"""
import json
import re

PATH = 'jogo.json'
PIPS = {'hud_pips_pistola', 'hud_pips_doze', 'hud_pips_minigun', 'hud_pips_lanca'}
IMAGENS = {'hud/pip_pistola.png', 'hud/pip_doze.png', 'hud/pip_minigun.png', 'hud/pip_lanca.png'}


def carrega():
    s = open(PATH, encoding='utf-8').read()
    return json.loads(s, parse_float=lambda t: '\x00F' + t + '\x00')


def salva(d):
    o = json.dumps(d, indent=2, ensure_ascii=False)
    o = re.sub(r'"\\u0000F(.*?)\\u0000"', r'\1', o)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(o + '\n')


def tira_imagens(d):
    r = d['resources']
    r['resources'] = [x for x in r['resources'] if x['name'] not in IMAGENS]


def limpa_pasta(p):
    if 'children' not in p:
        return
    for c in p['children']:
        limpa_pasta(c)
    # Some o objeto e a pasta que ficou vazia só por causa dele (municao_pips).
    p['children'] = [c for c in p['children'] if c.get('objectName') not in PIPS
                     and not (c.get('folderName') == 'municao_pips' and not c.get('children'))]


def coice_do_icone(e):
    conds = [c['type']['value'] for c in e.get('conditions', [])]
    s = json.dumps(e.get('actions', []), ensure_ascii=False)
    return conds == ['FireBullet::FireBullet::HasJustFired'] and 'hud_arma_icone' in s and '\\"coice\\"' in s


def limpa_eventos(evs, achou):
    novo = []
    for e in evs:
        if coice_do_icone(e):
            achou.append(e)
            continue
        if 'actions' in e:
            e['actions'] = [a for a in e['actions'] if not (a.get('parameters') and a['parameters'][0] in PIPS)]
        if e.get('events'):
            e['events'] = limpa_eventos(e['events'], achou)
        novo.append(e)
    return novo


def main():
    d = carrega()
    d['objects'] = [o for o in d['objects'] if o['name'] not in PIPS]
    if 'objectsFolderStructure' in d:
        limpa_pasta(d['objectsFolderStructure'])
    for lay in d['layouts']:
        lay['objects'] = [o for o in lay.get('objects', []) if o['name'] not in PIPS]
        lay['instances'] = [i for i in lay.get('instances', []) if i['name'] not in PIPS]
        if 'objectsFolderStructure' in lay:
            limpa_pasta(lay['objectsFolderStructure'])

    achou = []
    for x in d['externalEvents'] + d['layouts']:
        x['events'] = limpa_eventos(x['events'], achou)
    assert len(achou) == 1, 'esperava 1 evento de coice do ícone, achei %d' % len(achou)

    tira_imagens(d)
    s = json.dumps(d, ensure_ascii=False)
    for n in PIPS | {'pip_pistola', 'pip_doze', 'pip_minigun', 'pip_lanca'}:
        assert n not in s, n
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
