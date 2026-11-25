"""Giro do pulo só no desenho (tools/t193_giro_sem_escalar.py): a máscara girada entrava na parede e a plataforma devolvia o
pulo ao separar o pato dela (escalada infinita). Depois de desenhar, o pato volta a ângulo 0 enquanto o tween giroPulo existe."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class GiroSemEscalar(unittest.TestCase):
    def test_giro_volta_a_zero_depois_de_desenhar(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        g = m.acha(m.folha(d, 'Jogador')['events'], 'Giro do pulo so no desenho')
        cod = '\n'.join(g['events'][0]['inlineCode'])
        self.assertIn('cena.render = function', cod)
        self.assertIn('tw.exists("giroPulo")) p.setAngle(0)', cod)

    def test_tween_depois_da_plataforma(self):
        # o tween tem que andar depois da plataforma, para ela andar com a máscara reta
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        nomes = [b['name'] for b in m.objeto(d, 'pato')['behaviors']]
        self.assertLess(nomes.index('PlatformerObject'), nomes.index('Tween'))


if __name__ == '__main__':
    unittest.main()
