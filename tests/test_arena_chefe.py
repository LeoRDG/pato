"""Sala do demônio chefe fecha quando ele vê o pato (tools/t61_arena_chefe.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t61_arena_chefe as t61


class ArenaChefe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.objs = {o['name']: o for o in cls.d['objects']}
        cls.cena = next(l for l in cls.d['layouts'] if l['name'] == 'Inferno')
        cls.arena = next(e for e in next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')['events']
                         if e.get('name') == 'Arena')

    def test_portao_desenhado(self):
        o = self.objs[t61.W]
        self.assertEqual([s['image'] for a in o['animations'] for s in a['directions'][0]['sprites']], [t61.IMG])
        self.assertEqual(o['behaviors'][0]['platformType'], 'NormalPlatform')
        from PIL import Image
        im = Image.open(os.path.join(RAIZ, t61.IMG))
        p = next(i for i in self.cena['instances'] if i.get('persistentUuid') == t61.uid('entrada'))
        self.assertEqual(im.size, (p['width'], p['height']))                 # sem esticar
        self.assertLess(p['zOrder'], min(i['zOrder'] for i in self.cena['instances'] if i['name'] == 'tiles_inferno'))

    def test_parede_tampa_a_entrada(self):
        """A instância vai do teto ao chão: nos dois extremos há tile sólido, no meio está vazio."""
        p = next(i for i in self.cena['instances'] if i.get('persistentUuid') == t61.uid('entrada'))
        objs = self.objs
        mapas = []
        for i in self.cena['instances']:
            o = objs.get(i['name'])
            if o and o['type'] == 'TileMap::SimpleTileMap' and 'decor' not in i['name']:
                g = json.loads(next(x['value'] for x in i['stringProperties'] if x['name'] == 'tilemap'))
                mapas.append((i, g['layers'][0]['tiles'], {int(x) for x in o['content']['tilesWithHitBox'].split(',') if x}))

        def solido(x, y):
            for i, linhas, hit in mapas:
                c, r = int((x - i['x']) // 64), int((y - i['y']) // 64)
                if 0 <= r < len(linhas) and 0 <= c < len(linhas[0]) and linhas[r][c] in hit:
                    return True
            return False
        for x in (p['x'] + 4, p['x'] + p['width'] / 2, p['x'] + p['width'] - 4):
            self.assertTrue(solido(x, p['y'] + 2), 'o topo da parede não entra no teto')
            self.assertTrue(solido(x, p['y'] + p['height'] - 2), 'o pé da parede não entra no chão')
        pato = next(i for i in self.cena['instances'] if i['name'] == 'pato')
        chefe = next(i for i in self.cena['instances'] if i['name'] == t61.D)
        self.assertLess(pato['x'] + pato['width'], p['x'])          # o pato começa do lado de fora
        self.assertGreater(chefe['x'], p['x'] + p['width'])

    def test_fecha_no_sangue_desce_rapido_e_abre_na_morte(self):
        texto = json.dumps(self.arena)
        self.assertIn('"CollisionNP"}, "parameters": ["pato", "sangue"', texto)
        self.assertIn('"BuiltinCommonInstructions::Or"', texto)
        self.assertIn('"morto", "True"', texto)
        self.assertIn('descida_vel * TimeDelta()', texto)
        self.assertIn('subida_vel * TimeDelta()', texto)
        v = {x['name']: x['value'] for x in self.objs[t61.W]['variables']}
        # o portão fecha mais rápido do que o pato consegue voltar até ele, mesmo fora do sangue
        pato = next(o for o in self.d['objects'] if o['name'] == 'pato')
        maxv = next(b for b in pato['behaviors'] if b['type'].endswith('PlatformerObjectBehavior'))['maxSpeed']
        p = next(i for i in self.cena['instances'] if i.get('persistentUuid') == t61.uid('entrada'))
        self.assertLess((p['height'] - 155) / v['descida_vel'], 60 / maxv * 4)

    def test_variaveis_existem(self):
        texto = json.dumps(self.arena)
        nomes = {v['name'] for v in self.objs[t61.W]['variables']}
        for v in re.findall(t61.W + r'\.([a-z_]+)\b(?!\()', texto):
            self.assertIn(v, nomes)
        cena = {v['name'] for v in self.cena['variables']}
        self.assertLessEqual({'chefe_trancado', 'chefe_aberto', 'chefe_fora'}, cena)
        self.assertNotIn('aparece_tempo', nomes)

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t61.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
