"""Tarefa 56: as brasas da lava sobem de verdade.

No GDevelop o emissor de partículas atira na direção do ÂNGULO DO OBJETO, abrindo um leque de emitterAngleB graus
(emitterAngleA não entra na conta). As lava_brasas eram criadas com ângulo 0, então saíam para a direita e só a
gravidade negativa as levantava. Agora, ao criar cada lava_brasas, o evento aponta o emissor para lava.brasa_angulo
(-90 = para cima).

Migração de uso único: ADICIONA a variável lava.brasa_angulo e a ação de apontar logo depois do Create de
lava_brasas (se ainda não estiver lá). O leque (emitterAngleB) só é acertado para 50 se ainda estiver no valor
que a tarefa 51 gravou (-65); se já foi mexido no editor, fica como está.
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    lava, brasas = objs['lava'], objs['lava_brasas']
    if not any(v['name'] == 'brasa_angulo' for v in lava['variables']):
        lava['variables'].append({'name': 'brasa_angulo', 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t56/brasa_angulo')),
                                  'type': 'number', 'value': -90})
    if brasas['emitterAngleA'] == -115 and brasas['emitterAngleB'] == -65:      # ainda como a tarefa 51 deixou
        brasas['emitterAngleA'], brasas['emitterAngleB'] = 0, 50
    n = 0
    for e in anda(next(x for x in d['externalEvents'] if x['name'] == 'Lava')['events']):
        acts = e.get('actions') or []
        for i, a in enumerate(acts):
            if a['type']['value'] == 'Create' and a['parameters'][1] == 'lava_brasas':
                n += 1
                if not any(b['type']['value'] == 'SetAngle' and b['parameters'][0] == 'lava_brasas' for b in acts):
                    acts.insert(i + 1, {'type': {'value': 'SetAngle'}, 'parameters': ['lava_brasas', '=', 'lava.brasa_angulo']})
                break
    assert n == 1, n


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
