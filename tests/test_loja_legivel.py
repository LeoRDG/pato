"""Loja legível (tools/t189_loja_legivel.py): a descrição tem espaço entre as linhas, o painel é quase opaco
(o mercador e o pato não aparecem por trás do texto) e a linha escolhida tem uma faixa atrás (loja_faixa),
para não confundir com o amarelo de MAX."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class LojaLegivel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.loja = m.folha(cls.d, 'Loja')['events']

    def test_descricao_com_entrelinha(self):
        c = m.objeto(self.d, 'loja_desc')['content']
        self.assertGreater(c['lineHeight'], c['characterSize'])

    def test_painel_quase_opaco(self):
        self.assertGreaterEqual(m.objeto(self.d, 'loja_painel')['fillOpacity'], 230)

    def test_faixa_na_linha_escolhida(self):
        f = m.objeto(self.d, 'loja_faixa')
        self.assertEqual(f['type'], 'PrimitiveDrawing::Drawer')
        abre = [e for e in m.todos(self.loja) if '"loja_painel", "0", "0"' in json.dumps(e.get('actions', []))]
        self.assertIn('"Create"}, "parameters": ["", "loja_faixa"', json.dumps(abre))
        fecha = [e for e in m.todos(self.loja) if '"Delete"}, "parameters": ["loja_painel"' in json.dumps(e.get('actions', []))]
        self.assertIn('"Delete"}, "parameters": ["loja_faixa"', json.dumps(fecha))
        sel = [e for e in m.todos(self.loja)
               if '"loja_linha", "indice", "=", "loja_sel"' in json.dumps(e.get('conditions', []))]
        self.assertEqual(len(sel), 1)
        self.assertIn('"PrimitiveDrawing::Rectangle"}, "parameters": ["loja_faixa"', json.dumps(sel[0]['actions']))


if __name__ == '__main__':
    unittest.main()
