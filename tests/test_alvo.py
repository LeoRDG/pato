"""A mira não foge do mouse perto do pato (tools/t85_alvo_projecao.py)."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class Alvo(unittest.TestCase):
    def test_alvo_na_projecao_do_mouse(self):
        d = json.load(open(JOGO, encoding='utf-8'))
        alvo = next(o for o in d['objects'] if o['name'] == 'alvo')
        self.assertLessEqual({'dist_min', 'd'}, {v['name'] for v in alvo['variables']})
        ev = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
        e = next(e for e in todos(ev) if any(a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo'
                                             for a in e.get('actions') or []))
        nomes = [(a['type']['value'], a['parameters'][0]) for a in e['actions']]
        k = nomes.index(('SetXY', 'alvo'))
        calc = e['actions'][k - 1]['parameters']
        self.assertEqual(calc[:2], ['alvo', 'd'])
        self.assertIn('max(alvo.dist_min,', calc[3])
        self.assertIn('alvo.d', e['actions'][k]['parameters'][2])
        self.assertNotIn('DistanceBetweenPositions(bocal_x', json.dumps(e['actions'][k]))


if __name__ == '__main__':
    unittest.main()
