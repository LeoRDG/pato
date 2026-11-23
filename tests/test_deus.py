"""Deus, o olho de luz: corpo em partes, dano só na pupila, fases e morte (tools/t139_deus.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g

PARTES = ('deus_olho', 'deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa', 'deus_aura', 'deus_escudo')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class Deus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.grupos = {gr['name']: [x['name'] for x in gr['objects']] for gr in cls.d['objectsGroups']}
        cls.folha = m.folha(cls.d, 'InimigosParaiso')['events']
        cls.deus = m.acha(cls.folha, 'Deus')
        cls.cena = m.cena(cls.d, 'Paraiso')

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def ev(self, nome):
        return m.acha(self.deus['events'], nome)

    def test_objetos_e_grupos(self):
        self.assertIsNotNone(self.deus)
        for p in PARTES + ('deus', 'luz_olhar', 'canalizador', 'luz_halo', 'fragmento', 'feixe_olhar'):
            self.assertIn(p, self.o, p)
        for gr in ('Inimigo', 'Chefes', 'Personagem'):
            self.assertIn('deus', self.grupos[gr])
        for gr in ('Terrestre', 'Voador'):
            self.assertNotIn('deus', self.grupos[gr])
        for p in PARTES:
            self.assertNotIn(p, self.grupos['Inimigo'], 'só a pupila é inimigo')
        v = self.v('deus')
        self.assertIs(v['chefe_final'], True)
        self.assertIs(v['barra_ativa'], True)
        self.assertIs(v['firme'], True)
        self.assertIs(v['invulneravel'], True)
        self.assertEqual(v['qtd_moedas'], 0)
        self.assertEqual(v['nome'], 'DEUS')
        for nome in ('vida', 'max_vida', 'dano', 'estado', 'morto', 'preparado', 'bala_serie', 'kb_dir'):
            self.assertIn(nome, v, 'variáveis que os eventos genéricos de Inimigo usam')
        self.assertEqual(self.o['luz_olhar']['type'], g.OBJ_LUZ)
        self.assertEqual(self.o['luz_halo']['type'], g.OBJ_LUZ)

    def test_criado_pela_luta(self):
        e = next(e for e in m.todos(self.deus['events']) if '["deus_criar", "True", ""]' in tx(e.get('conditions', [])))
        a = tx(e['actions'])
        self.assertIn('["deus_criar", "False", ""]', a)
        for p in PARTES + ('deus',):
            self.assertIn(f'"Create"}}, "parameters": ["", "{p}"', a)

    def test_so_a_pupila_leva_dano(self):
        todos_ = list(m.todos(m.folha(self.d, 'InimigosParaiso')['events'])) + list(m.todos(self.cena['events']))
        self.assertFalse([e for e in todos_ if '"deus", "vida", "-"' in tx(e.get('actions', []))],
                         'o dano vem só de Combate (pupila no grupo Inimigo), respeitando invulneravel')
        libera = [e for e in todos_ if '"deus", "invulneravel", "False"' in tx(e.get('actions', []))]
        self.assertEqual(len(libera), 1)
        self.assertIn('"deus", "vulneravel", "True"', tx(libera[0]['conditions']))
        prende = [e for e in todos_ if '"deus", "invulneravel", "True"' in tx(e.get('actions', []))]
        self.assertTrue(any('"deus", "vulneravel", "False"' in tx(e['conditions']) for e in prende))

    def test_fases_por_vida(self):
        f = tx(self.ev('Fases'))
        for k in (2, 3, 4):
            self.assertIn(f'"deus.max_vida * deus.fase{k}_abaixo"', f)
            self.assertIn(f'deus.subida_{k}', f)
        self.assertIn('"deus_anel_ouro", "Animation", "=", "\\"quebra\\""', f)

    def test_golpes_por_fase_sem_repetir(self):
        e = tx(self.ev('Escolha do golpe'))
        for k in (1, 2, 3, 4):
            self.assertIn(f'deus.golpes_{k}', e)
        for golpe in ('olhar', 'piscar', 'amor', 'juizo', 'aneis', 'puxao'):
            self.assertIn(f'"deus", "golpe", "=", "\\"{golpe}\\""', e)
        self.assertIn('deus.ultimo_golpe', e)

    def test_janela_aberta_so_antes_da_fase_3(self):
        e = self.ev('Janela aberta')
        abre = next(x for x in m.todos(e['events']) if '"deus", "vulneravel", "True"' in tx(x['actions']))
        self.assertIn('"deus", "fase", "<", "3"', tx(abre['conditions']))
        self.assertIn('fim_golpe', tx(abre['conditions']))

    def test_morte_limpa_tudo(self):
        e = self.ev('Morte')
        a = tx(e)
        for obj in ('canalizador', 'luz_halo', 'fragmento', 'feixe_olhar', 'luz_olhar', 'projetil_inimigo'):
            self.assertIn(f'"Delete"}}, "parameters": ["{obj}"', a)
        self.assertIn('"deus", "vulneravel", "False"', a)
        self.assertIn(f'"{g.ACAO_LUZ_AMBIENTE}"', a)
        fim = m.acha(self.cena['events'], 'Fim da luta')
        self.assertIn('"SceneInstancesCount"}, "parameters": ["", "deus_olho", "=", "0"]', tx(fim))
        saida = m.acha(self.cena['events'], 'Saída no Empíreo')
        sai = next(x for x in m.todos(saida['events']) if '"Scene"' in tx(x['actions']))
        self.assertIn('["luta", "False", ""]', tx(sai['conditions']))

    def test_variaveis_usadas_existem(self):
        texto = tx(self.deus)
        for obj in ('deus', 'pato') + PARTES:
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')
        for cena in ('Paraiso', 'Teste'):
            cv = m.vars_cena(self.d, cena)
            for nome in ('luta', 'deus_criar', 'subida_vel', 'luz_ambiente_normal'):
                self.assertIn(nome, cv, f'{cena}.{nome}')

    def test_numeros_em_variaveis(self):
        for e in m.todos([self.deus]):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '3', '4', '5', '6', '90'),  # 90: um quarto de volta
                                       f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
