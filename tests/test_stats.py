"""Telas de atributos (tools/t190_stats.py), no visual "Plano": só texto sobre painéis lisos, cores neutras (sem roxo).
- pedestal: painel em cima da arma, cada linha com nome, valor e a diferença para a arma equipada; [E] PEGAR no
  cabeçalho (substitui a dica "E - ARMA");
- mercador: um painel em três colunas (arma equipada | loja | pato) e um rodapé com o item escolhido; o upgrade
  escolhido mostra o que muda.
As contas são as mesmas do 'Aplicar upgrades' (Jogador)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

STATS_ARMA = ('dano', 'tiros', 'dps', 'pente', 'recarga', 'mobilidade')
STATS_PATO = ('vida', 'velocidade', 'pulos', 'ricochete', 'perfuracao', 'eletricidade', 'laser')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class Stats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.g = m.acha(m.folha(cls.d, 'Hubs')['events'], 'Atributos')
        cls.t = tx(cls.g)
        cls.vars = {v['name']: v for v in cls.d['variables']}

    def test_so_texto_e_retangulos(self):
        for o in ('stats_rotulos', 'stats_valores', 'stats_fundo', 'ui_painel', 'ui_icone', 'ui_seg', 'ui_pip'):
            self.assertIsNone(m.objeto(self.d, o), o)
        c = m.objeto(self.d, 'ui_txt')['content']
        self.assertEqual(c['font'], 'Name Smile.otf')
        self.assertFalse(c['isShadowEnabled'])
        for o in ('ui_fundo_mundo', 'ui_fundo_hud'):
            self.assertEqual(m.objeto(self.d, o)['type'], 'PrimitiveDrawing::Drawer')
        self.assertFalse([r for r in self.d['resources']['resources'] if r['file'].startswith('assets/ui/')])

    def test_sem_roxo(self):
        cores = {n: v['value'] for n, v in self.vars.items() if n.startswith('ui_cor_')}
        self.assertTrue(cores)
        for n, c in cores.items():
            r, g, b = (int(x) for x in c.split(';'))
            self.assertFalse(b > g + 8 and r > g, f'{n} = {c} parece roxo')

    def test_contas_iguais_as_do_jogo(self):
        self.assertIn('Arma.cooldown_base * pow(pato.upg_cadencia', self.t)
        self.assertIn('Arma.recarga_base * pow(pato.upg_recarga', self.t)
        self.assertIn('Arma.FireBullet::BulletQuantity()', self.t)
        self.assertIn('Arma.dano_explosao', self.t)
        self.assertIn('pato.upg_vida_base + pato.upg_vida_nivel', self.t)
        self.assertIn('pato.velocidade_base * (1 + pato.upg_velocidade', self.t)
        for s in STATS_ARMA:
            self.assertIn(f'.atual.{s}', self.t, s)
            self.assertIn(f'.novo.{s}', self.t, s)
        for s in STATS_PATO:
            self.assertIn(f'stats_pato.novo.{s}', self.t, s)

    def test_cartoes_e_colunas(self):
        for c in ('arma', 'larma', 'loja', 'lpato', 'rodape'):
            self.assertIn(f'ui_card.{c}.x', self.t, c)
            self.assertIn(f'ui_lin.{c}', self.t + tx(m.folha(self.d, 'Loja')['events']), c)

    def test_previa_do_upgrade_escolhido(self):
        self.assertIn('stats_nivel[loja_sel_id]', self.t)
        self.assertIn('"loja_sel_nivel", "<", "loja_sel_max"', self.t)

    def test_pedestal_substitui_a_dica(self):
        self.assertIn('"Hide"}, "parameters": ["arma_dica"', self.t)
        self.assertIn('PEGAR', self.t)
        self.assertIn('stats_hover', tx(m.acha(m.folha(self.d, 'Hubs')['events'], 'Armas no hub')))

    def test_loja_antiga_escondida_e_mouse_por_linha(self):
        for o in ('loja_painel', 'loja_faixa', 'loja_linha', 'loja_desc'):
            self.assertIn(f'"Hide"}}, "parameters": ["{o}"', self.t, o)
        loja = tx(m.folha(self.d, 'Loja')['events'])
        self.assertNotIn('"SourisSurObjet"}, "parameters": ["loja_linha"', loja)
        self.assertIn('ui_mouse_lin', loja)
        self.assertIn('ESPACO', self.t)

    def test_numeros_em_variaveis(self):
        self.assertLessEqual({'ui_w_arma', 'ui_m_h', 'ui_rod_y', 'ui_op_fundo', 'ui_tam_val', 'stats_precisao',
                              'stats_nome'}, set(self.vars))
        for e in m.todos(self.g['events']):
            for a in e.get('conditions', []) + e.get('actions', []):
                if a['parameters'][1:2] == ['linha'] or a['parameters'][0].endswith('.linhas'):  # contagem, não ajuste
                    continue
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.#])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '100'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
