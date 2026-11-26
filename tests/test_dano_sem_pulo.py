"""O pato não pula sozinho ao levar dano (tools/t65_dano_sem_pulo.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t65_dano_sem_pulo as t65


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class DanoSemPulo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.eventos = [e for evs in t65.folhas(cls.d) for e in todos(evs)]

    def test_dano_nao_faz_pular(self):
        for e in self.eventos:
            acts = e.get('actions') or []
            if t65.tira_dano(acts) and not t65.pulo_da_lava(acts):
                self.assertFalse(any(t65.pulo(a) for a in acts), json.dumps(e.get('conditions'), ensure_ascii=False)[:200])

    def test_dano_continua(self):
        com_dano = [e for e in self.eventos if t65.tira_dano(e.get('actions') or [])]
        self.assertGreaterEqual(len(com_dano), 8)
        for e in com_dano:
            nomes = [a['type']['value'] for a in e['actions']]
            self.assertIn('ResetObjectTimer', nomes)                         # iframes continuam

    def test_pulo_do_jogador_e_da_lava_ficam(self):
        pulos = [e for e in self.eventos if any(t65.pulo(a) for a in e.get('actions') or [])]
        # a tecla pode estar dentro de um "ou" com o toque (t215)
        conds = lambda e: [s for c in e.get('conditions') or [] for s in [c] + (c.get('subInstructions') or [])]
        self.assertTrue(any(any(c['parameters'][1:2] == ['"Space"'] for c in conds(e)) for e in pulos))
        self.assertTrue(any(t65.pulo_da_lava(e['actions']) for e in pulos))

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t65.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
