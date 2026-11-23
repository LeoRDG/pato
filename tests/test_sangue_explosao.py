"""Poça de sangue e explosão de bolas de fogo do demônio chefe (tools/t60_sangue_e_explosao.py)."""
import json, os, re, sys, unittest
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t60_sangue_e_explosao as t60
sys.path.insert(0, os.path.join(RAIZ, 'tests'))
from folhas import folha


def instrucoes(evs):
    for e in evs:
        yield from e.get('conditions', [])
        yield from e.get('actions', [])
        yield from instrucoes(e.get('events', []))


class SangueExplosao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.objs = {o['name']: o for o in cls.d['objects']}
        cls.ext = {n: {'events': folha(cls.d, n)} for n in ('Sangue', 'Chefe')}

    def vars(self, nome):
        return {v['name']: v['value'] for v in self.objs[nome]['variables']}

    def test_usa_a_poca_que_ja_existe(self):
        self.assertEqual(t60.P, 'sangue')
        self.assertNotIn('poca_sangue', self.objs)
        self.assertFalse(any('poca_sangue' in r['name'] for r in self.d['resources']['resources']))
        self.assertFalse(os.path.exists(os.path.join(RAIZ, 'assets', 'poca_sangue')))

    def test_sangue_usa_variaveis(self):
        texto = json.dumps(self.ext['Sangue']['events'])
        for v in re.findall(r'poca_sangue\.([a-z_]+)\b(?!\()', texto):
            self.assertIn(v, self.vars(t60.P))
        for v in re.findall(r'pato\.([a-z_]+)\b(?!\()', texto):
            self.assertIn(v, self.vars('pato'))
        self.assertLess(self.vars(t60.P)['vel_fator'], 1)
        self.assertLess(self.vars(t60.P)['pulo_fator'], 1)

    def test_explosao_e_ida_e_volta_da_morte(self):
        anims = {a['name']: a['directions'][0] for a in self.objs[t60.D]['animations']}
        ida = [s['image'] for s in anims['morte']['sprites'][:10]]
        exp = [s['image'] for s in anims['explosao']['sprites']]
        self.assertEqual(exp, ida + ida[-2::-1])
        self.assertFalse(anims['explosao']['looping'])
        # as bolas saem no auge do fogo (último quadro da ida)
        t = anims['explosao']['timeBetweenFrames']
        self.assertAlmostEqual(self.vars(t60.D)['explosao_disparo'], 9 * t)

    def test_chefe_usa_variaveis_existentes(self):
        texto = json.dumps(self.ext['Chefe']['events'])
        for dono in (t60.D, t60.B):
            for v in re.findall(dono + r'\.([a-z_]+)\b(?!\()', texto):
                self.assertIn(v, self.vars(dono), f'{dono}.{v}')

    def test_cutelo_so_machuca_no_golpe_de_cutelo(self):
        for e in instrucoes(self.ext['Chefe']['events']):
            pass
        texto = json.dumps(self.ext['Chefe']['events'])
        self.assertIn('"golpe", "=", "\\"cutelo\\""', texto)
        self.assertEqual(texto.count('"Create"}, "parameters": ["", "bola_fogo"'), 3)   # explosão, queda da fase 2 e rajada da fúria

    def test_ligado_no_inferno(self):
        cena = next(l for l in self.d['layouts'] if l['name'] == 'Inferno')
        alvos = [e['target'] for e in cena['events'] if e['type'].endswith('::Link')]
        self.assertIn('CenarioInferno', alvos)
        self.assertGreater(alvos.index('CenarioInferno'), alvos.index('Jogador'))

    @unittest.skip('eventos reorganizados em tools/t131_organizar_eventos.py; a migração antiga não roda mais')
    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t60.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
