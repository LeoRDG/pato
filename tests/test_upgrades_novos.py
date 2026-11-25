"""Upgrades novos (tools/t197_upgrades_novos.py): dos quatro, só o vampirismo ficou (ímã, incendiária e cadáver explosivo saíram
na t205); ele está no catálogo da loja e ligado ao combate, com o número em variável do pato."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

NOVOS = ('vampirismo',)
SAIRAM = ('ima', 'incendiaria', 'cadaver')


class UpgradesNovos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.g = {v['name']: v for v in cls.d['variables']}
        cls.com = json.dumps(m.folha(cls.d, 'Combate')['events'])

    def test_no_catalogo_e_nos_niveis(self):
        ids = [next(c['value'] for c in it['children'] if c['name'] == 'id') for it in self.g['loja_catalogo']['children']]
        niveis = {c['name'] for c in self.g['upgrades']['children']}
        for u in NOVOS:
            self.assertIn(u, ids)
            self.assertIn(u, niveis)
        for u in SAIRAM:
            self.assertNotIn(u, ids)
            self.assertNotIn(u, niveis)

    def test_ligados_ao_combate(self):
        for u in NOVOS:
            self.assertIn(f'GlobalVariable(upgrades.{u})', self.com, u)
        for u in SAIRAM:
            self.assertNotIn(f'upgrades.{u}', self.com, u)

    def test_numeros_em_variaveis(self):
        pato = {v['name'] for v in m.objeto(self.d, 'pato')['variables']}
        self.assertIn('vamp_cura', pato)
        for n in ('upg_ima', 'queima_tempo', 'cadaver_dano'):
            self.assertNotIn(n, pato)


if __name__ == '__main__':
    unittest.main()
