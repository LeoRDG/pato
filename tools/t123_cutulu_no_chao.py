"""Tarefa 123: o cutulu deixa de flutuar acima do chão.

Em todos os quadros do cutulu (192x112) os pés acabam na linha 96 do desenho, mas a máscara de colisão desce até
y 99-100 (fundo um pouco inclinado). O comportamento de plataforma apoia o fundo da máscara no chão, então o desenho
ficava 4 px acima (12 px na tela, com a instância 3x). Os pontos da máscara abaixo dos pés sobem para y = 96 (fundo
reto, nos pés); o resto da máscara, desenhado no editor, fica como está.
Rodar uma vez:  python3 tools/t123_cutulu_no_chao.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PES = 96


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cut = next(o for o in d['objects'] if o['name'] == 'cutulu')
    mudou = 0
    for a in cut['animations']:
        for di in a['directions']:
            for s in di['sprites']:
                for poly in s.get('customCollisionMask') or []:
                    for p in poly:
                        if p['y'] > PES:
                            p['y'] = PES
                            mudou += 1
    if not mudou:
        sys.exit('t123 já foi aplicada; não roda de novo.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('pontos da máscara do cutulu no pé:', mudou)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
