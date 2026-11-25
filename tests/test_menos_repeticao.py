"""Eventos repetidos juntados em grupos de objetos e marcas (tools/t136_menos_repeticao.py)."""
import json, os, re, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class MenosRepeticao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.obj = {o['name']: o for o in cls.d['objects']}
        cls.grupos = {g['name']: [o['name'] for o in g['objects']] for g in cls.d['objectsGroups']}
        cls.txt = json.dumps([x['events'] for x in cls.d['externalEvents']] +
                             [l['events'] for l in cls.d['layouts']], ensure_ascii=False)

    def vars(self, n):
        return {v['name'] for v in self.obj[n]['variables']}

    def test_todo_objeto_do_grupo_tem_o_que_o_grupo_usa(self):
        for g in ('Perseguidores', 'Investida', 'Anjos', 'Explosivos', 'Arma', 'Chefes'):
            usadas = set(re.findall(r'\["' + g + r'", "([a-z_]+)"', self.txt)) | \
                set(re.findall(r'\b' + g + r'\.([a-z_]+)\b(?!\()', self.txt))
            usadas -= {'PlatformerObject', 'FireBullet', 'Animation', 'Scale'} | set(self.obj)
            self.assertTrue(usadas, g)
            for o in self.grupos[g]:
                self.assertLessEqual(usadas, self.vars(o), (g, o))

    def test_grupos_novos(self):
        self.assertEqual(set(self.grupos['Perseguidores']), {'condenado_azul', 'condenado_inchado', 'pigman'})
        self.assertEqual(set(self.grupos['Investida']), {'condenado_azul', 'pigman', 'roda_anjo'})
        self.assertEqual(set(self.grupos['Explosivos']), {'condenado_inchado', 'mina_demoniaca'})
        for o in set(self.grupos['Perseguidores']) | set(self.grupos['Investida']):
            self.assertTrue(any(b['name'] == 'PlatformerObject' for b in self.obj[o]['behaviors']), o)

    def test_sem_copias(self):
        t = self.txt
        self.assertEqual(t.count('\\"onda_abissal\\"'), 2)                         # uma onda para cada lado
        self.assertEqual(t.count('"cutulu.anel_qtd"'), 1)
        self.assertEqual(t.count('"TileMap::TileMapBehavior::RemoveTileAtGridCoordinates"'), 1)
        self.assertEqual(t.count('["", "flash_cano"'), 1)
        self.assertEqual(t.count('["", "anjo_morte_luz"'), 1)
        self.assertEqual(t.count('.explosao_raio", ""]'), 1)
        for o in self.grupos['Perseguidores']:
            self.assertNotIn(f'"abs(pato.CenterX() - {o}.CenterX())", ">", "{o}.parar_dist"', t, o)
        evs = [e for x in self.d['externalEvents'] for e in todos(x['events'])]
        for o in self.grupos['Investida']:
            atacar = [e for e in evs if any(c['parameters'] == [o, 'estado', '=', '"atacar"'] for c in e.get('conditions', []))]
            self.assertTrue(atacar, o)
            for e in atacar:
                self.assertNotIn('SimulateLeftKey', json.dumps(e.get('events') or []), o)

    def test_marcas_sao_feitas_e_consumidas(self):
        for dono, marca in (('cutulu', 'ondas_soltar'), ('cutulu', 'anel_soltar'), ('demonio_chefe', 'quebra_pedida'),
                            ('condenado_inchado', 'explodir'), ('mina_demoniaca', 'explodir')):
            self.assertIn(marca, self.vars(dono))
        for marca, quem in (('ondas_soltar', 'cutulu'), ('anel_soltar', 'cutulu'), ('quebra_pedida', 'demonio_chefe'),
                            ('explodir', 'Explosivos')):
            self.assertIn(f'"{quem}", "{marca}", "False"', self.txt)
        self.assertEqual(self.txt.count('"cutulu", "ondas_soltar", "True", ""]'), 3)  # mergulho, fim do ataque, teste
        self.assertEqual(self.txt.count('"cutulu", "anel_soltar", "True", ""]'), 3)

    def test_hubs(self):
        hubs = next(x for x in self.d['externalEvents'] if x['name'] == 'Hubs')
        self.assertEqual([e['name'] for e in hubs['events']], ['Queda da borda', 'Armas no hub', 'Atributos', 'Nome do jogador'])   # t186, t190, t204
        for l in self.d['layouts']:
            if l['name'].startswith('Hub'):
                alvos = [e.get('target') for e in l['events']]
                self.assertIn('Hubs', alvos, l['name'])
                self.assertNotIn('Queda da borda', [e.get('name') for e in l['events']])
                self.assertLessEqual({'queda_y', 'volta_x', 'volta_y'}, {v['name'] for v in l['variables']})


if __name__ == '__main__':
    unittest.main()
