"""Tarefa 89: upgrade de pulo na loja (mais pulos no ar).

Item novo no catálogo (depois de Velocidade): Pulo, +1 pulo no ar por nível, 3 níveis, mesmo preço dos outros.
O pato já tem pulo duplo pelo comportamento AdvancedJump (AirJumpCountMaximum = 1); o upgrade soma a isso.
- Global upgrades.pulo (nível comprado, começa em 0).
- Variáveis novas do pato (só se faltarem): upg_pulo = 1 (pulos no ar a mais por nível) e pulos_ar_base (auxiliar:
  o máximo de pulos no ar do comportamento, guardado no início da cena como velocidade_base).
- AplicarUpgrades: no início da cena, pato.pulos_ar_base = AdvancedJump::AirJumpsMax(); ao aplicar os upgrades,
  SetAirJumpCountMaximum(pulos_ar_base + upg_pulo * upgrades.pulo). Sempre a partir da base, então não acumula.
Só adiciona; se algo já existe, mantém. Rodar uma vez:  python3 tools/t89_upgrade_pulo.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PULOS = 'pato.pulos_ar_base + pato.upg_pulo * GlobalVariable(upgrades.pulo)'


def uid(chave):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t89/' + chave))


def var(nome, tipo, valor, chave):
    return {'name': nome, 'persistentUuid': uid(chave), 'type': tipo, 'value': valor}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if 'upgrades.pulo' in txt:
        sys.exit('t89 já foi aplicada (upgrades.pulo já é usado); não roda de novo.')

    g = {v['name']: v for v in d['variables']}
    if not any(c['name'] == 'pulo' for c in g['upgrades']['children']):
        g['upgrades']['children'].append(var('pulo', 'number', 0, 'upgrades/pulo'))
    cat = g['loja_catalogo']['children']
    ids = [next(x['value'] for x in it['children'] if x['name'] == 'id') for it in cat]
    if 'pulo' not in ids:
        item = {'persistentUuid': uid('cat/pulo'), 'type': 'structure', 'children': [
            var('descricao', 'string', '+1 pulo no ar por nível', 'cat/descricao'),
            var('id', 'string', 'pulo', 'cat/id'),
            var('nivel_max', 'number', 3, 'cat/nivel_max'),
            var('nome', 'string', 'Pulo', 'cat/nome'),
            var('preco_base', 'number', 50, 'cat/preco_base'),
            var('preco_mult', 'number', 1.6, 'cat/preco_mult'),
            var('requer', 'string', '', 'cat/requer'),
            var('tipo', 'string', 'upgrade', 'cat/tipo')]}
        cat.insert(ids.index('velocidade') + 1 if 'velocidade' in ids else len(cat), item)

    pato = next(o for o in d['objects'] if o['name'] == 'pato')
    tem = {v['name'] for v in pato['variables']}
    for nome, valor in (('upg_pulo', 1), ('pulos_ar_base', 0)):
        if nome not in tem:
            pato['variables'].append(var(nome, 'number', valor, 'pato/' + nome))

    ev = next(x for x in d['externalEvents'] if x['name'] == 'AplicarUpgrades')['events']
    base = next(e for e in todos(ev) if any(a['parameters'][:2] == ['pato', 'velocidade_base']
                                            for a in e.get('actions') or []))
    base['actions'].append({'type': {'value': 'SetNumberObjectVariable'},
                            'parameters': ['pato', 'pulos_ar_base', '=', 'pato.AdvancedJump::AirJumpsMax()']})
    aplica = next(e for e in todos(ev) if any(a['type']['value'] == 'PlatformBehavior::MaxSpeed'
                                              for a in e.get('actions') or []))
    k = next(i for i, a in enumerate(aplica['actions']) if a['type']['value'] == 'PlatformBehavior::MaxSpeed')
    aplica['actions'].insert(k + 1, {'type': {'value': 'AdvancedJump::AdvancedJump::SetAirJumpCountMaximum'},
                                     'parameters': ['pato', 'AdvancedJump', PULOS, '']})
    for e in todos(ev):
        if e['type'] == 'BuiltinCommonInstructions::Comment' and 'velocidade +10%' in e.get('comment', ''):
            e['comment'] = e['comment'].replace('velocidade +10%', 'velocidade +10%, +1 pulo no ar (upg_pulo)', 1)

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('upgrade de pulo (pulos no ar) adicionado')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
