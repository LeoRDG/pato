"""Upgrades novos (tools/t197_upgrades_novos.py): vampirismo, ímã, incendiária e cadáver explosivo, no catálogo da loja e
ligados ao combate, com os números em variáveis do pato."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

NOVOS = ('vampirismo', 'ima', 'incendiaria', 'cadaver')


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

    def test_ligados_ao_combate(self):
        for u in NOVOS:
            self.assertIn(f'GlobalVariable(upgrades.{u})', self.com, u)

    def test_numeros_em_variaveis(self):
        pato = {v['name'] for v in m.objeto(self.d, 'pato')['variables']}
        for n in ('vamp_cura', 'upg_ima', 'queima_tempo', 'queima_intervalo', 'queima_dano', 'cadaver_dano', 'cadaver_raio',
                  'cadaver_repulsao', 'cadaver_som_volume'):
            self.assertIn(n, pato)
        for o in next(g for g in self.d['objectsGroups'] if g['name'] == 'Inimigo')['objects']:
            self.assertIn('queima', {v['name'] for v in m.objeto(self.d, o['name'])['variables']}, o['name'])


if __name__ == '__main__':
    unittest.main()
