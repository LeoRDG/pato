"""Tarefa 80: o "zumbi" é um condenado em chamas; vira condenado_em_chamas e passa para o Inferno.

- Objeto zumbi -> condenado_em_chamas em todo lugar (objeto, grupos, painel, eventos, expressões como zumbi.vida).
- Imagens: assets/inimigos/purgatorio/zumbi/ -> assets/inimigos/inferno/condenado_em_chamas/ (só o caminho muda).
- Painel de objetos: sai de inimigos/purgatorio e entra em inimigos/inferno, depois do condenado_inchado.
- Eventos: o grupo "Zumbi (sem cabeça)" vira "Condenado em chamas (frenesi)". Mesma mecânica (abaixo de frenesi_abaixo da
  vida corre sem tranco trocando de direção), mas em vez de perder a cabeça ele se inflama: faíscas e som de fogo no
  lugar do sangue verde e do som de carne rasgando.
- Sangue: se ainda for "verde" (o do zumbi), vira "brasa"; qualquer outro valor fica como está.
Rodar uma vez:  python3 tools/t80_condenado_em_chamas.py
"""
import json, os, re, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VELHO, NOVO = 'zumbi', 'condenado_em_chamas'
PASTA_VELHA, PASTA_NOVA = 'assets/inimigos/purgatorio/zumbi', 'assets/inimigos/inferno/condenado_em_chamas'
EXPR = re.compile(r'(?<![A-Za-z0-9_])' + VELHO + r'(?=\.)')


def troca(x):
    if isinstance(x, dict):
        return {k: troca(v) for k, v in x.items()}
    if isinstance(x, list):
        return [troca(v) for v in x]
    if isinstance(x, str):
        return NOVO if x == VELHO else EXPR.sub(NOVO, x)
    return x


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events', []))


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if any(o['name'] == NOVO for o in d['objects']):
        sys.exit('t80 já foi aplicada (condenado_em_chamas existe); não roda de novo.')

    # imagens
    if os.path.isdir(os.path.join(RAIZ, PASTA_VELHA)):
        os.makedirs(os.path.dirname(os.path.join(RAIZ, PASTA_NOVA)), exist_ok=True)
        subprocess.run(['git', 'mv', PASTA_VELHA, PASTA_NOVA], cwd=RAIZ, check=True)
    renomeia = {}
    for r in d['resources']['resources']:
        f = r.get('file', '')
        if f.startswith(PASTA_VELHA + '/'):
            r['file'] = PASTA_NOVA + f[len(PASTA_VELHA):]
            if r['name'] == f:
                renomeia[f] = r['name'] = r['file']
    if renomeia:
        def troca_rec(x):
            if isinstance(x, dict):
                return {k: troca_rec(v) for k, v in x.items()}
            if isinstance(x, list):
                return [troca_rec(v) for v in x]
            return renomeia.get(x, x) if isinstance(x, str) else x
        d = troca_rec(d)

    # nome em todo lugar
    d = troca(d)

    # painel: purgatorio -> inferno
    ini = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'inimigos')
    pasta = {c['folderName']: c for c in ini['children'] if 'folderName' in c}
    item = next(c for c in pasta['purgatorio']['children'] if c.get('objectName') == NOVO)
    pasta['purgatorio']['children'].remove(item)
    inf = pasta['inferno']['children']
    k = next((i + 1 for i, c in enumerate(inf) if c.get('objectName') == 'condenado_inchado'), len(inf))
    inf.insert(k, item)

    # eventos: o grupo e o sabor (inflama em vez de perder a cabeça)
    evs = next(e for e in d['externalEvents'] if e['name'] == 'Inimigos')['events']
    for e in todos(evs):
        if e.get('type') == 'BuiltinCommonInstructions::Group' and e.get('name') == 'Zumbi (sem cabeça)':
            e['name'] = 'Condenado em chamas (frenesi)'
            for c in e['events']:
                if c['type'] == 'BuiltinCommonInstructions::Comment':
                    c['comment'] = ('Condenado em chamas: anda devagar até o pato. Abaixo de frenesi_abaixo da vida se inflama: '
                                    'firme (sem tranco), corre a frenesi_vel trocando de direção a cada '
                                    'frenesi_troca_min..max s (mais vezes para o pato) e pula à toa.')
        acoes = e.get('actions', [])
        if any(a['type']['value'] == 'Create' and a['parameters'][1] == 'sangue_verde'
               and a['parameters'][2].startswith(NOVO + '.') for a in acoes):
            novas = []
            for a in acoes:
                p = a['parameters']
                if a['type']['value'] == 'Create' and p[1] == 'sangue_verde':
                    novas.append({'type': {'value': 'Create'}, 'parameters': ['', 'explosao_faiscas', f'{NOVO}.CenterX()',
                                                                             f'{NOVO}.CenterY()', '']})
                elif a['type']['value'] == 'SetAngle' and p[0] == 'sangue_verde':
                    continue
                elif a['type']['value'] == 'PlaySound' and p[1] == 'som_arranca.wav':
                    a['parameters'] = ['', 'som_espiral.wav', '', p[3], 'RandomFloatInRange(1.15, 1.3)']
                    novas.append(a)
                else:
                    novas.append(a)
            e['actions'] = novas

    o = next(o for o in d['objects'] if o['name'] == NOVO)
    for v in o['variables']:
        if v['name'] == 'sangue' and v.get('value') == 'verde':
            v['value'] = 'brasa'

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('zumbi -> condenado_em_chamas, no Inferno')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
