"""Moedas do demônio chefe morto na fase 2 caem nas pontes (tools/t68_moedas_nas_pontes.py)."""
import json, os, re, sys, unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from folhas import folha, inimigos_todos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t68_moedas_nas_pontes as t68


class MoedasNasPontes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.objs = {o['name']: o for o in cls.d['objects']}
        cls.ext = folha(cls.d, 'Chefe')
        cls.grupo = next(e for e in cls.ext if e.get('name') == 'Moedas do chefe')

    def vars(self, nome):
        return {v['name']: v['value'] for v in self.objs[nome]['variables']}

    def test_variaveis_existem(self):
        texto = json.dumps(self.grupo, ensure_ascii=False)
        for dono in (t68.D, t68.M):
            for v in re.findall(dono + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(v, self.vars(dono), f'{dono}.{v}')
        cena = {v['name'] for v in next(l for l in self.d['layouts'] if l['name'] == 'Inferno')['variables']}
        for v in re.findall(r'Variable\(([a-z_]+)\)', texto):
            self.assertIn(v, cena)
        # cada moeda recém-criada sorteia uma ponte da zona e recebe o arco até ela
        self.assertIn('"AjoutHasard"}, "parameters": ["", "tiles_inferno_ponte"]', texto)
        self.assertIn('"CompareObjectTimer"}, "parameters": ["moeda", "\\"vida\\"", "<=", "0"]', texto)
        self.assertNotIn('JsCode', texto)

    def test_so_na_fase2_e_depois_das_moedas_do_combate(self):
        texto = json.dumps(self.grupo)
        self.assertIn('"fase2", "True"', texto)
        self.assertIn('"morto", "True"', texto)
        # as moedas são criadas nos eventos do Combate, que vêm antes do Chefe no Inferno
        cena = next(l for l in self.d['layouts'] if l['name'] == 'Inferno')
        alvos = [e['target'] for e in cena['events'] if e['type'].endswith('::Link')]
        self.assertLess(alvos.index('Combate'), alvos.index('CenarioInferno'))

    def test_arco_chega_descendo(self):
        """Com o menor tempo de voo a moeda que sai da lava ainda chega descendo na ponte mais alta."""
        v = self.vars(t68.D)
        g = self.vars(t68.M)['gravidade']
        cena = next(l for l in self.d['layouts'] if l['name'] == 'Inferno')
        pontes = [i['y'] for i in cena['instances'] if i['name'] == t68.PONTE and i['x'] > 11000]
        lava = next(i for i in cena['instances'] if i['name'] == 'lava' and i['x'] > 11000)
        # as moedas saem do centro do demônio parado na lava (afundado lava_afunda px; ele tem 384 px de altura)
        superficie = lava['y'] + lava['height'] * self.vars('lava')['superficie_frac']
        centro_chefe = superficie + v['lava_afunda'] - 384 / 2
        subida = centro_chefe - min(pontes)
        t = v['moedas_ponte_tempo_min']
        self.assertGreater(g * t * t / 2, subida)

    @unittest.skip('eventos reorganizados em tools/t131_organizar_eventos.py; a migração antiga não roda mais')
    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t68.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
