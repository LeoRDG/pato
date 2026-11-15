"""Demônio chefe do inferno (tools/t58_demonio_chefe_sprites.py e tools/t59_demonio_chefe.py)."""
import json, os, re, sys, unittest
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D = 'demonio_chefe'


def instrucoes(evs):
    for e in evs:
        yield from e.get('conditions', [])
        yield from e.get('actions', [])
        yield from instrucoes(e.get('events', []))


class DemonioChefe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.obj = next(o for o in cls.d['objects'] if o['name'] == D)
        cls.vars = {v['name']: v['value'] for v in cls.obj['variables']}
        cls.ext = next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')

    def test_animacoes_e_imagens(self):
        recursos = {r['name'] for r in self.d['resources']['resources']}
        anims = {a['name']: a for a in self.obj['animations']}
        self.assertLessEqual({'idle', 'andando', 'ataque', 'tomou_dano', 'morte'}, set(anims))
        for a in anims.values():
            for s in a['directions'][0]['sprites']:
                self.assertIn(s['image'], recursos)
                self.assertEqual(Image.open(os.path.join(RAIZ, s['image'])).size, (744, 384))
        self.assertEqual(len(anims['ataque']['directions'][0]['sprites']), 15)
        self.assertFalse(anims['ataque']['directions'][0]['looping'])

    def test_grupos_e_ligacao(self):
        grupos = {g['name']: {x['name'] for x in g['objects']} for g in self.d['objectsGroups']}
        for g in ('Inimigo', 'Personagem', 'Terrestre'):
            self.assertIn(D, grupos[g])
        self.assertNotIn(D, grupos.get('CorpoACorpo', set()))
        cena = next(l for l in self.d['layouts'] if l['name'] == 'Inferno')
        alvos = [e['target'] for e in cena['events'] if e['type'].endswith('::Link')]
        self.assertGreater(alvos.index('Chefe'), max(alvos.index('Inimigos'), alvos.index('HUD')))

    def test_variaveis_usadas_existem(self):
        texto = json.dumps(self.ext['events'])
        usadas = set(re.findall(D + r'\.([a-z_]+)\b(?!\()', texto))
        self.assertTrue(usadas)
        self.assertLessEqual(usadas, set(self.vars))
        self.assertTrue(self.vars['tem_barra_de_vida'])
        self.assertTrue(self.vars['sprite_esquerda'])
        self.assertLess(self.vars['golpe_inicio'], self.vars['golpe_fim'])

    def test_golpe_bate_quando_o_cutelo_desce(self):
        tempo = next(a for a in self.obj['animations'] if a['name'] == 'ataque')['directions'][0]['timeBetweenFrames']
        # o cutelo chega ao chão no quadro 9 e é arrastado até o 11
        self.assertAlmostEqual(self.vars['golpe_inicio'], 9 * tempo)
        self.assertAlmostEqual(self.vars['golpe_fim'], 12 * tempo)

    def test_sem_numeros_soltos_nos_eventos(self):
        permitidos = {'0', '1', '2', '30', '360', '0.75', '0.85', '0.8', '0.9'}   # 360: volta inteira; tons de som
        for ins in instrucoes(self.ext['events']):
            for p in ins['parameters']:
                for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w])', p):
                    self.assertIn(n, permitidos | {'30'}, f'{ins["type"]["value"]}: {p}')

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t59.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
