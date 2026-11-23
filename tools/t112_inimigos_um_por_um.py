"""Tarefa 112: os inimigos decidem um por um (mesmo erro do frenesi da t111, nos outros inimigos).

Condições "comparar dois números" que leem uma variável ou posição do inimigo (ex.: abs(pato.CenterX() -
sapo.CenterX()) < sapo.lingua_alcance) não filtram instâncias e leem só o primeiro inimigo da lista: o que o primeiro
decidia (andar para um lado, investir, atacar, entrar em fúria, ferido) valia para todos daquele tipo. Em cada grupo
abaixo, os eventos de cima que têm uma comparação assim passam a ser um "para cada" do inimigo, com as mesmas
condições, ações e subeventos:
Estados (terrestres) [Terrestre], Condenado azul (investida), Condenado inchado (bolsa de bile), Moscas (enxame com
inércia) [alerta], Olho demoníaco (raio), Pigman (pancada), Sapo (cura e língua), Cutulu (elite) [fúria e
movimento], Voador (bombardeiro), Querubim (arqueiro), Roda do anjo e, no Chefe, Moedas do chefe [moeda].
Pato, arma, barras do HUD, demônio chefe e o tilemap existem uma vez só e ficam como estão.
Rodar uma vez:  python3 tools/t112_inimigos_um_por_um.py
"""
import json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVOS = [  # (eventos externos, grupo, objeto, quantos eventos viram "para cada")
    ('Inimigos', 'Estados (terrestres)', 'Terrestre', 1),
    ('Inimigos', 'Condenado azul (investida)', 'condenado_azul', 1),
    ('Inimigos', 'Condenado inchado (bolsa de bile)', 'condenado_inchado', 1),
    ('Inimigos', 'Moscas (enxame com inércia)', 'moscas', 1),
    ('Inimigos', 'Olho demoníaco (raio)', 'olho_demoniaco', 1),
    ('Inimigos', 'Pigman (pancada)', 'pigman', 1),
    ('Inimigos', 'Sapo (cura e língua)', 'sapo', 1),
    ('Inimigos', 'Cutulu (elite)', 'cutulu', 2),
    ('Inimigos', 'Voador (bombardeiro)', 'voador', 1),
    ('Inimigos', 'Querubim (arqueiro)', 'querubim', 1),
    ('Inimigos', 'Roda do anjo', 'roda_anjo', 1),
    ('Chefe', 'Moedas do chefe', 'moeda', 1),
]
LIVRE = ('BuiltinCommonInstructions::CompareNumbers', 'BuiltinCommonInstructions::CompareStrings')


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def le_o_primeiro(e, obj):
    """Alguma comparação livre no evento ou subeventos lê obj.algo fora de um "para cada" de obj."""
    if e['type'].endswith('ForEach') and e.get('object') == obj:
        return False
    for c in e.get('conditions') or []:
        if c['type']['value'] in LIVRE and re.search(rf'\b{obj}\.', c['parameters'][0] + ' ' + c['parameters'][2]):
            return True
    return any(le_o_primeiro(s, obj) for s in e.get('events') or [])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    ext = {x['name']: x['events'] for x in d['externalEvents']}
    mudou = 0
    for src, grupo, obj, n in ALVOS:
        g = next(e for e in todos(ext[src]) if e.get('name') == grupo and e['type'].endswith('Group'))
        alvo = [e for e in g['events'] if e['type'].endswith('Standard') and le_o_primeiro(e, obj)]
        if not alvo:
            continue
        assert len(alvo) == n, (grupo, len(alvo))
        for e in alvo:
            e['type'] = 'BuiltinCommonInstructions::ForEach'
            e['object'] = obj
            mudou += 1
        com = next((e for e in g['events'] if e['type'].endswith('Comment')), None)
        if com is not None:
            com['comment'] += ' Cada um decide sozinho (para cada).'
    if not mudou:
        sys.exit('t112 já foi aplicada; não roda de novo.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print(mudou, 'eventos viraram "para cada"')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
