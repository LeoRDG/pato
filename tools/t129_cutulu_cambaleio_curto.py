"""Tarefa 129: o cambaleio do cutulu não se renova com tiros.

No estado "dano" a postura (t127) deixava firme = False, e todo acerto em "dano" põe "dano" de novo e zera o
cronômetro "estado" (Inimigos > Estados (terrestres)); com a minigun os acertos vêm a menos de dano_duracao s um do
outro e ele não saía mais. Agora, ao cambalear, firme volta a True na hora: o cambaleio dura só dano_duracao s.
Rodar uma vez:  python3 tools/t129_cutulu_cambaleio_curto.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    folha = next(x for x in d['externalEvents'] if x['name'] == 'Cutulu')
    post = next(e for e in folha['events'] if e.get('name') == 'Postura')
    ev = next(e for e in post['events'] if any(c['parameters'][1:] == ['estado', '=', '"dano"']
                                               for c in e.get('conditions', [])))
    firme = {'type': {'value': 'SetBooleanObjectVariable'}, 'parameters': ['cutulu', 'firme', 'True', '']}
    if firme in ev['actions']:
        sys.exit('t129 já foi aplicada; não roda de novo.')
    ev['actions'].append(firme)
    post['events'][0]['comment'] += ' Ao cambalear, firme volta a True na hora, para tiros não renovarem o cambaleio.'
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cambaleio sem renovar')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
