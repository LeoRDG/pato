"""Sessão de placar por fase (tools/t201_sessao_por_fase.py): o tempo pausa fora da fase, cada fase guarda a própria sessão
pausada em corridas[fase] e o relógio do HUD mostra o tempo da sessão."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class SessaoPorFase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.g = {v['name']: v for v in cls.d['variables']}

    def test_tempo_pausa_no_hub(self):
        placar = {c['name']: c['value'] for c in self.g['placar']['children']}
        self.assertIs(placar['tempo_no_hub'], False)

    def test_cada_fase_guarda_a_sua_sessao(self):
        self.assertEqual({c['name'] for c in self.g['corridas']['children']}, {'Inferno', 'Purgatorio', 'Paraiso'})
        g = m.acha(m.folha(self.d, 'Jogador')['events'], 'Corrida (placar)')
        comeca = next(e for e in g['events'] if any(a['parameters'][:2] == ['corrida.nova', 'True'] for a in e.get('actions', [])))
        troca = comeca['events'][0]
        self.assertEqual(troca['type'], 'BuiltinCommonInstructions::JsCode')   # antes de decidir se a corrida é nova
        self.assertEqual(troca['inlineCode'][0], 'try {')
        self.assertIn('corridas', '\n'.join(troca['inlineCode']))

    def test_hud_mostra_o_tempo_da_sessao(self):
        hud = json.dumps(m.folha(self.d, 'HUD')['events'])
        self.assertIn('GlobalVariable(tempo_hud)', hud)
        self.assertIn('GlobalVariable(corrida.tempo)', hud)


if __name__ == '__main__':
    unittest.main()
