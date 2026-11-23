"""Tarefa 133: sem a folha CenarioParaiso, que só tinha o grupo Correntes de luz e só era ligada no Paraiso. O grupo vai
para os eventos da própria cena Paraiso, no lugar do link (a ordem dos eventos não muda), e a folha sai.
Só move o grupo como está.
Rodar uma vez:  python3 tools/t133_correntes_na_cena_paraiso.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    folha = next((x for x in d['externalEvents'] if x['name'] == 'CenarioParaiso'), None)
    if folha is None:
        sys.exit('t133 já foi aplicada; não roda de novo.')
    assert [g.get('name') for g in folha['events']] == ['Correntes de luz']
    ligada = [l['name'] for l in d['layouts']
              if any(e['type'].endswith('::Link') and e.get('target') == 'CenarioParaiso' for e in l['events'])]
    assert ligada == ['Paraiso'], ligada
    cena = next(l for l in d['layouts'] if l['name'] == 'Paraiso')
    i = next(i for i, e in enumerate(cena['events'])
             if e['type'].endswith('::Link') and e.get('target') == 'CenarioParaiso')
    cena['events'][i:i + 1] = folha['events']
    d['externalEvents'] = [x for x in d['externalEvents'] if x['name'] != 'CenarioParaiso']
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('Correntes de luz na cena Paraiso')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
