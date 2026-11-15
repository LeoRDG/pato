"""Tarefa 70: o salto com pancada do demônio na lava sempre cai em cima de uma ponte.

Antes o alvo do salto era o pé do pato: com o pato no ar o demônio cravava o cutelo no ar. Migração de uso único que
só ADICIONA um subevento ao evento que começa o salto (o que troca o golpe para "salto", no grupo Fase 2): ele troca o
alvo para a ponte (tiles_inferno_ponte dentro da faixa quebra_x_min..quebra_x_max) mais perto do pato na horizontal:
  - o cutelo desce no ponto dessa ponte mais perto do pato (lava_golpe_dx à frente do corpo dele);
  - o pé dele fica lava_golpe_baixo abaixo do topo da ponte, como antes;
  - ele vira para o lado desse ponto.
Sem pontes na faixa, fica o alvo de antes.
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = 'demonio_chefe'
MARCA = '// o salto sempre cai numa ponte'

JS = [
    MARCA + ': a mais perto do pato na horizontal',
    'const cena = runtimeScene.getVariables();',
    'const n = (k) => cena.get(k).getAsNumber();',
    'const pontes = runtimeScene.getObjects("tiles_inferno_ponte").filter(',
    '  (p) => p.getX() >= n("quebra_x_min") && p.getX() + p.getWidth() <= n("quebra_x_max"));',
    'const pato = runtimeScene.getObjects("pato")[0];',
    'if (pontes.length === 0 || !pato) return;',
    'const px = pato.getCenterXInScene();',
    'const longe = (p) => Math.max(p.getX() - px, px - (p.getX() + p.getWidth()), 0);',
    'const ponte = pontes.reduce((a, p) => (longe(p) < longe(a) ? p : a));',
    'const alvo = Math.min(Math.max(px, ponte.getX()), ponte.getX() + ponte.getWidth());',
    'for (const b of objects) {',
    '  const v = b.getVariables();',
    '  const num = (k) => v.get(k).getAsNumber();',
    '  const dir = Math.sign(alvo - b.getCenterXInScene()) || num("direcao") || 1;',
    '  const x1 = alvo - dir * num("lava_golpe_dx");',
    '  v.get("direcao").setNumber(dir);',
    '  v.get("lava_x1").setNumber(Math.min(Math.max(x1, n("quebra_x_min") + num("lava_borda")), n("quebra_x_max") - num("lava_borda")));',
    '  v.get("lava_y1").setNumber(ponte.getY() - b.getHeight() + num("lava_golpe_baixo"));',
    '}',
]


def evento():
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': JS, 'parameterObjects': D,
            'useStrict': True, 'eventsSheetExpanded': False}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def inicio_do_salto(fase2):
    for e in todos(fase2['events']):
        if any(a['type']['value'] == 'SetStringObjectVariable' and a['parameters'][:4] == [D, 'golpe', '=', '"salto"']
               for a in e.get('actions') or []):
            return e


def migra(d):
    chefe = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')['events']
    fase2 = next(e for e in chefe if e.get('name') == 'Fase 2')
    e = inicio_do_salto(fase2)
    codigo = lambda s: s['inlineCode'] if isinstance(s['inlineCode'], str) else '\n'.join(s['inlineCode'])
    if any(MARCA in codigo(s) for s in e.get('events') or [] if s['type'].endswith('JsCode')):
        return
    e.setdefault('events', []).append(evento())


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
