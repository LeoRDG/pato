"""Nome do jogador no hub (tools/t204_nome_no_hub.py): N abre o painel, Enter salva, Esc cancela; as teclas não chegam ao jogo."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class NomeNoHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        g = m.acha(m.folha(cls.d, 'Hubs')['events'], 'Nome do jogador')
        cls.js = g['events'][0]['inlineCode']
        cls.codigo = '\n'.join(cls.js)

    def test_nunca_trava_o_jogo(self):
        self.assertEqual(self.js[0], 'try {')
        self.assertTrue(self.js[-1].startswith('} catch (e)'))

    def test_teclas_nao_chegam_ao_jogo_e_pato_parado(self):
        for trecho in ('stopImmediatePropagation', '"keyup"', 'na_loja', 'clearAllPressedKeys', 'jogador_nome', '__save'):
            self.assertIn(trecho, self.codigo)

    def test_numeros_em_variaveis(self):
        tela = {c['name'] for v in self.d['variables'] if v['name'] == 'nome_tela' for c in v['children']}
        for k in set(re.findall(r'n\("([a-z_]+)"\)', self.codigo)) | {'tecla', 'max'}:
            self.assertIn(k, tela)
        nome_max = re.search(r'nome_max: (\d+)', open(os.path.join(RAIZ, 'servidor', 'src', 'regras.js')).read()).group(1)
        self.assertLessEqual(next(c['value'] for v in self.d['variables'] if v['name'] == 'nome_tela'
                                  for c in v['children'] if c['name'] == 'max'), int(nome_max))

    def test_objetos_proprios(self):
        nomes = {o['name'] for o in self.d['objects']}
        self.assertIn('nome_txt', nomes)
        self.assertIn('nome_painel', nomes)
        self.assertNotIn('"ui_txt"', self.codigo)


if __name__ == '__main__':
    unittest.main()


def test_nome_no_celular():
    """t221: no celular a dica é para tocar e abre o teclado do aparelho (campo de texto invisível)."""
    import json as _json
    jogo = _json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'),
                           encoding='utf-8'))
    hubs = next(x for x in jogo['externalEvents'] if x['name'] == 'Hubs')
    g = next(e for e in hubs['events'] if e.get('name') == 'Nome do jogador')
    codigo = '\n'.join(next(e for e in g['events'] if e['type'].endswith('JsCode'))['inlineCode'])
    for trecho in ('"touchend"', 'createElement("input")', 'c.focus()', 'TOQUE AQUI PARA ESCOLHER SEU NOME',
                   'N.dicaRet', 'N.painelRet', '"y_celular"', 'tam_dica_celular', 'ev.target === N.campo'):
        assert trecho in codigo, trecho
    t = {c['name'] for v in jogo['variables'] if v['name'] == 'nome_tela' for c in v['children']}
    assert {'toque_folga', 'y_celular', 'tam_dica_celular'} <= t
