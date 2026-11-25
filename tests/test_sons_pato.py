"""Sons do pato (tools/t191_sons_pato.py): pulo macio sem tom, batida de asas no pulo no ar, pouso proporcional à queda
e um som de moeda por quadro com o tom subindo em sequência. Todos os volumes são variáveis."""
import json, os, sys, unittest, wave
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def sons(evs, nome):
    return [a for e in m.todos(evs) for a in e.get('actions', [])
            if a['type']['value'] == 'PlaySound' and a['parameters'][1] == nome]


class SonsPato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.jog = m.folha(cls.d, 'Jogador')['events']
        cls.com = m.folha(cls.d, 'Combate')['events']

    def test_volumes_em_variaveis(self):
        for nome, var in (('som_pulo.wav', 'pato.pulo_som_volume'), ('som_pulo_ar.wav', 'pato.pulo_ar_som_volume')):
            acs = sons(self.jog, nome)
            self.assertTrue(acs)
            for a in acs:
                self.assertEqual(a['parameters'][3], var)
        self.assertTrue(all(a['parameters'][3].startswith('pato.pouso_som_min') for a in sons(self.jog, 'som_pouso.wav')))
        pv = {v['name'] for v in m.objeto(self.d, 'pato')['variables']}
        self.assertLessEqual({'pulo_som_volume', 'pulo_som_variacao', 'pulo_ar_som_volume', 'pouso_som_min', 'pouso_som_extra'}, pv)

    def test_pulo_curto_e_sem_tom(self):
        with wave.open(os.path.join(RAIZ, 'assets', 'som_pulo.wav')) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float)
            dur = w.getnframes() / w.getframerate()
        self.assertLess(dur, 0.25)
        sp = np.abs(np.fft.rfft(x))
        self.assertLess(sp.max() / sp.mean(), 60)   # ruído (roupa), não um apito: nenhum pico domina o espectro

    def test_moeda_um_som_por_quadro(self):
        coleta = m.acha(self.com, 'Coleta')
        laco = coleta['events'][0]
        self.assertFalse([a for a in laco['actions'] if a['type']['value'] == 'PlaySound'])
        s = sons(coleta['events'], 'som_moeda.wav')
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]['parameters'][3], 'moeda_som_volume')
        self.assertIn('moeda_combo', s[0]['parameters'][4])


if __name__ == '__main__':
    unittest.main()
