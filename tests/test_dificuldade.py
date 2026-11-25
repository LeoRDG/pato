"""Dificuldade (tools/t196_dificuldade.py): dano recebido escalado por dificuldade_dano (pelo vida_ref, antes da conferência de
morte e do número de dano), mortes de propósito sem escala, empurrão ao encostar num inimigo e invencibilidade maior."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class Dificuldade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_escala_antes_da_morte_e_do_numero(self):
        for folha, grupo in (('Jogador', 'Morte do Pato'), ('Combate', 'Sons de dano')):
            primeiro = m.acha(m.folha(self.d, folha)['events'], grupo)['events'][0]
            self.assertIn('dificuldade_dano', json.dumps(primeiro), folha)
        g = {v['name']: v.get('value') for v in self.d['variables']}
        self.assertLess(g['dificuldade_dano'], 1)

    def test_mortes_de_proposito_nao_escaladas(self):
        for x in self.d['externalEvents']:
            for e in m.todos(x['events']):
                acs = e.get('actions', [])
                for k, a in enumerate(acs):
                    if a['type']['value'] == 'SetNumberObjectVariable' and a['parameters'][:3] == ['pato', 'vida', '='] \
                            and a['parameters'][3] in ('0', '-10'):
                        self.assertEqual(acs[k + 1]['parameters'][:2], ['pato', 'vida_ref'])

    def test_empurrao_no_toque(self):
        com = m.folha(self.d, 'Combate')['events']
        t = json.dumps(m.acha(com, 'Dano e invencibilidade')['events'][0]['actions'])
        self.assertIn('pato.dano_empurrao_x', t)


if __name__ == '__main__':
    unittest.main()
