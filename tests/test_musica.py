"""Música (tools/t209_musica.py, faixas de tools/gera_musica.py): recursos e arquivos das faixas, variáveis, a faixa
de cada cena, a folha Musica ligada nas cenas e a troca para a música de chefe com as condições da barra de chefe."""
import json, os, struct, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

CENAS = {'Hub': 'musica_hub_inferno', 'HubPurgatorio': 'musica_hub_purgatorio',
         'HubParaiso': 'musica_hub_paraiso', 'Inferno': 'musica_inferno', 'Purgatorio': 'musica_purgatorio',
         'Paraiso': 'musica_paraiso', 'Resultado': 'musica_resultado'}
FASES = ('Inferno', 'Purgatorio', 'Paraiso')


def vars_cena(d, nome):
    return {v['name']: v for v in m.cena(d, nome)['variables']}


def amostras_ogg(caminho):
    """número de amostras pela granule position da última página Ogg"""
    dados = open(caminho, 'rb').read()
    i = dados.rfind(b'OggS')
    return struct.unpack('<q', dados[i + 6:i + 14])[0]


class Musica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.rec = {r['name']: r for r in cls.d['resources']['resources']}

    def test_recursos_e_arquivos(self):
        nomes = set(CENAS.values()) | {f'musica_{f.lower()}_chefe' for f in FASES}
        for n in nomes:
            r = self.rec.get(n)
            self.assertIsNotNone(r, n)
            self.assertEqual(r['kind'], 'audio')
            self.assertTrue(r['file'].startswith('assets/musica/') and r['file'].endswith('.ogg'), r['file'])
            caminho = os.path.join(RAIZ, r['file'])
            self.assertTrue(os.path.exists(caminho), caminho)
            self.assertLess(os.path.getsize(caminho), 1_500_000, caminho)
            self.assertFalse(r['preloadAsMusic'] or r['preloadAsSound'], n)   # carrega só na cena que usa

    def test_faixa_de_chefe_do_mesmo_tamanho(self):
        for f in FASES:
            base = os.path.join(RAIZ, self.rec[f'musica_{f.lower()}']['file'])
            chefe = os.path.join(RAIZ, self.rec[f'musica_{f.lower()}_chefe']['file'])
            self.assertEqual(amostras_ogg(base), amostras_ogg(chefe), f)
            self.assertGreater(amostras_ogg(base) / 44100, 45)

    def test_variaveis_globais(self):
        g = next(v for v in self.d['variables'] if v['name'] == 'musica')
        filhos = {c['name']: c for c in g['children']}
        for k in ('volume', 'ligada', 'fade', 'fade_chefe', 'fade_volta', 'espera_chefe', 'volume_chefe'):
            self.assertIn(k, filhos)
        codigo = '\n'.join(self.js())
        for k in filhos:
            self.assertTrue(f'n("{k}")' in codigo or f'getChild("{k}")' in codigo, k)

    def test_cada_cena_tem_sua_faixa(self):
        for cena, faixa in CENAS.items():
            v = vars_cena(self.d, cena)
            self.assertEqual(v['musica']['type'], 'string', cena)
            self.assertIn(v['musica']['value'], self.rec, cena)
            self.assertIn('musica_volume', v)
            self.assertIn('musica_chefe_ativo', v)
            links = [e for e in m.cena(self.d, cena)['events'] if e['type'] == 'BuiltinCommonInstructions::Link'
                     and e.get('target') == 'Musica']
            self.assertEqual(len(links), 1, cena)
        for f in FASES:
            self.assertIn(vars_cena(self.d, f)['musica_chefe']['value'], self.rec, f)

    def js(self):
        return m.acha(m.folha(self.d, 'Musica')['events'], 'Música')['events'][2]['inlineCode']

    def test_troca_para_chefe_com_as_condicoes_da_barra(self):
        evs = m.acha(m.folha(self.d, 'Musica')['events'], 'Música')['events']
        self.assertEqual(evs[0]['actions'][0]['parameters'][:2], ['musica_chefe_ativo', 'False'])
        barra = m.acha(m.acha(m.folha(self.d, 'HUD')['events'], 'Barras de chefe')['events'], 'Chefes')['events'][0]
        self.assertEqual(evs[1]['conditions'], barra['conditions'])
        self.assertEqual(evs[1]['actions'][0]['parameters'][:2], ['musica_chefe_ativo', 'True'])
        codigo = '\n'.join(self.js())
        self.assertEqual(self.js()[0], 'try {')
        for t in ('musica_chefe_ativo', 'musica_chefe', 'src.loop = true', 'setTargetAtTime', 'M.toca(f, M.base)',
                  'ctx.resume', 'M.base.nome !== nomeBase'):
            self.assertIn(t, codigo)

    def test_gerador_existe(self):
        self.assertTrue(os.path.exists(os.path.join(RAIZ, 'tools', 'gera_musica.py')))


if __name__ == '__main__':
    unittest.main()
