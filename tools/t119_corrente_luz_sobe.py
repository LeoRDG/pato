"""Tarefa 119: a textura da corrente de luz do Paraíso corre para cima.

A corrente_luz (TiledSprite) ganhou textura nova (feixe com bordas douradas, fios de luz e setas ^), contínua na
vertical. Para mostrar que ela ergue o pato, a textura sobe a vel_textura px/s (variável nova do objeto, 180):
no evento que já soma t a cada quadro entra  YOffset = corrente_luz.t * corrente_luz.vel_textura.
Só adiciona: se a variável já existe, o valor dela fica; se a ação já está lá, não roda de novo.
Rodar uma vez:  python3 tools/t119_corrente_luz_sobe.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPR = 'corrente_luz.t * corrente_luz.vel_textura'


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    obj = next(o for o in d['objects'] if o['name'] == 'corrente_luz')
    ev = next(x for x in d['externalEvents'] if x['name'] == 'CorrentesDeLuz')['events']
    laco = next(e for e in ev if e.get('type') == 'BuiltinCommonInstructions::ForEach' and e.get('object') == 'corrente_luz')
    if any(a['type']['value'] == 'TiledSpriteObject::YOffset' for a in laco['actions']):
        sys.exit('t119 já foi aplicada; não roda de novo.')

    if not any(v['name'] == 'vel_textura' for v in obj['variables']):
        obj['variables'].append({'name': 'vel_textura', 'persistentUuid': str(uuid.uuid4()), 'type': 'number',
                                 'value': 180})
    laco['actions'].append({'type': {'value': 'TiledSpriteObject::YOffset'},
                            'parameters': ['corrente_luz', '=', EXPR]})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('corrente_luz sobe:', EXPR)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
