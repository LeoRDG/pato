"""Tarefa 92: saem os grupos de eventos dos inimigos que o usuário removeu do jogo (condenado, condenada,
condenado_torto e atirador), que ficaram apontando para objetos que não existem mais:
  Inimigos > Inferno > Condenado (se levanta), Condenada (joga ossos), Condenado torto (pulador)
  Inimigos > Purgatório > Atirador
Só sai um grupo se o objeto dele não existir mais. Rodar uma vez:  python3 tools/t92_remove_eventos_inimigos_removidos.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRUPOS = {'Condenado (se levanta)': 'condenado', 'Condenada (joga ossos)': 'condenada',
          'Condenado torto (pulador)': 'condenado_torto', 'Atirador': 'atirador'}


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    objetos = {o['name'] for o in d['objects']}
    vivos = {g: o for g, o in GRUPOS.items() if o in objetos}
    if vivos:
        sys.exit(f'objetos ainda existem, não mexo: {vivos}')
    removidos = []

    def poda(evs):
        fica = []
        for e in evs:
            if e['type'] == 'BuiltinCommonInstructions::Group' and e.get('name') in GRUPOS:
                removidos.append(e['name'])
                continue
            if e.get('events'):
                e['events'] = poda(e['events'])
            fica.append(e)
        return fica

    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')
    ini['events'] = poda(ini['events'])
    if not removidos:
        sys.exit('t92 já foi aplicada (nenhum grupo para remover); não roda de novo.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('grupos removidos:', ', '.join(removidos))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
