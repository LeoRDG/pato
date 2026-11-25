"""Placar global (tools/t200_placar_token.py + servidor/): o jogo pede o token no começo da corrida e o manda no fim; os testes
do worker (node --test, D1 falso com node:sqlite) rodam aqui também se houver Node."""
import json, os, shutil, subprocess, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class PlacarToken(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_jogo_pede_e_manda_o_token(self):
        g = m.acha(m.folha(self.d, 'Jogador')['events'], 'Corrida (placar)')
        js = '\n'.join('\n'.join(e['inlineCode']) for e in m.todos(g['events']) if e['type'].endswith('JsCode'))
        self.assertIn('url + "/comecar"', js)
        self.assertIn('token: V.get("corrida").getChild("token")', js)
        self.assertIn('global_pos_tempo', js)

    def test_placar_nunca_trava_o_jogo(self):
        # todo evento JS do placar fica dentro de try/catch e as requisições têm limite de tempo
        g = m.acha(m.folha(self.d, 'Jogador')['events'], 'Corrida (placar)')
        js = [e['inlineCode'] for e in m.todos(g['events']) if e['type'].endswith('JsCode')]
        self.assertEqual(len(js), 4)
        for linhas in js:
            self.assertEqual(linhas[0], 'try {')
            self.assertTrue(linhas[-1].startswith('} catch (e)'))
            if any('fetch(' in l for l in linhas):
                self.assertTrue(any('AbortSignal.timeout' in l for l in linhas))
                self.assertTrue(any('.catch(() => {})' in l for l in linhas))

    def test_formula_do_servidor_igual_a_do_jogo(self):
        placar = {c['name']: c['value'] for v in self.d['variables'] if v['name'] == 'placar' for c in v['children']}
        regras = open(os.path.join(RAIZ, 'servidor', 'src', 'regras.js'), encoding='utf-8').read()
        for k in ('pts_conclusao', 'pts_segundo', 'pts_dano', 'pts_morte', 'pts_ida_hub'):
            self.assertIn(f'{k}: {placar[k]:g},', regras, k)
        niveis = {c['name']: c['children'][0]['value'] for v in self.d['variables'] if v['name'] == 'placar_niveis' for c in v['children']}
        for n, t in niveis.items():
            self.assertIn(f'{n}: {{ tempo_ref: {t:g},', regras, n)

    @unittest.skipUnless(shutil.which('node'), 'sem node')
    def test_worker(self):
        r = subprocess.run(['node', '--test', 'test/'], cwd=os.path.join(RAIZ, 'servidor'), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])


if __name__ == '__main__':
    unittest.main()
