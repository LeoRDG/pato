"""A mira fica no mouse e sobe com o recuo (tools/t87_alvo_no_mouse.py, tools/t88_alvo_recuo.py)."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class Alvo(unittest.TestCase):
    def test_alvo_no_mouse_com_recuo(self):
        d = json.load(open(JOGO, encoding='utf-8'))
        ev = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
        e = next(e for e in todos(ev) if any(a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo'
                                             for a in e.get('actions') or []))
        p = next(a for a in e['actions'] if a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo')['parameters']
        for q in (p[2], p[4]):
            self.assertIn('MouseX() - pato.CenterX()', q)          # o mouse, girado em volta da mão
            self.assertIn('alvo.giro', q)
        acoes = [a['parameters'] for a in e['actions'] if a['type']['value'] == 'SetNumberObjectVariable']
        self.assertIn(['alvo', 'giro', '=', '-mira_lado * ToRad(recuo)'], acoes)   # com recuo 0, giro 0: no mouse
        alvo = next(o for o in d['objects'] if o['name'] == 'alvo')
        self.assertIn('giro', {v['name'] for v in alvo['variables']})
        self.assertNotIn('alvo.dist_min', json.dumps(d))


if __name__ == '__main__':
    unittest.main()
