"""Fase do Purgatório (tools/t72_purgatorio_fase.py): cena, eventos, variáveis e um caminho do começo até o cume."""
import json, math, os, unittest
from collections import deque

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = 64


def tiles(inst):
    return json.loads(next(p['value'] for p in inst['stringProperties'] if p['name'] == 'tilemap'))['layers'][0]['tiles']


class Purgatorio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.cena = next(l for l in cls.d['layouts'] if l['name'] == 'Purgatorio')
        cls.obj = {o['name']: o for o in cls.d['objects']}
        cls.var = {v['name']: v['value'] for v in cls.cena['variables']}
        cls.pato = next(i for i in cls.cena['instances'] if i['name'] == 'pato')
        # células sólidas e de tronco, em coordenadas de tile do mundo
        cls.solido, cls.tronco = set(), set()
        for i in cls.cena['instances']:
            if i.get('layer', '') != '' or i['name'] not in ('tiles_purgatorio', 'tiles_purgatorio_ponte'):
                continue
            hit = {int(x) for x in cls.obj[i['name']]['content']['tilesWithHitBox'].split(',') if x}
            alvo = cls.solido if i['name'] == 'tiles_purgatorio' else cls.tronco
            for r, linha in enumerate(tiles(i)):
                for c, t in enumerate(linha):
                    if t in hit:
                        alvo.add((round(i['x'] / T) + c, round(i['y'] / T) + r))
        # rodas: o tronco passa por todo o círculo, então cada ponto dele vale como um tronco parado (dá para esperar)
        cls.rodas = [i for i in cls.cena['instances'] if i['name'] == 'plataforma_radial']
        for i in cls.rodas:
            v = {x['name']: x['value'] for x in i['initialVariables']}
            larg = i['width'] if i.get('customSize') else 192
            ancora = v.get('ancora_y', 14)
            for g in range(0, 360, 5):
                x0 = v['centro_x'] + v['raio'] * math.cos(math.radians(g)) - larg / 2
                topo = v['centro_y'] + v['raio'] * math.sin(math.radians(g)) - ancora + 4 * larg / 192
                for c in range(math.floor((x0 + 8) / T), math.floor((x0 + larg - 8) / T) + 1):
                    cls.tronco.add((c, math.floor(topo / T)))
        # lajes que somem voltam depois de sumida s: para o caminho valem como troncos parados
        cls.lajes = [i for i in cls.cena['instances'] if i['name'] == 'plataforma_some']
        for i in cls.lajes:
            for c in range(math.floor((i['x'] + 8) / T), math.floor((i['x'] + 192 - 8) / T) + 1):
                cls.tronco.add((c, math.floor((i['y'] + 2) / T)))
        cls.acidos = [i for i in cls.cena['instances'] if i['name'] == 'acido']

    def test_cena_logo_depois_do_inferno_com_os_eventos_comuns(self):
        nomes = [l['name'] for l in self.d['layouts']]
        self.assertEqual(nomes.index('Purgatorio'), nomes.index('Inferno') + 1)
        links = [e['target'] for e in self.cena['events'] if e['type'] == 'BuiltinCommonInstructions::Link']
        self.assertEqual(links, ['Jogador', 'AplicarUpgrades', 'Inimigos', 'Combate', 'HUD', 'PlataformasRadiais', 'Armadilhas'])
        self.assertEqual([c['name'] for c in self.cena['layers']], ['Fundo', '', 'HUD'])
        presentes = {i['name'] for i in self.cena['instances']}
        self.assertLessEqual({'pato', 'alvo', 'hud_vida_fill', 'hud_moeda', 'moedas', 'municao', 'hud_tempo'}, presentes)
        self.assertNotIn('demonio_chefe', presentes)
        uuids = [i['persistentUuid'] for l in self.d['layouts'] for i in l['instances']]
        self.assertEqual(len(uuids), len(set(uuids)))

    def test_numeros_em_variaveis(self):
        txt = json.dumps(self.cena['events'])
        for v in ('fundo_parallax_x', 'fundo_parallax_y', 'fundo_dx', 'fundo_dy', 'saida_x_min', 'saida_x_max',
                  'saida_y', 'proxima_cena'):
            self.assertIn(v, self.var)
            self.assertIn(v, txt)
        self.assertIn(self.var['proxima_cena'], [l['name'] for l in self.d['layouts']])
        saida = next(e for e in self.cena['events'] if e.get('name') == 'Saída no cume')['events'][0]
        self.assertEqual(saida['actions'][0]['parameters'][1], 'proxima_cena')

    def test_moedas_flutuam_fora_do_terreno(self):
        moedas = [i for i in self.cena['instances'] if i['name'] == 'moeda']
        self.assertGreaterEqual(len(moedas), 20)
        for m in moedas:
            self.assertIn({'name': 'tem_gravidade', 'value': False},
                          [{k: v[k] for k in ('name', 'value')} for v in m['initialVariables']])
            c, r = int((m['x'] + m['width'] / 2) // T), int((m['y'] + m['height'] / 2) // T)
            self.assertNotIn((c, r), self.solido)

    def test_da_para_subir_do_comeco_ao_cume(self):
        """Busca num grid de tiles: o pato (3 x 3 tiles) anda, cai e pula (com o pulo no ar) de onde está de pé até
        outro lugar de pé, por um caminho em caixa (sobe, anda, desce) que não atravessa terreno; tronco só segura
        por cima. Chega no cume, na área da saída (que troca de cena), e nunca cai para fora do mapa."""
        b = {x['name']: x for x in self.obj['pato']['behaviors']}
        p = b['PlatformerObject']
        pulo = p['jumpSpeed'] * p['jumpSustainTime'] + p['jumpSpeed'] ** 2 / (2 * p['gravity'])
        pulos = 1 + b['AdvancedJump']['AirJumpCountMaximum']
        subida = int(pulo * pulos * 0.9 // T)               # com folga
        dx_max = 7
        lw, lh = math.ceil(self.pato['width'] / T), math.ceil(self.pato['height'] / T)
        S, P = self.solido, self.tronco
        cmin, cmax = min(c for c, _ in S), max(c for c, _ in S)
        rmin, rmax = min(r for _, r in S) - lh - 2, max(r for _, r in S)

        def livre(c, r):                                       # r = linha dos pés
            return all((c + i, r - j) not in S for i in range(lw) for j in range(lh))

        def apoio(c, r):
            return any((c + i, r + 1) in S or (c + i, r + 1) in P for i in range(lw))

        def cai(c, r):
            while not apoio(c, r):
                r += 1
                self.assertLess(r, rmax + 5, 'caiu para fora do mapa')
                if not livre(c, r):
                    return None
            return r

        c0 = round(self.pato['x'] / T)
        r0 = cai(c0, int((self.pato['y'] + self.pato['height'] - 1) // T))
        de_pe = {(c, r) for c in range(cmin, cmax) for r in range(rmin, rmax) if livre(c, r) and apoio(c, r)}
        vistos, fila = {(c0, r0)}, deque([(c0, r0)])
        margem = next(v['value'] for v in self.obj['acido']['variables'] if v['name'] == 'margem')
        no_acido = lambda c, r: any(a['x'] < (c + lw) * T and c * T < a['x'] + 384 and (r + 1) * T > a['y'] + margem
                                    for a in self.acidos)
        na_saida = lambda c, r: (self.var['saida_x_min'] <= (c + lw / 2) * T <= self.var['saida_x_max']
                                 and (r + 1) * T <= self.var['saida_y'])
        while fila:
            c, r = fila.popleft()
            if na_saida(c, r):                                 # a saída troca de cena: dali não se anda mais
                continue
            if no_acido(c, r):                                 # o ácido devolve o pato para a beira do poço
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
        saida = [v for v in vistos if na_saida(*v)]
        self.assertTrue(saida, 'não chega na saída; ponto mais alto: %s' % (min(vistos, key=lambda v: v[1]),))


    def test_rodas_de_troncos(self):
        """Plataforma radial: gira em volta do centro (não vai e volta como a do Inferno), presa por um cipó."""
        o = self.obj['plataforma_radial']
        self.assertEqual([b['platformType'] for b in o['behaviors']], ['Jumpthru'])
        self.assertLessEqual({'centro_x', 'centro_y', 'raio', 'vel_ang', 'angulo', 'ancora_y', 'com_eixo'},
                             {v['name'] for v in o['variables']})
        self.assertEqual(self.obj['plataforma_radial_corda']['type'], 'TiledSpriteObject::TiledSprite')
        self.assertIn('plataforma_radial_eixo', self.obj)
        ev = json.dumps(next(e for e in self.d['externalEvents'] if e['name'] == 'PlataformasRadiais')['events'])
        for trecho in ('vel_ang * TimeDelta()', 'raio * cos(ToRad(plataforma_radial.angulo))', 'ini_x'):
            (self.assertNotIn if trecho == 'ini_x' else self.assertIn)(trecho, ev)
        rodas = {}
        for i in self.rodas:
            v = {x['name']: x['value'] for x in i['initialVariables']}
            v['_larg'] = i['width'] if i.get('customSize') else 192
            rodas.setdefault((v['centro_x'], v['centro_y']), []).append(v)
        self.assertEqual(sorted(len(r) for r in rodas.values() if r[0]['_larg'] == 192), [2, 3])
        for r in rodas.values():
            self.assertEqual(sum(v['com_eixo'] for v in r), 1)           # uma pedra por roda
            self.assertEqual(len({(v['raio'], v['vel_ang']) for v in r}), 1)
        self.assertEqual({v['vel_ang'] > 0 for r in rodas.values() for v in r}, {True, False})   # uma em cada sentido
        # o tronco e o pato em cima dele nunca entram no terreno
        for r in rodas.values():
            v = r[0]
            for g in range(0, 360, 3):
                cx = v['centro_x'] + v['raio'] * math.cos(math.radians(g))
                topo = v['centro_y'] + v['raio'] * math.sin(math.radians(g)) - v.get('ancora_y', 14)
                for x in range(int(cx - v['_larg'] / 2), int(cx + v['_larg'] / 2), 16):
                    for y in range(int(topo - self.pato['height']), int(topo + 30), 16):
                        self.assertNotIn((x // T, y // T), self.solido)


    def test_escalada_final_com_armadilhas(self):
        """Depois do cume: lajes que somem, jatos de fogo purificador nas paredes, ácido no fundo e rodas pequenas e rápidas."""
        ev = json.dumps(next(e for e in self.d['externalEvents'] if e['name'] == 'Armadilhas')['events'])
        for trecho in ('ActivateBehavior', '"Platform", "no"', 'IsOnFloor', 'plataforma_some.sumida', 'plataforma_some.aviso',
                       'mod(jato_fogo.t, jato_fogo.espera + jato_fogo.aviso + jato_fogo.disparo)',
                       'jato_fogo_chama.dano', 'jato_fogo.alcance_aviso', 'jato_fogo.vel_chama', 'acido.margem', 'acido.dano', 'retorno_x', 'retorno_y'):
            self.assertIn(trecho, ev)
        self.assertGreaterEqual(len(self.lajes), 8)
        self.assertGreaterEqual(sum(i['name'] == 'jato_fogo' for i in self.cena['instances']), 5)
        lados = {v['value'] for i in self.cena['instances'] if i['name'] == 'jato_fogo'
                 for v in i['initialVariables'] if v['name'] == 'lado'}
        self.assertEqual(lados, {1, -1})                                   # das duas paredes
        self.assertNotIn('laser', ev)                                      # fogo que purifica, não laser
        self.assertEqual(self.obj['jato_fogo_chama']['type'], 'TiledSpriteObject::TiledSprite')
        self.assertTrue(self.acidos)
        z_pato = self.pato['zOrder']
        self.assertTrue(all(a['zOrder'] > z_pato for a in self.acidos))    # o pato afunda por trás da superfície
        pequenas = [i for i in self.rodas if i.get('customSize')]
        grandes = [i for i in self.rodas if not i.get('customSize')]
        vel = lambda i: abs(next(v['value'] for v in i['initialVariables'] if v['name'] == 'vel_ang'))
        self.assertGreaterEqual(len(pequenas), 5)
        self.assertLess(max(i['width'] for i in pequenas), 192)
        self.assertGreater(min(map(vel, pequenas)), max(map(vel, grandes)))
        # a saída fica no alto da escalada nova, acima do cume da primeira parte
        self.assertLess(self.var['saida_y'], -9408 - 60 * T)
        # o retorno do ácido é um lugar de pé, fora do ácido
        rx, ry = self.var['retorno_x'], self.var['retorno_y'] + self.pato['height']
        self.assertIn((int(rx // T) + 1, int(ry // T) + 1), self.solido)
        for a in self.acidos:
            self.assertFalse(a['x'] < rx + self.pato['width'] and rx < a['x'] + 384 and ry > a['y'])


if __name__ == '__main__':
    unittest.main()
