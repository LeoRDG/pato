"""Tarefa 120: os quadros do pigman deixam de pular de lugar.

Os quadros do pigman têm tamanhos diferentes (80x80 na maioria, mas 96x80, 80x160, 126x126, 126x160, 160x80, 180x80
e 240x80 no ataque_1, ataque_2 e no fim da morte), com o pigman centrado no quadro maior. Todos tinham ponto de
origem (0, 0) e a máscara de colisão no canto (0,0)-(80,80); o GDevelop desenha o quadro com o canto de cima à
esquerda na posição do objeto, então nesses quadros o pigman descia até 40 px (80 px na tela, com a instância 2x)
e ia até 80 px para o lado, e a máscara ficava no canto vazio.
Cada quadro maior ganha ponto de origem ((largura - 80) / 2, (altura - 80) / 2), onde o pigman está, e a máscara
anda o mesmo tanto. Com o centro automático (meio do quadro), virado para a esquerda o quadro espelha em volta do
mesmo ponto e o pigman também fica parado. As imagens não mudam.
Só mexe em quadros que ainda estão com origem (0, 0) e a máscara padrão (ninguém ajustou no editor).
Rodar uma vez:  python3 tools/t120_pigman_quadros_alinhados.py
"""
import json, os, sys
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = (80, 80)
MASCARA_PADRAO = [(80, 0), (0, 0), (0, 0), (0, 0), (0, 80), (80, 80)]


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    arq = {r['name']: r['file'] for r in d['resources']['resources']}
    pig = next(o for o in d['objects'] if o['name'] == 'pigman')
    mudou = []
    for a in pig['animations']:
        for di in a['directions']:
            for i, s in enumerate(di['sprites']):
                w, h = Image.open(os.path.join(RAIZ, arq[s['image']])).size
                if (w, h) == BASE:
                    continue
                o = s['originPoint']
                masc = s.get('customCollisionMask') or []
                padrao = len(masc) == 1 and [(p['x'], p['y']) for p in masc[0]] == MASCARA_PADRAO
                if (o['x'], o['y']) != (0, 0) or not padrao:
                    continue
                dx, dy = (w - BASE[0]) // 2, (h - BASE[1]) // 2
                o['x'], o['y'] = dx, dy
                for p in masc[0]:
                    p['x'] += dx
                    p['y'] += dy
                mudou.append(f"{a['name']}[{i}] {w}x{h} -> origem ({dx}, {dy})")
    if not mudou:
        sys.exit('t120 já foi aplicada; não roda de novo.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('\n'.join(mudou))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
