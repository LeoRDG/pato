"""Tarefa 66: o pulo da lava da fase 2 do chefe fica mais alto.

Migração de uso único: lava.pulo_vel (força do pulo que a lava dá no pato quando o queima) sobe para PULO_VEL, o
bastante para o pato sair do fundo da lava direto para acima das pontes mais altas. Só sobe: se o valor atual já
for maior, fica como está.
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PULO_VEL = 1900          # com a gravidade 2000 do pato, ~900 px de altura (antes 1500, ~560 px)


def migra(d):
    lava = next(o for o in d['objects'] if o['name'] == 'lava')
    v = next(v for v in lava['variables'] if v['name'] == 'pulo_vel')
    if v['value'] < PULO_VEL:
        v['value'] = PULO_VEL


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
