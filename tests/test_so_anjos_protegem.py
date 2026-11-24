"""Deus só fica invulnerável enquanto os anjinhos (canalizadores) canalizam; eles vão e voltam além de girar e o
laço deles fere o pato (tools/t156_so_anjos_protegem.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class SoAnjosProtegem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.rosa = m.acha(cls.deus['events'], 'Anel rosa: amor')
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def test_aberto_sem_anjos(self):
        guarda = m.acha(self.deus['events'], 'Pupila fechada')
        (abre,) = [e for e in guarda['events'] if '"deus", "vulneravel", "True"' in tx(e['actions'])]
        c = tx(abre['conditions'])
        self.assertIn('"deus.canal_vivos", "=", "0"', c)
        self.assertIn('"deus", "morto", "False"', c)
        self.assertIn('"deus", "estado", "=", "\\"fase\\""', c, 'fechado na troca de fase')
        self.assertTrue(any(x['type'].get('inverted') for x in abre['conditions']
                            if x['type']['value'] == 'StringObjectVariable'))
        fecha = [e for e in guarda['events'] if '"deus", "vulneravel", "False"' in tx(e['actions'])]
        self.assertEqual(len(fecha), 1, 'só os anjos fecham (sai o fecha/escuro do piscar)')
        self.assertIn('"deus.canal_vivos", ">", "0"', tx(fecha[0]['conditions']))
        nomes = [e.get('name') for e in self.deus['events']]
        self.assertLess(nomes.index('Pupila fechada'), nomes.index('Dano na pupila'))

    def test_vai_e_volta(self):
        # o raio (para fora, até as bordas) é testado em test_anjos_nas_bordas (t158)
        orbita = next(e for e in self.rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']))  # a presa (a solta é da t160)
        self.assertIn('canalizador.vaivem_fase', tx(orbita['actions']))
        cria = [e for e in m.todos(self.deus['events']) if '"Create"}, "parameters": ["", "canalizador"' in tx(e.get('actions', []))]
        self.assertEqual(len(cria), 2, 'o Juízo não cria mais anjinhos (t164)')
        for e in cria:
            a = e['actions']
            k = next(i for i, x in enumerate(a) if x['parameters'][:2] == ['canalizador', 'ang'])
            self.assertEqual(a[k + 1]['parameters'], ['canalizador', 'vaivem_fase', '=', 'canalizador.ang'])
        self.assertIn('vaivem_fase', {x['name'] for x in self.o['canalizador']['variables']})

    def test_laco_fere(self):
        (fere,) = [e for e in m.todos(self.deus['events']) if '"pato", "vida", "-", "deus.laco_dano"' in tx(e.get('actions', []))]
        pai = next(e for e in m.todos(self.deus['events']) if fere in e.get('events', []))
        self.assertEqual(pai.get('object'), 'canalizador')
        t = tx(pai['actions'])
        self.assertIn('"canalizador", "laco_t", "=", "clamp(((pato.CenterX() - canalizador.CenterX()) * (deus.cx - canalizador.CenterX())'
                      ' + (pato.CenterY() - canalizador.CenterY()) * (deus.cy - canalizador.CenterY()))'
                      ' / max(1, pow(deus.cx - canalizador.CenterX(), 2) + pow(deus.cy - canalizador.CenterY(), 2)), 0, 1)"', t)
        c = tx(fere['conditions'])
        for s in ('"pato", "invencivel", "False"', '"pato", "morto", "False"', '"canalizador", "morto", "False"',
                  'deus.laco_raio', 'canalizador.laco_t'):
            self.assertIn(s, c)
        a = tx(fere['actions'])
        self.assertIn('"pato", "invencivel", "True"', a)
        self.assertIn('"pato", "ultimo_agressor", "=", "\\"deus\\""', a)

    def test_variaveis(self):
        for nome in ('canal_vaivem', 'canal_vaivem_vel', 'laco_dano', 'laco_raio'):
            self.assertIn(nome, self.v)
        self.assertIn('laco_t', {x['name'] for x in self.o['canalizador']['variables']})


if __name__ == '__main__':
    unittest.main()
