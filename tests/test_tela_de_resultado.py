"""Tela de resultado (tools/t203_tela_de_resultado.py): o fim da fase vai para a cena Resultado, que liga só o grupo do placar,
desenha o resultado e os placares (números em fim_tela.*) e volta para o hub da fase."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class TelaDeResultado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.r = m.cena(cls.d, 'Resultado')

    def test_cena_liga_so_o_grupo_do_placar(self):
        link = self.r['events'][0]
        self.assertEqual(link['type'], 'BuiltinCommonInstructions::Link')
        self.assertEqual(link['target'], 'Jogador')
        self.assertEqual(link['include'], {'includeConfig': 1, 'eventsGroup': 'Corrida (placar)'})

    def test_fim_da_fase_vai_para_o_resultado(self):
        entra = json.dumps(m.acha(m.folha(self.d, 'Portais')['events'], 'Entrar no portal'))
        self.assertIn('"Scene"}, "parameters": ["", "\\"Resultado\\""', entra)
        self.assertIn('"resultado_volta", "=", "portal.cena"', entra)
        self.assertIn('"Resultado\\""', json.dumps(m.acha(m.cena(self.d, 'Paraiso')['events'], 'Saída no Empíreo')))

    def test_volta_e_desenho(self):
        volta = json.dumps(m.acha(self.r['events'], 'Voltar para o hub'))
        self.assertIn('GlobalVariableString(resultado_volta)', volta)
        self.assertIn('fim_tela.espera', volta)
        js = m.acha(self.r['events'], 'Tela de resultado')['events'][0]['inlineCode']
        self.assertEqual(js[0], 'try {')
        codigo = '\n'.join(js)
        for k in ('ESTA CORRIDA', 'MAIS RAPIDOS', 'MAIS PONTOS', 'SEU RECORDE', 'ref_w'):
            self.assertIn(k, codigo)
        fim = {c['name'] for v in self.d['variables'] if v['name'] == 'fim_tela' for c in v['children']}
        import re
        for k in set(re.findall(r'n\("([a-z_]+)"\)', codigo)):
            self.assertIn(k, fim)

    def test_envio_marca_o_estado(self):
        g = m.acha(m.folha(self.d, 'Jogador')['events'], 'Corrida (placar)')
        js = '\n'.join('\n'.join(e['inlineCode']) for e in m.todos(g['events']) if e['type'].endswith('JsCode'))
        for estado in ('"enviando"', '"sem_placar"', '"parcial"', '"ok"', '"erro"'):
            self.assertIn(estado, js)


if __name__ == '__main__':
    unittest.main()
