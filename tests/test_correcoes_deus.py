"""Correções da revisão final do chefe Deus (tools/t145_correcoes_deus.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class CorrecoesDeus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.nomes = [e.get('name') for e in cls.deus['events']]

    def ev(self, nome):
        return m.acha(self.deus['events'], nome)

    def test_morte_termina_sem_a_pupila(self):
        """Combate apaga a pupila 1 s depois de morrer; a limpeza das partes não pode depender dela."""
        morte = self.ev('Morte')
        inicio = next(e for e in morte['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
        self.assertIn('"ResetObjectTimer"}, "parameters": ["deus_olho", "\\"morte_deus\\""]', tx(inicio['actions']))
        (fim,) = [e for e in morte['events'] if '"deus_olho.morte_tempo"' in tx(e['conditions'])]
        c = tx(fim['conditions'])
        self.assertIn('"CompareObjectTimer"}, "parameters": ["deus_olho", "\\"morte_deus\\""', c)
        self.assertNotIn('["deus", ', c, 'sem condição sobre a pupila, que já sumiu')
        for p in ('deus_aura', 'deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa', 'deus_olho', 'deus_escudo'):
            self.assertIn(f'"Delete"}}, "parameters": ["{p}"', tx(fim['actions']))
        self.assertIn('morte_tempo', {v['name'] for v in self.o['deus_olho']['variables']})

    def test_corpo_so_com_a_pupila(self):
        corpo = self.ev('Corpo')
        poe = next(e for e in corpo['events'] if '"SetXY"}, "parameters": ["deus_olho"' in tx(e['actions']))
        self.assertIn('"SceneInstancesCount"}, "parameters": ["", "deus", ">", "0"]', tx(poe['conditions']))

    def test_troca_de_fase_limpa_o_golpe(self):
        fases = self.ev('Fases')
        troca = next(e for e in fases['events'] if '"deus", "estado", "=", "\\"fase\\""' in tx(e['actions']))
        a = tx(troca['actions'])
        self.assertIn('"deus", "etapa", "=", "\\"\\""', a)
        self.assertIn('"deus", "janela_amor", "False"', a)
        self.assertIn(f'"{g.ACAO_LUZ_AMBIENTE}"}}, "parameters": ["", "\\"Luz\\"", "luz_ambiente_normal"]', a)
        self.assertIn('"luz_pato", "luz_pato_raio"', a)
        self.assertIn('"luz_olhar", "deus.olhar_raio_idle"', a)
        self.assertIn('"Show"}, "parameters": ["deus"', a)
        for obj in ('luz_halo', 'feixe_olhar'):
            self.assertIn(f'"Delete"}}, "parameters": ["{obj}"', a)

    def test_pupila_fechada_com_escudo_ou_olho_fechado(self):
        guarda = self.ev('Pupila fechada')
        self.assertLess(self.nomes.index('Pupila fechada'), self.nomes.index('Dano na pupila'))
        escudo = next(e for e in guarda['events'] if '"deus.canal_vivos", ">", "0"' in tx(e['conditions']))
        self.assertIn('"deus", "vulneravel", "False"', tx(escudo['actions']))
        self.assertIn('"deus", "janela_amor", "False"', tx(escudo['actions']))
        for etapa in ('fecha', 'escuro'):
            e = next(e for e in guarda['events'] if f'"deus", "etapa", "=", "\\"{etapa}\\""' in tx(e['conditions']))
            self.assertIn('"deus", "vulneravel", "False"', tx(e['actions']))


if __name__ == '__main__':
    unittest.main()
