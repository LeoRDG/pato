"""Barra de vida dos chefes no HUD sobre o grupo de objetos Chefes (tools/t135_barra_dos_chefes.py)."""
import json, os, re, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def acha(evs, nome):
    for e in evs:
        if e.get('name') == nome:
            return e
        r = acha(e.get('events') or [], nome)
        if r:
            return r
    return None


class BarraChefes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        hud = next(x for x in cls.d['externalEvents'] if x['name'] == 'HUD')
        cls.barras = acha(hud['events'], 'Barras de chefe')

    def test_um_subgrupo_para_os_chefes(self):
        self.assertEqual([g['name'] for g in self.barras['events']], ['Chefes'])   # o mercador não é mais inimigo (t207)
        txt = json.dumps(self.barras['events'][0])
        self.assertNotIn('demonio_chefe', txt)
        self.assertNotIn('cutulu', txt)

    def test_todo_chefe_tem_as_variaveis_da_barra(self):
        grupo = next(g for g in self.d['objectsGroups'] if g['name'] == 'Chefes')
        nomes = [o['name'] for o in grupo['objects']]
        self.assertLessEqual({'demonio_chefe', 'cutulu'}, set(nomes))
        usadas = set(re.findall(r'Chefes\.([a-z_]+)\b(?!\()', json.dumps(self.barras['events'][0]))) | {'morto'}
        objs = {o['name']: o for o in self.d['objects']}
        for n in nomes:
            self.assertLessEqual(usadas, {v['name'] for v in objs[n]['variables']}, n)


if __name__ == '__main__':
    unittest.main()
