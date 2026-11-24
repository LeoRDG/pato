"""Juízo com aviso: os laços engrossam e brilham conforme o prazo se aproxima, um som avisa antes do clarão, e os
anjinhos nascem colados em Deus e se afastam aos poucos (tools/t162_juizo_avisa.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

RAIO = '(deus.canal_orbita_raio + deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class JuizoAvisa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.rosa = m.acha(cls.deus['events'], 'Anel rosa: amor')
        cls.evs = list(m.todos(cls.rosa['events']))
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def com(self, trecho, onde='actions'):
        return [e for e in self.evs if trecho in tx(e.get(onde, []))]

    def test_carga_do_juizo(self):
        zera = [e for e in self.rosa['events'] if e['conditions'] == [] and '"deus", "juizo_carga", "=", "0"' in tx(e['actions'])]
        self.assertEqual(len(zera), 1)
        (carga,) = self.com('"deus", "juizo_carga", "=", "min(1, deus.ObjectTimerElapsedTime(\\"golpe\\") / deus.juizo_tempo)"')
        c = tx(carga['conditions'])
        for s in ('"deus", "golpe", "=", "\\"juizo\\""', '"deus", "etapa", "=", "\\"juizo\\""'):
            self.assertIn(s, c)
        ordem = self.rosa['events']
        (linha,) = [e for e in ordem if '"PrimitiveDrawing::LineV2"' in tx(e['actions'])]
        self.assertLess(ordem.index(zera[0]), ordem.index(carga), 'zera e depois carrega')
        self.assertLess(ordem.index(carga), ordem.index(linha))

    def test_lacos_engrossam_e_brilham(self):
        (linha,) = [e for e in self.rosa['events'] if '"PrimitiveDrawing::LineV2"' in tx(e['actions'])]
        (l,) = [a for a in linha['actions'] if a['type']['value'] == 'PrimitiveDrawing::LineV2']
        self.assertEqual(l['parameters'][5], 'deus.laco_espessura * (1 + deus.juizo_engrossa * deus.juizo_carga)')
        (zera,) = [e for e in self.rosa['events'] if e['conditions'] == [] and '"deus", "juizo_carga", "=", "0"' in tx(e['actions'])]
        self.assertIn('"EffectCapability::EffectBehavior::SetEffectDoubleParameter"}, "parameters": ["laco_amor", "Effect", "\\"Effect\\"", '
                      '"\\"outerStrength\\"", "deus.laco_brilho * (1 + deus.juizo_brilha * deus.juizo_carga)"]', tx(self.rosa['events']))

    def test_som_de_aviso(self):
        (avisa,) = self.com('"deus", "juizo_avisou", "True"')
        c = tx(avisa['conditions'])
        self.assertIn('"deus", "juizo_avisou", "False"', c)
        self.assertIn('deus.juizo_tempo - deus.juizo_aviso', c)
        self.assertIn('"deus.canal_vivos", ">", "0"', c)
        self.assertIn('deus.juizo_aviso_tom', tx(avisa['actions']))
        (comeca,) = self.com('"deus", "etapa", "=", "\\"juizo\\""')
        self.assertIn('"deus", "juizo_avisou", "False"', tx(comeca['actions']))

    def test_anjos_nascem_colados(self):
        cria = [e for e in m.todos(self.deus['events']) if '"Create"}, "parameters": ["", "canalizador"' in tx(e.get('actions', []))]
        self.assertEqual(len(cria), 4)
        for e in cria:
            self.assertIn('"canalizador", "surgir", "=", "0"', tx(e['actions']))
        orbitas = [e for e in self.rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions'])]
        self.assertEqual(len(orbitas), 2)
        for e in orbitas:
            t = tx(e['actions'])
            self.assertIn(f'canalizador.surgir * {RAIO}', t)
        self.assertIn('"canalizador", "surgir", "=", "min(1, canalizador.surgir + TimeDelta() / deus.canal_surgir)"', tx(orbitas[0]['actions']))
        self.assertIn('surgir', {x['name'] for x in self.o['canalizador']['variables']})

    def test_variaveis(self):
        for n in ('juizo_carga', 'juizo_engrossa', 'juizo_brilha', 'laco_brilho', 'juizo_aviso', 'juizo_aviso_tom',
                  'juizo_avisou', 'canal_surgir'):
            self.assertIn(n, self.v)
        self.assertLess(self.v['juizo_aviso'], self.v['juizo_tempo'])


if __name__ == '__main__':
    unittest.main()
