"""O 'Aplicar upgrades' fixava a velocidade do pato em 289; agora usa o maxSpeed do comportamento (editável no GDevelop)."""
import json
from t12_armas import PATH

VELHO = '289 * (1 + 0.1 * GlobalVariable(upgrades.velocidade))'
NOVO = 'pato.PlatformerObject::MaxSpeed() * (1 + 0.1 * GlobalVariable(upgrades.velocidade))'


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    n = 0
    def walk(evs):
        nonlocal n
        for e in evs:
            for a in e.get('actions', []):
                if a['type']['value'] == 'PlatformBehavior::MaxSpeed' and a['parameters'][-1] == VELHO:
                    a['parameters'][-1] = NOVO; n += 1
            walk(e.get('events', []))
    for x in d['externalEvents']:
        walk(x['events'])
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    print('trocados', n)


if __name__ == '__main__':
    main()
