"""Tarefa 104: condenados maiores.

Eles apareciam com 104 a 115 px de altura visível, quase o tamanho do pato (95 px). Um condenado em chamas foi
aumentado à mão no editor para 205x203 (143 px visíveis); os outros condenados do Inferno passam ao mesmo tamanho
visível, cada um pelo desenho dele (o espaço vazio em volta do sprite muda de um para outro):
condenado_em_chamas 205x203 (igual ao aumentado), condenado_azul 200x200 e condenado_inchado 212x212.
Só cresce instância menor que isso, mantendo o meio de baixo no lugar (os pés continuam no chão). O tamanho continua
sendo o da instância no editor: dá para mudar cada um lá.
Rodar uma vez:  python3 tools/t104_condenados_maiores.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAMANHO = {'condenado_em_chamas': (205, 203), 'condenado_azul': (200, 200), 'condenado_inchado': (212, 212)}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    mudou = []
    for l in d['layouts']:
        for i in l['instances']:
            if i['name'] not in TAMANHO or not i.get('customSize'):
                continue
            w, h = TAMANHO[i['name']]
            if i['height'] >= h:
                continue
            i['x'] = round(i['x'] + (i['width'] - w) / 2, 2)
            i['y'] = round(i['y'] + i['height'] - h, 2)
            i['width'], i['height'] = w, h
            mudou.append((l['name'], i['name']))
    if not mudou:
        sys.exit('t104 já foi aplicada (nenhum condenado menor que o tamanho novo); não roda de novo.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print(len(mudou), 'condenados aumentados:', mudou)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
