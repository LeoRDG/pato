"""Tarefa 208: bordas certas no lugar do tile preto genérico (144) no Inferno e no Purgatório.
Muitos tiles de chão, parede e canto foram pintados com o 144 (preto liso). Para cada 144 que tem um lado ou uma diagonal
aberta, a tarefa põe a peça do autotile que corresponde:
- lados abertos (vizinho de cima, direita, baixo ou esquerda vazio): chão (crosta em cima), paredes (borda irregular),
  teto (estalactites embaixo) e as combinações (quinas, colunas, plataformas);
- cantos internos (os dois lados encostam em terreno mas a diagonal está vazia): as peças com a pontinha de crosta no canto.
As peças (0..97, mesma disposição nos três atlas) foram identificadas pelo desenho do atlas do Inferno: crosta vermelha em
cima = topo aberto; borda transparente = lado/baixo aberto; crosta só no canto = canto interno.
- "Sólido" é o que tem colisão no tilemap (tilesWithHitBox), menos as tábuas das pontes. Vizinho fora do tilemap é procurado
  nos outros tilemaps de terreno da mesma cena (o Inferno e o Purgatório têm dois que se encostam); fora de todos conta como
  sólido (não põe borda na beira do mapa).
- Entre as variantes de uma peça, a escolha varia de célula para célula (sorteio fixo pela posição), com mais peso para as
  que o mapa já usa mais. Combinação de cantos que o atlas não tem: a peça mais parecida que não desenha borda onde não há
  buraco.
- Só muda célula que é 144; tile que já era borda fica como está. A colisão não muda (todas essas peças têm colisão).
Rodar uma vez:  python3 tools/t208_bordas_dos_tiles.py      (--previa: só gera imagens antes/depois, sem mexer no jogo.json)
"""
import collections, sys, zlib
from gd_mig import *

GENERICO = 144
TABUAS = {108, 109, 110, 125, 126, 127, 142}
CENAS = {'Inferno': ('tiles_inferno', 'tiles_inferno_escuro_'), 'Purgatorio': ('tiles_purgatorio',)}
# peça -> (N, E, S, W, cNE, cNW, cSE, cSW): lado aberto / canto interno aberto
PECAS = {}
for ids, sig in [
    ([1, 41, 52, 92], 'N'), ([19, 23, 70, 74], 'E'), ([7, 35, 58, 86], 'S'), ([17, 25, 68, 76], 'W'),
    ([2, 53], 'NE'), ([0, 51], 'NW'), ([36, 87], 'ES'), ([34, 85], 'SW'), ([4, 38, 55, 89], 'NS'),
    ([20, 22, 29, 71, 73, 80], 'EW'), ([10, 12, 61, 63], 'NEW'), ([28, 79], 'NES'), ([26, 77], 'NSW'),
    ([44, 46, 95, 97], 'ESW'),
    ([3, 54], 'NW+cSE'), ([5, 56], 'NE+cSW'), ([37, 88], 'SW+cNE'), ([39, 90], 'ES+cNW'),
    ([40, 91], '+cNE'), ([42, 93], '+cNW'), ([6, 57], '+cSE'), ([8, 59], '+cSW'), ([27, 78], '+cNE+cNW+cSE+cSW'),
]:
    lados, _, cantos = sig.partition('+')
    chave = tuple(l in lados for l in 'NESW') + tuple(f'c{c}' in sig for c in ('NE', 'NW', 'SE', 'SW'))
    for i in ids:
        PECAS[i] = chave


def assinatura(solido, x, y):
    s = lambda dx, dy: solido(x + dx, y + dy)
    N, E, S, W = not s(0, -1), not s(1, 0), not s(0, 1), not s(-1, 0)
    return (N, E, S, W,
            not N and not E and not s(1, -1), not N and not W and not s(-1, -1),
            not S and not E and not s(1, 1), not S and not W and not s(-1, 1))


def escolhe(sig, uso, x, y):
    """peça com os mesmos lados; nos cantos, falta custa 1 e sobra custa 2 (borda onde não há buraco é pior)."""
    melhor, custo = [], None
    for i, p in PECAS.items():
        if p[:4] != sig[:4]:
            continue
        c = sum(1 if a and not b else 2 if b and not a else 0 for a, b in zip(sig[4:], p[4:]))
        if custo is None or c < custo:
            melhor, custo = [i], c
        elif c == custo:
            melhor.append(i)
    if not melhor:
        return None
    melhor.sort()
    pesos = [uso[i] + 1 for i in melhor]
    h = zlib.crc32(f'{x},{y}'.encode()) % sum(pesos)
    for i, p in zip(melhor, pesos):
        if h < p:
            return i
        h -= p


