"""Tarefa 105: inimigos que viravam de costas para o pato.

sprite_esquerda diz para que lado o desenho olha; com ele errado, o evento de virar deixa o inimigo de costas para o
pato. O voador (caveira de fogo), a caveira azul e o olho demoníaco são desenhados olhando para a esquerda (o rosto /
a pupila à esquerda, o fogo e os tentáculos ficando para trás à direita), mas estavam com sprite_esquerda False.
Passam a True. Os outros conferem com o desenho (pigman e sapo para a direita; condenado azul, inchado, moscas,
caveira gigante e demônio chefe para a esquerda; os de frente tanto faz).
Rodar uma vez:  python3 tools/t105_inimigos_olham_para_o_pato.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLHAM_ESQUERDA = ('voador', 'caveira_azul', 'olho_demoniaco')


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    mudou = []
    for o in d['objects']:
        if o['name'] in OLHAM_ESQUERDA:
            v = next(x for x in o['variables'] if x['name'] == 'sprite_esquerda')
            if v['value'] is False:
                v['value'] = True
                mudou.append(o['name'])
    if not mudou:
        sys.exit('t105 já foi aplicada; não roda de novo.')
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('olham para o pato:', mudou)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
