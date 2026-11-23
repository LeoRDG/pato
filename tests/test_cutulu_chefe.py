"""Cutulu como chefe de três fases (tools/t124_cutulu_chefe.py)."""
import json, os, re, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from folhas import folha

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class CutuluChefe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(JOGO, encoding='utf-8'))
        cls.obj = {o['name']: o for o in cls.d['objects']}
        cls.folha = {'events': folha(cls.d, 'Cutulu')}
        cls.txt = json.dumps(cls.folha['events'], ensure_ascii=False)

    def test_ligada_depois_do_hud(self):
        for nome in ('Purgatorio', 'Teste'):
            alvos = [e.get('target') for e in next(l for l in self.d['layouts'] if l['name'] == nome)['events']]
            self.assertIn('InimigosPurgatorio', alvos, nome)
            self.assertLess(alvos.index('Inimigos'), alvos.index('InimigosPurgatorio'))
            self.assertLess(alvos.index('InimigosPurgatorio'), alvos.index('HUD'))

    def test_variaveis_usadas_existem(self):
        for o in ('cutulu', 'moscas', 'pato', 'projetil_inimigo'):
            usadas = set(re.findall(o + r'\.([a-z_]+)\b(?!\()', self.txt)) - {'wav'}
            tem = {v['name'] for v in self.obj[o]['variables']}
            self.assertFalse(usadas - tem, o)

    def test_cada_ataque_tem_estado(self):
        for est in ('rugido', 'mergulho', 'espiral', 'chuva', 'invocar'):
            self.assertIn(f'\\"{est}\\"', self.txt)
        self.assertGreaterEqual(self.txt.count('"PlatformerObject", "yes"'), 3)
        self.assertNotIn('demonio_chefe', self.txt)

    def test_sombra_em_laco(self):
        s = self.obj['cutulu_sombra']
        self.assertEqual([a['name'] for a in s['animations']], ['segue', 'trava'])
        for a in s['animations']:
            d = a['directions'][0]
            self.assertTrue(d['looping'])
            for sp in d['sprites']:
                self.assertTrue(os.path.exists(os.path.join(RAIZ, sp['image'])), sp['image'])
        quadros = [sp['image'] for sp in s['animations'][0]['directions'][0]['sprites']]
        self.assertEqual(quadros[-1], quadros[1])       # 1 2 3 2: o último leva de volta ao primeiro

    def test_um_create_de_projetil_por_evento(self):
        # dois Create na mesma lista somam a seleção: as ações do segundo iriam também para o primeiro
        for e in todos(self.folha['events']):
            n = sum(a['type']['value'] == 'Create' and a['parameters'][1] == 'projetil_inimigo'
                    for a in e.get('actions', []))
            self.assertLessEqual(n, 1)

    def test_golpes_acertam(self):
        for g in ('rasgo', 'chicote'):
            self.assertIn(f'\\"{g}\\"', self.txt)
            self.assertIn(f'cutulu.{g}_dano', self.txt)

    def test_tiro_nao_trava(self):
        # firme volta a True no fim do quadro (o grupo Postura é o último da folha)
        ult = self.folha['events'][-1]
        self.assertEqual(ult.get('name'), 'Postura')
        self.assertIn('"firme", "True"', json.dumps(ult))
        self.assertIn('cutulu.postura_frac', json.dumps(ult))
        self.assertIn('cutulu.postura_imune', json.dumps(ult))
        # ao cambalear (estado "dano") firme volta a True na hora: tiros não renovam o cambaleio
        dano = next(e for e in ult['events'] if any(c['parameters'][1:] == ['estado', '=', '"dano"']
                                                    for c in e.get('conditions', [])))
        self.assertIn('"firme", "True"', json.dumps(dano['actions']))


if __name__ == '__main__':
    unittest.main()
