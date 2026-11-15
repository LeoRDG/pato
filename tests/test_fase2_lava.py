"""Segunda fase do demônio chefe na lava embaixo da arena (tools/t63_fase2_lava.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t63_fase2_lava as t63


def eventos(evs):
    for e in evs:
        yield e
        yield from eventos(e.get('events', []))


class Fase2Lava(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.objs = {o['name']: o for o in cls.d['objects']}
        cls.cena = next(l for l in cls.d['layouts'] if l['name'] == 'Inferno')
        cls.chefe = next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')['events']
        cls.grupo = next(e for e in cls.chefe if e.get('name') == 'Fase 2')
        cls.cv = {v['name']: v['value'] for v in cls.cena['variables']}

    def vars(self, nome):
        return {v['name']: v['value'] for v in self.objs[nome]['variables']}

    def mapa(self):
        i = next(i for i in self.cena['instances'] if i['name'] == t63.TM)
        return i, json.loads(next(x['value'] for x in i['stringProperties'] if x['name'] == 'tilemap'))['layers'][0]['tiles']

    def test_zona_que_quebra_e_o_piso_da_arena_sobre_a_lava(self):
        i, t = self.mapa()
        c0, c1 = (self.cv['quebra_x_min'] - i['x']) // 64, (self.cv['quebra_x_max'] - i['x']) // 64
        r0, r1 = (self.cv['quebra_y_min'] - i['y']) // 64, (self.cv['quebra_y_max'] - i['y']) // 64
        self.assertTrue(all(t[r][c] >= 0 for r in range(r0, r1) for c in range(c0, c1)), 'a zona é piso sólido')
        self.assertTrue(all(t[r1][c] < 0 for c in range(c0, c1)), 'embaixo do piso é vazio')
        lavas = [l for l in self.cena['instances'] if l['name'] == t63.LAVA]
        for x in (self.cv['quebra_x_min'], self.cv['quebra_x_max'] - 1):
            self.assertTrue(any(l['x'] <= x < l['x'] + l['width'] for l in lavas), f'lava embaixo de x {x}')
        self.assertGreaterEqual(self.cv['quebra_topo_linhas'], 1, 'os ataques comuns não abrem buraco por cima')

    def test_pontes_sobre_a_lava(self):
        pontes = [p for p in self.cena['instances'] if p.get('persistentUuid', '').startswith('') and
                  p.get('persistentUuid') in {t63.uid('ponte', str(k)) for k in range(len(t63.PONTES))}]
        self.assertEqual(len(pontes), len(t63.PONTES))
        lava = next(l for l in self.cena['instances'] if l['name'] == t63.LAVA and l['x'] <= pontes[0]['x'] < l['x'] + l['width'])
        sup = lava['y'] + lava['height'] * self.vars(t63.LAVA)['superficie_frac']
        hit = {int(x) for x in self.objs[t63.PONTE]['content']['tilesWithHitBox'].split(',')}
        for p in pontes:
            tiles = json.loads(p['stringProperties'][0]['value'])['layers'][0]['tiles']
            self.assertTrue(all(x in hit for x in tiles[0]))
            self.assertLess(p['y'], sup + self.vars(t63.LAVA)['dano_margem'], 'o pato na ponte não queima')
            self.assertGreater(p['zOrder'], lava['zOrder'])
            self.assertTrue(self.cv['quebra_x_min'] <= p['x'] and p['x'] + 64 * len(tiles[0]) <= self.cv['quebra_x_max'])
        # parado na lava o cutelo não alcança a ponte; no alto do pulo alcança o pato em pé nela
        dv = self.vars(t63.D)
        altura_chefe = 384
        y_chefe = sup + dv['lava_afunda'] - altura_chefe
        pato = next(i for i in self.cena['instances'] if i['name'] == 'pato')
        for p in pontes:
            centro_pato, topo_pato = p['y'] - pato['height'] / 2, p['y'] - pato['height']
            self.assertLess(centro_pato, y_chefe + dv['golpe_topo'], 'a ponte é alta')
            # o salto acaba com o pé dele lava_golpe_baixo abaixo da tábua: o cutelo pega o pato em pé nela
            y_golpe = p['y'] - altura_chefe + dv['lava_golpe_baixo']
            self.assertGreater(centro_pato, y_golpe + dv['golpe_topo'])
            self.assertLess(topo_pato, y_golpe + altura_chefe)
            # pulando por cima dele (o pé um pato acima da tábua) o pato escapa
            self.assertLess(centro_pato - pato['height'], y_golpe + dv['golpe_topo'])
        # bem avisado: fica parado no alto antes de cair, e o golpe só machuca logo na batida
        self.assertGreater(dv['lava_espera_t'], 0.3)
        self.assertLess(dv['lava_golpe_janela'], dv['lava_cravado_t'])
        # a animação do cutelo (solta no quadro do golpe) não acaba antes de ele sair do cravado
        anim = next(a for a in self.objs[t63.D]['animations'] if a['name'] == 'ataque')['directions'][0]
        self.assertLess(dv['lava_quadro_espera'], dv['lava_quadro_golpe'])
        # o pulo da lava (sem segurar) leva o pé do pato do fundo da lava até acima da ponte mais baixa
        g = next(b for b in self.objs['pato']['behaviors'] if b['type'].endswith('PlatformerObjectBehavior'))['gravity']
        fundo = lava['y'] + lava['height'] - 54
        self.assertLess(fundo - self.vars(t63.LAVA)['pulo_vel'] ** 2 / (2 * g), max(p['y'] for p in pontes))
        # ... e com folga acima da ponte mais alta (tools/t66_pulo_da_lava.py)
        self.assertLess(fundo - self.vars(t63.LAVA)['pulo_vel'] ** 2 / (2 * g), min(p['y'] for p in pontes) - pato['height'])
        self.assertLess(dv['lava_cravado_t'], (len(anim['sprites']) - dv['lava_quadro_golpe']) * anim['timeBetweenFrames'])
        self.assertGreater(dv['lava_ataque_alcance'], dv['ataque_alcance'], 'na lava ataca de mais longe')
        self.assertLessEqual(dv['lava_golpe_dx'], dv['golpe_x_max'])

    def test_explosao_grande_na_furia(self):
        texto = json.dumps(self.chefe)
        self.assertEqual(texto.count('"SetStringObjectVariable"}, "parameters": ["demonio_chefe", "golpe", "=", "\\"grande\\""'), 1)
        inicio = next(e for e in eventos(self.chefe) if any(a['parameters'][:4] == [t63.D, 'golpe', '=', '"grande"']
                                                           for a in e.get('actions', [])))
        self.assertIn('"em_furia", "True"', json.dumps(inicio['conditions']))
        js = ['\n'.join(e['inlineCode']) for e in eventos(self.grupo['events']) if e['type'].endswith('JsCode')]
        self.assertTrue(any('Infinity, 0)' in c for c in js))
        self.assertEqual(sum('quebra_topo_linhas' in c and 'quebra(cx' in c for c in js), 2)
        g = json.dumps(self.grupo)
        self.assertIn('"SetBooleanVariable"}, "parameters": ["fase2", "True"', g)
        self.assertIn('"ActivateBehavior"}, "parameters": ["plataforma_movel", "Platform", "no"]', g)
        self.assertIn('"ActivateBehavior"}, "parameters": ["plataforma_movel", "Platform", "yes"]', g)
        self.assertIn('"Delete"}, "parameters": ["sangue"', g)

    def test_variaveis_existem(self):
        g = json.dumps(self.chefe, ensure_ascii=False)
        for dono in (t63.D, t63.LAVA, t63.DES):
            nomes = set(self.vars(dono))
            for v in re.findall(dono + r'\.([a-z_0-9]+)\b(?!\()', g):
                self.assertIn(v, nomes, f'{dono}.{v}')
        for v in re.findall(r'Variable\(([a-z_0-9]+)\)', g) + re.findall(r'n\("([a-z_0-9]+)"\)', g):
            self.assertIn(v, self.cv)
        js = [e for e in eventos(self.grupo['events']) if e['type'].endswith('JsCode')]
        for e in js:
            c = '\n'.join(e['inlineCode'])
            if 'destroco' in c:
                for v in re.findall(r'num\("([a-z_]+)"\)', c.split('runtimeScene.createObject')[-1].split('};')[0]):
                    self.assertIn(v, self.vars(t63.DES))
        pedacos = [s['image'] for a in self.objs[t63.DES]['animations'] for s in a['directions'][0]['sprites']]
        self.assertEqual(pedacos, t63.IMGS)
        for p in pedacos:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, p)))

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t63.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
