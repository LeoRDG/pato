"""Pegar moeda solta um brilho dourado (moeda_brilho) onde ela estava (tools/t174_moeda_brilho.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class MoedaBrilho(unittest.TestCase):
    def test(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        o = m.objeto(d, 'moeda_brilho')
        self.assertTrue(o['additive'] and o['destroyWhenNoParticles'])
        self.assertLess(o['particleSize1'], 20)
        g = m.acha(m.acha(m.folha(d, 'Combate')['events'], 'Moeda')['events'], 'Coleta')
        (e,) = [e for e in g['events'] if '"CollisionNP"}, "parameters": ["moeda", "pato"' in tx(e['conditions'])]
        self.assertIn('"Create"}, "parameters": ["", "moeda_brilho", "moeda.CenterX()", "moeda.CenterY()"', tx(e['actions']))
        tipos = [a['type']['value'] for a in e['actions']]
        i = next(i for i, a in enumerate(e['actions']) if a['type']['value'] == 'Create' and a['parameters'][1] == 'moeda_brilho')
        self.assertTrue(all(not (a['type']['value'] == 'Delete' and a['parameters'][0] == 'moeda') for a in e['actions'][:i]))


if __name__ == '__main__':
    unittest.main()
