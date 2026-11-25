"""Preços da loja (tools/t198_precos.py): a loja inteira custa várias idas ao Inferno, não uma."""
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
        self.assertGreater(total, 15000)   # uma ida ao Inferno solta ~3700 moedas


if __name__ == '__main__':
    unittest.main()
