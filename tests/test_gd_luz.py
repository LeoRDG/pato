"""Identificadores das luzes e efeitos do GDevelop usados pelo chefe final (tools/gd_luz.py)."""
import os, sys, unittest
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_luz as g


class GdLuz(unittest.TestCase):
    def test_constantes(self):
        self.assertEqual(g.OBJ_LUZ, 'Lighting::LightObject')
        self.assertEqual(g.COMP_SOMBRA, 'Lighting::LightObstacleBehavior')
        for c in (g.ACAO_RAIO_LUZ, g.ACAO_COR_LUZ, g.ACAO_LUZ_AMBIENTE, g.ACAO_PARAM_EFEITO_CAMADA,
                  g.ACAO_PARAM_EFEITO_OBJ, g.ACAO_MOSTRA_CAMADA, g.ACAO_ESCONDE_CAMADA):
            self.assertIsInstance(c, str)
            self.assertTrue(c)
        self.assertEqual(set(g.CONTEUDO_LUZ), {'radius', 'color', 'texture', 'debugMode'})
        self.assertTrue(g.CAMADA_LUZ['isLightingLayer'])
        self.assertTrue(g.CAMADA_LUZ['followBaseLayerCamera'])
        self.assertEqual(set(g.EFEITOS['Godray']), {'lacunarity', 'angle', 'gain', 'light', 'x', 'y',
                                                    'animationSpeed', 'padding', 'parallel'})

    def test_acoes_montam_parametros(self):
        a = g.acao_luz_ambiente('"Luz"', '"10;10;20"')
        self.assertEqual(a['type']['value'], g.ACAO_LUZ_AMBIENTE)
        self.assertEqual(a['parameters'], ['', '"Luz"', '"10;10;20"'])
        a = g.acao_raio_luz('luz_pato', 'Variable(luz_pato_raio)')
        self.assertEqual(a['parameters'], ['luz_pato', 'Variable(luz_pato_raio)'])
        a = g.acao_param_efeito_camada('""', '"Raios"', '"gain"', 'deus.raios_gain')
        self.assertEqual(a['parameters'], ['', '""', '"Raios"', '"gain"', 'deus.raios_gain'])


if __name__ == '__main__':
    unittest.main()
