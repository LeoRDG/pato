"""Base do placar (tools/t199_placar.py): corrida por fase com tempo, abates, dano, mortes e idas ao hub; pontos por fórmula
em variáveis; fim no portal final e na saída do Empíreo; recordes locais e envio opcional para o placar global."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class Placar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.g = {v['name']: v for v in cls.d['variables']}

    def test_variaveis(self):
        placar = {c['name'] for c in self.g['placar']['children']}
        for k in ('pts_abate', 'pts_vida_inimigo', 'pts_conclusao', 'pts_segundo', 'pts_dano', 'pts_morte', 'pts_ida_hub', 'tempo_no_hub'):
            self.assertIn(k, placar)
        for fase in ('Inferno', 'Purgatorio', 'Paraiso'):
            self.assertIn(fase, {c['name'] for c in self.g['placar_niveis']['children']})
            self.assertIn(fase, {c['name'] for c in self.g['recordes']['children']})
        self.assertIn('placar_url', self.g)

    def test_corrida_no_jogador(self):
        g = json.dumps(m.acha(m.folha(self.d, 'Jogador')['events'], 'Corrida (placar)'))
        self.assertIn('waypoints[CurrentSceneName()].ativo', g)   # começar pelo ponto de volta não vale
        self.assertIn('localStorage', g)
        self.assertIn('placar_url', g)
        self.assertIn('corrida.mortes', json.dumps(m.acha(m.folha(self.d, 'Jogador')['events'], 'Morte do Pato')))

    def test_dano_e_abates(self):
        todos_ev = json.dumps([x['events'] for x in self.d['externalEvents']])
        self.assertEqual(todos_ev.count('"corrida.dano", "+"'), 2)   # nos dois eventos que escalam o dano (t196)
        self.assertIn('corrida.abates', json.dumps(m.acha(m.folha(self.d, 'Combate')['events'], 'Morte do Inimigo')))

    def test_fim_e_idas_ao_hub(self):
        entra = json.dumps(m.acha(m.folha(self.d, 'Portais')['events'], 'Entrar no portal'))
        self.assertIn('corrida.concluir', entra)
        self.assertIn('corrida.idas_hub', entra)
        self.assertIn('corrida.concluir', json.dumps(m.acha(m.cena(self.d, 'Paraiso')['events'], 'Saída no Empíreo')))


if __name__ == '__main__':
    unittest.main()
