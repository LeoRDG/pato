"""Tarefa 117: barra de vida dos inimigos do tamanho do inimigo, centrada e mais fina.

A barra nascia em (X - 20, Y - 30) do inimigo e ficava grudada (Sticker) com esse deslocamento, sempre do mesmo
tamanho (224 x 34): enorme nas moscas e fora do centro em quem tem espaço vazio no desenho (mercador, etc.).
Agora, todo quadro, no "para cada barra_de_vida" que já atualiza o valor:
- largura = clamp(largura da caixa de colisão do inimigo * barra_fator, barra_min, barra_max);
- altura = barra_altura (mais fina);
- centrada no meio da caixa de colisão, barra_folga px acima do topo dela.
Variáveis novas no objeto barra_de_vida: barra_fator 0.8, barra_min 36, barra_max 110, barra_altura 10,
barra_folga 8. O Sticker continua (apaga a barra junto com o inimigo). (Não existe BoundingBoxWidth(): a largura é
BoundingBoxRight() - BoundingBoxLeft(); com a expressão inválida a largura virava 0 e a barra sumia.)
Rodar uma vez:  python3 tools/t117_barra_de_vida_no_inimigo.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARS = [('barra_fator', 0.8), ('barra_min', 36), ('barra_max', 110), ('barra_altura', 10), ('barra_folga', 8)]
B, P = 'barra_de_vida', 'Personagem'


def a(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    com = next(x for x in d['externalEvents'] if x['name'] == 'Combate')['events']
    fe = next(e for e in todos(com) if e['type'].endswith('ForEach') and e.get('object') == B)
    if any(x['type']['value'].endswith('SetWidth') for x in fe['actions']):
        sys.exit('t117 já foi aplicada; não roda de novo.')
    assert any(c['type']['value'] == 'LinkedObjects::PickObjectsLinkedTo' for c in fe['conditions']), fe['conditions']
    fe['actions'] += [
        a('ResizableCapability::ResizableBehavior::SetWidth', B, 'Resizable', '=',
          f'clamp(({P}.BoundingBoxRight() - {P}.BoundingBoxLeft()) * {B}.barra_fator, {B}.barra_min, {B}.barra_max)'),
        a('ResizableCapability::ResizableBehavior::SetHeight', B, 'Resizable', '=', f'{B}.barra_altura'),
        a('SetX', B, '=', f'{P}.BoundingBoxCenterX() - {B}.Width() / 2'),
        a('SetY', B, '=', f'{P}.BoundingBoxTop() - {B}.barra_folga - {B}.Height()'),
    ]
    o = next(o for o in d['objects'] if o['name'] == B)
    nomes = {v['name'] for v in o['variables']}
    for n, v in VARS:
        if n not in nomes:
            o['variables'].append({'name': n, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t117/' + n)),
                                   'type': 'number', 'value': v})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('barra de vida no inimigo')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
