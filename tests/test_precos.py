"""Preços da loja (tools/t198_precos.py, baixados na t205): a loja inteira custa umas duas idas ao Inferno."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Precos(unittest.TestCase):
    def test_loja_custa_varias_corridas(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
        total = 0
        for it in cat['children']:
            c = {x['name']: x.get('value') for x in it['children']}
            self.assertGreaterEqual(c['preco_base'], 100, c['id'])
            total += sum(round(c['preco_base'] * c['preco_mult'] ** n) for n in range(int(c['nivel_max'])))
        # uma ida ao Inferno solta ~3700 moedas: nem uma ida só compra tudo, nem precisa de muitas
        self.assertGreater(total, 5000)
        self.assertLess(total, 15000)
        self.assertGreater(next(v['value'] for v in d['variables'] if v['name'] == 'moedas_total'), 0)   # moedas no começo


if __name__ == '__main__':
    unittest.main()
