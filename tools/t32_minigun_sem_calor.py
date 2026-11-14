"""Migração única: a minigun não tem mais mecânica de calor.

- Barra de calor do HUD (hud_calor_trilho, hud_calor_fill): some do projeto, das cenas
  (objetos, instâncias, pastas) e de todas as ações que a citam.
- Pasta "recarga_e_calor" vira "recarga".
- FireBullet da minigun: OverheatDuration 5 -> 0, igual às outras armas (o calor por tiro já era 0).
- Imagem hud/fill_laranja.png (só a barra de calor usava): sai dos recursos; o arquivo é apagado com git rm.
- Recursos hud/pip_*.png (arquivos já apagados na t31) saem de novo se o editor os tiver devolvido.
O giro da minigun continua. Não rode de novo.
Uso: python3 tools/t32_minigun_sem_calor.py [arquivo]  (padrão jogo.json)
"""
import json
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'jogo.json'
CALOR = {'hud_calor_trilho', 'hud_calor_fill'}
IMAGENS = {'hud/fill_laranja.png', 'hud/pip_pistola.png', 'hud/pip_doze.png', 'hud/pip_minigun.png', 'hud/pip_lanca.png'}


def carrega():
    s = open(PATH, encoding='utf-8').read()
    return json.loads(s, parse_float=lambda t: '\x00F' + t + '\x00')


def salva(d):
    o = json.dumps(d, indent=2, ensure_ascii=False)
    o = re.sub(r'"\\u0000F(.*?)\\u0000"', r'\1', o)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(o + '\n')


def limpa_pasta(p):
    if 'children' not in p:
        return
    for c in p['children']:
        limpa_pasta(c)
        if c.get('folderName') == 'recarga_e_calor':
            c['folderName'] = 'recarga'
    p['children'] = [c for c in p['children'] if c.get('objectName') not in CALOR]


COMENTARIO_VELHO = ('Ícone, nome, munição e marcadores da arma equipada; calor da minigun; '
                    'recarga com anel na mira; aviso de pente vazio; coice do ícone.')
COMENTARIO_NOVO = 'Ícone, nome e munição da arma equipada; recarga com anel na mira; aviso de pente vazio.'


def limpa_eventos(evs):
    for e in evs:
        if e.get('comment') == COMENTARIO_VELHO:
            e['comment'] = COMENTARIO_NOVO
        if 'actions' in e:
            e['actions'] = [a for a in e['actions'] if not (a.get('parameters') and a['parameters'][0] in CALOR)]
        limpa_eventos(e.get('events') or [])


def main():
    d = carrega()
    d['objects'] = [o for o in d['objects'] if o['name'] not in CALOR]
    limpa_pasta(d['objectsFolderStructure'])
    for lay in d['layouts']:
        lay['objects'] = [o for o in lay.get('objects', []) if o['name'] not in CALOR]
        lay['instances'] = [i for i in lay.get('instances', []) if i['name'] not in CALOR]
        if 'objectsFolderStructure' in lay:
            limpa_pasta(lay['objectsFolderStructure'])
    for x in d['externalEvents'] + d['layouts']:
        limpa_eventos(x['events'])

    mg = next(o for o in d['objects'] if o['name'] == 'minigun')
    fb = next(b for b in mg['behaviors'] if b['type'] == 'FireBullet::FireBullet')
    assert fb['HeatIncreasePerShot'] == 0, 'a minigun esquenta por tiro; conferir antes'
    fb['OverheatDuration'] = 0

    d['resources']['resources'] = [r for r in d['resources']['resources'] if r['name'] not in IMAGENS]

    s = json.dumps([d['objects'], d['layouts'], d['externalEvents'], d['resources']], ensure_ascii=False)
    for n in ('calor', 'fill_laranja', 'pip_'):
        assert n not in s, n
    assert 'Heat' not in json.dumps([d['externalEvents'], [l['events'] for l in d['layouts']]]), 'evento ainda usa calor'
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
