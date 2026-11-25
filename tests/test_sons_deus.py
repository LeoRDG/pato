"""Sons do chefe final (tools/t192_sons_deus.py): Deus não usa mais som_luz/som_dash; cada golpe tem som próprio, o pulso
tem um zumbido em laço que sobe com a carga e para no disparo, e fase, morte e dano na pupila têm som."""
import json, os, sys, unittest, wave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def acoes(evs, tipo):
    return [a for e in m.todos(evs) for a in e.get('actions', []) if a['type']['value'] == tipo]


class SonsDeus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')

    def test_sem_som_de_anjo(self):
        sons = {a['parameters'][1] for a in acoes(self.deus['events'], 'PlaySound')}
        self.assertFalse(sons & {'som_luz.wav', 'som_dash.wav'})
        self.assertGreaterEqual(len({s for s in sons if s.startswith('som_deus_')}), 14)
        res = {r['name'] for r in self.d['resources']['resources'] if r['kind'] == 'audio'}
        for s in sons:
            self.assertIn(s, res)
            with wave.open(os.path.join(RAIZ, 'assets', s)) as w:
                self.assertEqual(w.getframerate(), 44100)

    def test_momentos_sem_som_agora_tem(self):
        for grupo, som in (('Fases', 'som_deus_fase.wav'), ('Morte', 'som_deus_morte.wav'), ('Dano na pupila', 'som_deus_dano.wav')):
            g = m.acha(self.deus['events'], grupo)
            self.assertIn(som, [a['parameters'][1] for a in acoes(g['events'], 'PlaySound')], grupo)

    def test_zumbido_do_pulso(self):
        p = m.acha(self.deus['events'], 'Anel de ouro: o pulso')
        liga = acoes(p['events'], 'PlaySoundOnChannel')
        self.assertEqual([a['parameters'][1] for a in liga], ['som_deus_zumbido.wav'])
        self.assertEqual(liga[0]['parameters'][3], 'yes')
        self.assertTrue(acoes(p['events'], 'SetSoundChannelVolume'))
        for g in ('Anel de ouro: o pulso', 'Fases', 'Morte'):
            self.assertTrue(acoes(m.acha(self.deus['events'], g)['events'], 'StopSoundCanal'), g)


if __name__ == '__main__':
    unittest.main()
