"""Tarefa 135: uma barra só para os chefes. Grupo de objetos novo Chefes (demonio_chefe e cutulu, que têm as mesmas
variáveis de barra: barra_dist, barra_largura, barra_rastro_vel, nome, vida, max_vida, morto). Em HUD > Barras de chefe
os subgrupos Demônio chefe e Cutulu, que eram o mesmo evento com o nome do objeto trocado, viram um subgrupo Chefes com
esse evento sobre o grupo Chefes. O Mercador continua à parte (outra condição e outras variáveis).
Só junta eventos iguais; nenhum valor muda.
Rodar uma vez:  python3 tools/t135_barra_dos_chefes.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEFES = ['demonio_chefe', 'cutulu']


def acha(evs, nome):
    for e in evs:
        if e.get('name') == nome:
            return e
        r = acha(e.get('events') or [], nome)
        if r:
            return r
    return None


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(g['name'] == 'Chefes' for g in d['objectsGroups']):
        sys.exit('t135 já foi aplicada; não roda de novo.')
    hud = next(x for x in d['externalEvents'] if x['name'] == 'HUD')
    barras = acha(hud['events'], 'Barras de chefe')
    subs = {g['name']: g for g in barras['events']}
    dem, cut = subs['Demônio chefe'], subs['Cutulu']
    # os dois eventos são o mesmo, trocando o nome do objeto
    a = json.dumps(dem['events'], ensure_ascii=False).replace('demonio_chefe', 'Chefes')
    b = json.dumps(cut['events'], ensure_ascii=False).replace('cutulu', 'Chefes')
    assert a == b, 'as barras do demônio e do cutulu não são mais iguais'
    d['objectsGroups'].append({'name': 'Chefes', 'objects': [{'name': n} for n in CHEFES]})
    novo_sub = dict(dem, name='Chefes', events=json.loads(a))
    i = barras['events'].index(dem)
    barras['events'] = [e for e in barras['events'] if e is not dem and e is not cut]
    barras['events'].insert(i, novo_sub)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('barra dos chefes sobre o grupo Chefes')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
