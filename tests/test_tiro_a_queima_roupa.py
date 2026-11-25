"""Tiro à queima-roupa (tools/t195_tiro_a_queima_roupa.py): cada bala varre com um raio do ponto do quadro anterior (no primeiro
quadro, o ombro do pato na linha do cano) até onde está, e é posta no primeiro inimigo vivo que cruzou."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class QueimaRoupa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.proj = m.acha(m.folha(cls.d, 'Combate')['events'], 'Projéteis')['events']

    def test_varredura_antes_do_dano(self):
        nomes = [e.get('name') for e in self.proj]
        i = nomes.index('Varredura da bala (queima-roupa e bala rápida)')
        self.assertLess(i, nomes.index('Dano da bala'))
        self.assertLess(i, nomes.index('Explosão da granada'))
        v = self.proj[i]['events'][0]
        ray = next(c for c in v['conditions'] if c['type']['value'] == 'RaycastToPosition')
        self.assertEqual(ray['parameters'][:3], ['Inimigo', 'projetil.rcx', 'projetil.rcy'])
        self.assertIn('NumberObjectVariable', [c['type']['value'] for c in v['conditions']])   # só inimigo que a bala ainda não acertou

    def test_ponto_do_encontro_em_variavel_de_cena(self):
        # o raio grava em variável de cena; se fosse global, a expressão leria a global (0) e a bala iria para a origem
        self.assertFalse(any(v['name'] == 'tiro_hx' for v in self.d['variables']))
        for l in self.d['layouts']:
            if any(v['name'] == 'laser_x' for v in l['variables']):
                self.assertTrue(any(v['name'] == 'tiro_hx' for v in l['variables']), l['name'])

    def test_comeca_no_ombro(self):
        ini = m.acha(self.proj, 'Balas (alcance, queda e perfuração)')['events'][0]
        rc = [a['parameters'][3] for a in ini['actions'] if a['parameters'][:2] == ['projetil', 'rcx']]
        self.assertTrue(rc and 'pato.tiro_ombro_frac' in rc[0])


if __name__ == '__main__':
    unittest.main()
