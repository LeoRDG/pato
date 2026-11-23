"""Tarefa 130: o demonio_chefe com os pés no chão.

Em todos os quadros (744x384) os pés do demônio em pé acabam na linha 381 (só alguns quadros do ataque, com o pé
erguido, acabam em 378), mas a máscara de colisão descia até y 384. O comportamento de plataforma apoia o fundo da
máscara no chão, então ele flutuava 3 px. Os pontos da máscara abaixo dos pés sobem para y = 381 (a linha dos pés
em pé; usar a de cada quadro faria ele tremer nos quadros do pé erguido); o resto da máscara fica.
Rodar uma vez:  python3 tools/t130_demonio_no_chao.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PES = 381


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    dem = next(o for o in d['objects'] if o['name'] == 'demonio_chefe')
    mudou = 0
    for a in dem['animations']:
        for di in a['directions']:
            for s in di['sprites']:
                for poly in s.get('customCollisionMask') or []:
                    for p in poly:
                        if p['y'] > PES:
                            p['y'] = PES
                            mudou += 1
    if not mudou:
        sys.exit('t130 já foi aplicada; não roda de novo.')
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('pontos da máscara do demônio no pé:', mudou)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
