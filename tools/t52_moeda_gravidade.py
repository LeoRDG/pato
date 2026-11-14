"""Tarefa 52: nem toda moeda tem gravidade.

moeda.tem_gravidade (booleano, começa True): com True a moeda cai, quica e para como sempre (as que os inimigos
soltam); com False ela fica flutuando onde foi posta. Para uma moeda colocada na cena flutuar, desmarque
tem_gravidade nas variáveis daquela instância no editor de cena. O ímã e a coleta valem para as duas.

Migração de uso único que só ADICIONA: a variável (se faltar) e a condição no evento da Física que aplica a
gravidade e o movimento (se ainda não estiver lá). Nenhum valor existente é alterado.
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAR = 'tem_gravidade'


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def migra(d):
    moeda = next(o for o in d['objects'] if o['name'] == 'moeda')
    if not any(v['name'] == VAR for v in moeda['variables']):
        moeda['variables'].append({'name': VAR, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t52/' + VAR)),
                                   'type': 'boolean', 'value': True})
    n = 0
    for fonte in d['layouts'] + d['externalEvents']:
        for e in anda(fonte['events']):
            aplica = any(a['type']['value'] == 'SetNumberObjectVariable' and a['parameters'][:2] == ['moeda', 'vy']
                         and 'moeda.gravidade' in a['parameters'][3] for a in e.get('actions') or [])
            if not aplica:
                continue
            n += 1
            if not any(c['type']['value'] == 'BooleanObjectVariable' and c['parameters'][:2] == ['moeda', VAR]
                       for c in e['conditions']):
                e['conditions'].append({'type': {'value': 'BooleanObjectVariable'}, 'parameters': ['moeda', VAR, 'True', '']})
    assert n == 1, f'esperava 1 evento que aplica a gravidade da moeda, achei {n}'


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
