"""Trecho de plataformas móveis no alto do Inferno (tools/t57_inferno_escalada.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t57_inferno_escalada as t57


class Escalada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.cena = next(l for l in cls.d['layouts'] if l['name'] == 'Inferno')
        cls.plats = {i['persistentUuid']: i for i in cls.cena['instances'] if i['name'] == 'plataforma_movel'}

    def trecho(self):
        return [self.plats[t57.uid(n)] for n, *_ in t57.TRECHO]

    def test_seis_plataformas_com_variaveis(self):
        for p in self.trecho():
            nomes = {v['name'] for v in p['initialVariables']}
            self.assertLessEqual({'ini_x', 'ini_y', 'fim_x', 'fim_y', 'velocidade', 'espera'}, nomes)

    def test_nao_atravessam_o_terreno(self):
        tm = next(i for i in self.cena['instances'] if i['name'] == 'tiles_inferno_escuro_')
        linhas = json.loads(next(p['value'] for p in tm['stringProperties'] if p['name'] == 'tilemap'))['layers'][0]['tiles']
        for p in self.trecho():
            v = {x['name']: x['value'] for x in p['initialVariables']}
            for k in range(101):
                x = v['ini_x'] + (v['fim_x'] - v['ini_x']) * k / 100
                y = v['ini_y'] + (v['fim_y'] - v['ini_y']) * k / 100
                for r in range(int((y - tm['y']) // 64), int((y + p['height'] - tm['y']) // 64) + 1):
                    for c in range(int((x - tm['x']) // 64), int((x + p['width'] - tm['x']) // 64) + 1):
                        if 0 <= r < len(linhas) and 0 <= c < len(linhas[0]):
                            self.assertEqual(linhas[r][c], -1, f'plataforma em cima de tile ({r}, {c})')

    def test_cada_salto_cabe_no_pulo_do_pato(self):
        pato = next(o for o in self.d['objects'] if o['name'] == 'pato')
        b = next(b for b in pato['behaviors'] if b['type'] == 'PlatformBehavior::PlatformerObjectBehavior')
        altura = b['jumpSpeed'] * b['jumpSustainTime'] + b['jumpSpeed'] ** 2 / (2 * b['gravity'])
        ps = self.trecho()
        for a, c in zip(ps, ps[1:]):
            va = {x['name']: x['value'] for x in a['initialVariables']}
            vc = {x['name']: x['value'] for x in c['initialVariables']}
            # melhor momento: o ponto mais alto de a contra o ponto mais baixo de c, e as pontas mais próximas
            sobe = min(va['ini_y'], va['fim_y']) - max(vc['ini_y'], vc['fim_y'])
            vao = min(abs(xa - xc) - a['width'] for xa in (va['ini_x'], va['fim_x']) for xc in (vc['ini_x'], vc['fim_x']))
            self.assertLess(sobe, altura * 0.6)
            self.assertLess(vao, 300)

    def test_rodar_de_novo_nao_duplica(self):
        d = json.loads(json.dumps(self.d))
        t57.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
