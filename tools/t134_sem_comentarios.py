"""Tarefa 134: sem comentários nos eventos; o nome de cada grupo e subgrupo já diz o que ele faz. Tira o comentário de
uma frase que abria cada grupo (t131). Só esses: comentário em outro lugar fica.
Rodar uma vez:  python3 tools/t134_sem_comentarios.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def limpa(evs):
    n = 0
    for e in evs:
        filhos = e.get('events') or []
        if e['type'].endswith('::Group') and filhos and filhos[0]['type'].endswith('::Comment'):
            del filhos[0]
            n += 1
        n += limpa(filhos)
    return n


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    n = sum(limpa(x['events']) for x in d['externalEvents'] + d['layouts'])
    if not n:
        sys.exit('t134 já foi aplicada; não roda de novo.')
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print(f'{n} comentários tirados')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
