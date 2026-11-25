"""Salvar progresso (tools/t202_salvar_progresso.py): o Menu carrega o save antes do primeiro hub e vai para o último hub;
o Jogador salva ao começar cada cena, de tempo em tempo e ao esconder/fechar a aba; tudo dentro de try/catch."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

CHAVES = ('moedas_total', 'upgrades', 'armas', 'waypoints', 'corrida', 'corridas', 'ultimo_hub')


class SalvarProgresso(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_menu_carrega_antes_de_ir_para_o_ultimo_hub(self):
        menu = m.cena(self.d, 'Menu')['events']
        carrega = m.acha(menu, 'Carregar progresso')
        self.assertIs(menu[0], carrega)
        codigo = '\n'.join(carrega['events'][0]['inlineCode'])
        for k in CHAVES:
            self.assertIn(f'"{k}"', codigo)
        self.assertIn('hasScene', codigo)
        self.assertIn('GlobalVariableString(ultimo_hub)', json.dumps(m.acha(menu, 'Ir para o Hub')))

    def test_jogador_salva(self):
        g = m.acha(m.folha(self.d, 'Jogador')['events'], 'Salvar progresso')
        codigo = '\n'.join(g['events'][0]['inlineCode'])
        for trecho in ('pagehide', 'visibilitychange', 'save_intervalo', 'localStorage.setItem("pato_save"'):
            self.assertIn(trecho, codigo)
        for k in CHAVES:
            self.assertIn(f'"{k}"', codigo)

    def test_nunca_trava_o_jogo(self):
        for e in (m.acha(m.cena(self.d, 'Menu')['events'], 'Carregar progresso')['events'][0],
                  m.acha(m.folha(self.d, 'Jogador')['events'], 'Salvar progresso')['events'][0]):
            self.assertEqual(e['inlineCode'][0], 'try {')
            self.assertTrue(e['inlineCode'][-1].startswith('} catch (e)'))


if __name__ == '__main__':
    unittest.main()
