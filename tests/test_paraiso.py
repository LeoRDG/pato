"""Fase do Paraíso (tools/t83_paraiso.py): cena, correntes de luz, queda, anjos e um caminho do portão até o Empíreo."""
import json, math, os, unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from folhas import folha, inimigos_todos
from collections import deque

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))
T = 64


def tiles(inst):
    valor = next((p['value'] for p in inst['stringProperties'] if p['name'] == 'tilemap'), None)
    return json.loads(valor)['layers'][0]['tiles'] if valor else []


class Paraiso(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(JOGO, encoding='utf-8'))
        cls.cena = next(l for l in cls.d['layouts'] if l['name'] == 'Paraiso')
        cls.obj = {o['name']: o for o in cls.d['objects']}
        cls.var = {v['name']: v['value'] for v in cls.cena['variables']}
        cls.pato = next(i for i in cls.cena['instances'] if i['name'] == 'pato')
        cls.solido, cls.nuvem = set(), set()
        for i in cls.cena['instances']:
            if i.get('layer', '') != '' or i['name'] not in ('tiles_ceu', 'tiles_ceu_ponte'):
                continue
            hit = {int(x) for x in cls.obj[i['name']]['content']['tilesWithHitBox'].split(',') if x}
            alvo = cls.solido if i['name'] == 'tiles_ceu' else cls.nuvem
            for r, linha in enumerate(tiles(i)):
                for c, t in enumerate(linha):
                    if t in hit:
                        alvo.add((round(i['x'] / T) + c, round(i['y'] / T) + r))
        cls.correntes = [i for i in cls.cena['instances'] if i['name'] == 'corrente_luz']

    def test_cena_depois_do_purgatorio_com_os_eventos_comuns(self):
        nomes = [l['name'] for l in self.d['layouts']]
        self.assertEqual(nomes.index('Paraiso'), nomes.index('Purgatorio') + 1)
        links = [e['target'] for e in self.cena['events'] if e['type'] == 'BuiltinCommonInstructions::Link']
        self.assertEqual(links, ['Jogador', 'Inimigos', 'InimigosParaiso', 'Combate', 'HUD', 'Portais', 'Musica'])  # Musica: t209
        # (t138) a camada de luz da luta com o chefe final fica escondida até a luta
        self.assertEqual([c['name'] for c in self.cena['layers']], ['Fundo', 'Estrelas', '', 'Luz', 'HUD'])  # Estrelas: t167
        self.assertTrue(all(c['visibility'] for c in self.cena['layers'] if c['name'] != 'Luz'))
        presentes = {i['name'] for i in self.cena['instances']}
        self.assertLessEqual({'pato', 'alvo', 'hud_vida_fill', 'hud_moeda', 'moedas', 'municao', 'hud_tempo',
                              'bg_paraiso_nuvens', 'bg_paraiso_rosa', 'tiles_ceu_decor'}, presentes)
        uuids = [i['persistentUuid'] for l in self.d['layouts'] for i in l['instances']]
        self.assertEqual(len(uuids), len(set(uuids)))
        # as folhas comuns usam essas variáveis de cena
        self.assertLessEqual({'laser_x', 'olho_rx', 'olho_ry', 'moscas_alerta'}, set(self.var))

    def test_numeros_em_variaveis(self):
        txt = json.dumps(self.cena['events'])
        for v in ('fundo_parallax_x', 'fundo_parallax_y', 'fundo_dx', 'fundo_dy', 'saida_x_min', 'saida_x_max',
                  'saida_y', 'proxima_cena', 'queda_y', 'queda_dano', 'retorno_x', 'retorno_y'):
            self.assertIn(v, self.var)
            self.assertIn(v, txt)
        self.assertIn(self.var['proxima_cena'], [l['name'] for l in self.d['layouts']])
        ev = json.dumps(folha(self.d, 'CorrentesDeLuz'))
        for v in ('forca', 'ligada', 'desligada', 'aviso', 'defasagem', 'opacidade_ligada', 'opacidade_desligada', 'pisca_vel'):
            self.assertIn(f'corrente_luz.{v}', ev)
        self.assertIn('SetCurrentFallSpeed', ev)
        self.assertNotIn('JsCode', ev + txt)

    def test_anjos_e_moedas(self):
        nomes = [i['name'] for i in self.cena['instances']]
        for anjo in ('querubim', 'serafim', 'ofanim', 'roda_anjo'):
            self.assertIn(anjo, nomes)
        moedas = [i for i in self.cena['instances'] if i['name'] == 'moeda']
        self.assertGreaterEqual(len(moedas), 20)
        for m in moedas:
            c, r = int((m['x'] + m['width'] / 2) // T), int((m['y'] + m['height'] / 2) // T)
            self.assertNotIn((c, r), self.solido)

    def test_da_para_chegar_ao_empireo(self):
        """Como no Purgatório: o pato (lw x lh tiles) anda, cai e pula (com o pulo no ar) entre lugares de pé; nuvem
        só segura por cima. Dentro de uma corrente de luz (acesa) ele sobe até o topo dela e flutua ali: cada célula
        da corrente conta como lugar de pé. Chega na saída e nunca passa de queda_y."""
        b = {x['name']: x for x in self.obj['pato']['behaviors']}
        p = b['PlatformerObject']
        pulo = p['jumpSpeed'] * p['jumpSustainTime'] + p['jumpSpeed'] ** 2 / (2 * p['gravity'])
        subida = int(pulo * (1 + b['AdvancedJump']['AirJumpCountMaximum']) * 0.9 // T)
        dx_max = 7
        lw, lh = math.ceil(self.pato['width'] / T), math.ceil(self.pato['height'] / T)
        S, P = self.solido, set(self.nuvem)
        for c in self.correntes:
            for x in range(int(c['x'] // T), int((c['x'] + c['width']) // T)):
                for y in range(int(c['y'] // T) - 1, int((c['y'] + c['height']) // T)):
                    P.add((x, y))
        queda = int(self.var['queda_y'] // T)

        def livre(c, r):
            return all((c + i, r - j) not in S for i in range(lw) for j in range(lh))

        def apoio(c, r):
            return any((c + i, r + 1) in S or (c + i, r + 1) in P for i in range(lw))

        def cai(c, r):
            while not apoio(c, r):
                r += 1
                if r > queda:
                    return None                               # caiu do céu: volta para onde estava
                if not livre(c, r):
                    return None
            return r

        cmin, cmax = min(c for c, _ in S) - 2, max(c for c, _ in S) + 2
        rmin, rmax = min(r for _, r in S | P) - lh - 2, queda
        c0 = round(self.pato['x'] / T)
        r0 = cai(c0, int((self.pato['y'] + self.pato['height'] - 1) // T))
        de_pe = {(c, r) for c in range(cmin, cmax) for r in range(rmin, rmax) if livre(c, r) and apoio(c, r)}
        na_saida = lambda c, r: (self.var['saida_x_min'] <= (c + lw / 2) * T <= self.var['saida_x_max']
                                 and (r + 1) * T <= self.var['saida_y'])
        vistos, fila = {(c0, r0)}, deque([(c0, r0)])
        while fila:
            c, r = fila.popleft()
            if na_saida(c, r):
                continue
            prox = []
            for dc in (-1, 1):
                if livre(c + dc, r):
                    rr = cai(c + dc, r)
                    if rr is not None:
                        prox.append((c + dc, rr))
            for (c2, r2) in de_pe:
                if abs(c2 - c) > dx_max or not 0 < r - r2 <= subida:
                    continue
                topo = r2 - 1
                if all(livre(c, t) for t in range(topo, r + 1)) and \
                        all(livre(x, topo) for x in range(min(c, c2), max(c, c2) + 1)) and livre(c2, r2):
                    prox.append((c2, r2))
            for n in prox:
                if n not in vistos:
                    vistos.add(n)
                    fila.append(n)
        self.assertTrue([v for v in vistos if na_saida(*v)],
                        'não chega na saída; mais à direita: %s' % (max(vistos),))

    def test_correntes_so_seguram_acesas(self):
        """Sem as correntes não dá para atravessar o abismo do Sol nem subir ao Empíreo."""
        self.assertGreaterEqual(len(self.correntes), 3)
        self.assertEqual(self.obj['corrente_luz']['type'], 'TiledSpriteObject::TiledSprite')
        ev = json.dumps(folha(self.d, 'CorrentesDeLuz'))
        self.assertIn('"ativa", "True"', ev)
        self.assertIn('mod(corrente_luz.t + corrente_luz.defasagem, corrente_luz.ligada + corrente_luz.desligada)', ev)


if __name__ == '__main__':
    unittest.main()
