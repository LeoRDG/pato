"""Tarefa 67: na luta contra o demônio chefe a câmera fica mais baixa, mostrando o chefe.

Migração de uso único que só ADICIONA o que falta:
  - fora da luta a câmera do pato olha camera_offset_normal px acima dele (o deslocamento Y da SmoothCamera, guardado
    no começo da cena, -140 hoje);
  - enquanto a arena está trancada (chefe_trancado) e o demônio vive, o deslocamento vira
    (centro do chefe - centro do pato) * camera_mistura + camera_dy: a câmera mira entre os dois, então desce quando
    ele está na lava lá embaixo e sobe junto quando ele salta; a SmoothCamera suaviza a troca;
  - variáveis: demonio_chefe.camera_mistura, demonio_chefe.camera_dy (ajustáveis) e pato.camera_offset_normal (de
    trabalho); grupo "Câmera da luta" no fim dos eventos externos "Chefe".
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D = 'demonio_chefe'
I, E, grupo = t59.I, t59.E, t59.grupo
VARS_CHEFE = [('camera_mistura', 'number', 0.5), ('camera_dy', 'number', 60)]
VARS_PATO = [('camera_offset_normal', 'number', -140)]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t67/' + '/'.join(p)))


def offset(valor):
    return I('SmoothCamera::SmoothCamera::SetOffsetYOp', 'pato', 'SmoothCamera', '=', valor, '')


def eventos():
    luta = [I('BooleanVariable', 'chefe_trancado', 'True', ''), I('SceneInstancesCount', '', D, '>', '0'),
            I('BooleanObjectVariable', D, 'morto', 'False', '')]
    fora = {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
        I('BooleanVariable', 'chefe_trancado', 'False', ''), I('SceneInstancesCount', '', D, '=', '0'),
        I('BooleanObjectVariable', D, 'morto', 'True', '')]}
    return grupo('Câmera da luta', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Câmera da luta: com a arena trancada a câmera mira entre o pato e o demônio (camera_mistura) mais '
                    'camera_dy px para baixo; fora da luta volta ao deslocamento normal da SmoothCamera do pato.'},
        E([I('SceneJustBegins', '')], [I('SetNumberObjectVariable', 'pato', 'camera_offset_normal', '=', 'pato.SmoothCamera::OffsetY()')]),
        E(luta, [offset(f'({D}.CenterY() - pato.CenterY()) * {D}.camera_mistura + {D}.camera_dy')]),
        E([fora], [offset('pato.camera_offset_normal')]),
    ])


def variaveis(lista, dono, existentes):
    tem = {v['name'] for v in existentes}
    for n, t, v in lista:
        if n not in tem:
            existentes.append({'name': n, 'persistentUuid': uid(dono, n), 'type': t, 'value': v})


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    variaveis(VARS_CHEFE, D, objs[D]['variables'])
    variaveis(VARS_PATO, 'pato', objs['pato']['variables'])
    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not any(e.get('name') == 'Câmera da luta' for e in ext['events']):
        ext['events'].append(eventos())


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
