"""Eventos do Chefe só com eventos e ações do GDevelop, sem JavaScript (tools/t71_chefe_sem_js.py)."""
import json, os, re, sys, unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from folhas import folha, inimigos_todos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t71_chefe_sem_js as t71


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class ChefeSemJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.chefe = folha(cls.d, 'Chefe')
        cls.objs = {o['name']: o for o in cls.d['objects']}

    def test_sem_js(self):
        self.assertEqual([e for e in todos(self.chefe) if e['type'].endswith('JsCode')], [])

    def test_tile_map_pelas_acoes_dele(self):
        texto = json.dumps(self.chefe)
        tm = next(o for o in self.objs.values() if o['name'] == t71.TM)
        self.assertEqual(tm['type'], 'TileMap::SimpleTileMap')
        for expr in ('GridX', 'GridY', 'TileIdAtGrid', 'TileCenterX', 'TileCenterY'):
            self.assertIn(f'tiles_inferno.TileMap::{expr}(', texto)

    def test_variaveis_existem(self):
        texto = json.dumps(self.chefe, ensure_ascii=False)
        for dono in (t71.D, t71.DES, t71.M, t71.F):
            nomes = {v['name'] for v in self.objs[dono]['variables']}
            for v in re.findall(dono + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(v, nomes, f'{dono}.{v}')
        self.assertEqual(self.objs[t71.DES]['variables'][[v['name'] for v in self.objs[t71.DES]['variables']].index('pedacos')]['value'],
                         len(self.objs[t71.DES]['animations']))

    @unittest.skip('eventos reorganizados em tools/t131_organizar_eventos.py; a migração antiga não roda mais')
    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t71.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