def mapas_da_cena(d, nome):
    l = cena(d, nome)
    out = []
    for inst in l['instances']:
        if inst['name'] in CENAS[nome]:
            prop = next(p for p in inst['stringProperties'] if p['name'] == 'tilemap')
            t = json.loads(prop['value'])
            ob = objeto(d, inst['name'])
            hit = {int(v) for v in ob['content']['tilesWithHitBox'].split(',') if v.strip()} - TABUAS
            esc = (inst['width'] / (t['dimX'] * 64)) if inst.get('customSize') and inst.get('width') else 1
            assert esc == 1, (nome, inst['name'], esc)
            out.append(dict(inst=inst, prop=prop, t=t, T=t['layers'][0]['tiles'], hit=hit,
                            ox=inst['x'], oy=inst['y'], atlas=ob['content']['atlasImage']))
    return out


def corrige(d, previa=None):
    total = {}
    for nome in CENAS:
        mapas = mapas_da_cena(d, nome)
        orig = [[row[:] for row in m_['T']] for m_ in mapas]

        def solido_mundo(wx, wy):
            # ponto do mundo: sólido se algum tilemap tem terreno ali; fora de todos conta como sólido
            achou = False
            for m_, T in zip(mapas, orig):
                x, y = int((wx - m_['ox']) // 64), int((wy - m_['oy']) // 64)
                if 0 <= y < len(T) and 0 <= x < len(T[0]):
                    achou = True
                    if T[y][x] in m_['hit']:
                        return True
            return not achou

        def solido_de(m_, T):
            def solido(x, y):
                if 0 <= y < len(T) and 0 <= x < len(T[0]):
                    return T[y][x] in m_['hit']
                return solido_mundo(m_['ox'] + (x + 0.5) * 64, m_['oy'] + (y + 0.5) * 64)
            return solido

        uso = collections.Counter(v for T in orig for row in T for v in row)
        mudou = 0
        for m_, T in zip(mapas, orig):
            for y, row in enumerate(T):
                for x, v in enumerate(row):
                    if v != GENERICO:
                        continue
                    sig = assinatura(solido_de(m_, T), x, y)
                    if not any(sig):
                        continue
                    gx, gy = round(m_['ox'] / 64) + x, round(m_['oy'] / 64) + y
                    novo = escolhe(sig, uso, gx, gy)
                    if novo is not None and novo != v:
                        m_['T'][y][x] = novo
                        mudou += 1
        total[nome] = mudou
        if previa:
            previa(nome, mapas, orig)
        else:
            for m_ in mapas:
                m_['prop']['value'] = json.dumps(m_['t'], separators=(',', ':'))
    return total


def migra(d):
    print(corrige(d))


def ja_aplicada(d):
    return False   # a correção só mexe em 144 com borda aberta; rodar de novo não muda nada


if __name__ == '__main__':
    if '--previa' in sys.argv:
        from PIL import Image
        saida = sys.argv[sys.argv.index('--previa') + 1]
        d = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'), encoding='utf-8'))
        atlas_cache = {}

        def desenha(nome, mapas, orig):
            px = 16
            x0 = min(m_['ox'] for m_ in mapas) / 64; y0 = min(m_['oy'] for m_ in mapas) / 64
            x1 = max(m_['ox'] / 64 + len(m_['T'][0]) for m_ in mapas); y1 = max(m_['oy'] / 64 + len(m_['T']) for m_ in mapas)
            for tag, fonte in (('antes', orig), ('depois', [m_['T'] for m_ in mapas])):
                img = Image.new('RGBA', (int((x1 - x0) * px), int((y1 - y0) * px)), (60, 60, 90, 255))
                for m_, T in zip(mapas, fonte):
                    if m_['atlas'] not in atlas_cache:
                        a = Image.open(m_['atlas']).convert('RGBA')
                        atlas_cache[m_['atlas']] = {i: a.crop(((i % 17) * 64, (i // 17) * 64, (i % 17) * 64 + 64, (i // 17) * 64 + 64)).resize((px, px), Image.NEAREST) for i in range(153)}
                    A = atlas_cache[m_['atlas']]
                    for y, row in enumerate(T):
                        for x, v in enumerate(row):
                            if v >= 0:
                                t = A[v]
                                img.paste(t, (int((x + m_['ox'] / 64 - x0) * px), int((y + m_['oy'] / 64 - y0) * px)), t)
                img.save(f'{saida}/{nome}_{tag}.png')
        print(corrige(d, desenha))
    else:
        roda(migra, ja_aplicada, 't208')
