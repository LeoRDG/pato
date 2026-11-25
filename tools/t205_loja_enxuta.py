"""Tarefa 205: loja mais enxuta e mais barata, moedas no começo e um upgrade novo (Estilhaços).
- Saem três dos upgrades da t197: Ímã, Incendiária e Cadáver Explosivo (a explosão do inimigo morto). Vampirismo fica.
  Somem o item do catálogo, o nível (upgrades.*), os eventos e as variáveis deles (pato.upg_ima, queima_*, cadaver_*,
  queima/queima_tick dos inimigos); o ímã volta ao alcance moeda.iman_dist. Nenhum deles chegou à main, então nenhum
  jogador tinha comprado.
- Estilhaços (upgrades.estilhaco): no primeiro impacto (inimigo, ou terreno sem ricochete sobrando) a bala do jogador solta
  pato.estilhaco_qtd (5) estilhaços. Se ainda pode atravessar (perfuração, ou a pistola, que já atravessa um), ela segue,
  mas não estilhaça de novo; senão ela vira os estilhaços.
  - No inimigo, os estilhaços saem em volta (pato.estilhaco_abertura, 360°), a partir da borda dele: não acertam de novo o
    inimigo que a bala acertou, vão nos vizinhos.
  - Na parede, saem de volta para fora num leque de pato.estilhaco_abertura_parede graus.
  - Cada estilhaço dá pato.estilhaco_dano * nível do dano da bala (25%, 50%, 75%), anda pato.estilhaco_alcance px a
    pato.estilhaco_vel da velocidade da bala, tem pato.estilhaco_escala do tamanho e pato.estilhaco_repulsao do empurrão.
    Estilhaço não estilhaça, não atravessa e não ricocheteia. Granadas (raio > 0) não estilhaçam.
- Preços mais baixos (preço do nível n = preco_base * preco_mult^n):
  - atributos básicos 100 * 1,5^n = 100, 150, 225 (antes 200, 400, 800);
  - efeitos (ricochete, perfuração, eletricidade, vampirismo, estilhaços) 200 * 1,5^n = 200, 300, 450 (antes 350, 700, 1400);
  - laser 800 (antes 1500).
  A loja inteira fica em ~8.400 moedas, pouco mais de duas idas ao Inferno. Só muda o preço que ainda está no valor da t198.
- Jogo novo começa com 300 moedas (valor inicial de moedas_total, se ainda era 0). Um save existente continua com as dele.
Rodar uma vez:  python3 tools/t205_loja_enxuta.py
"""
import copy
from gd_mig import *

SAEM = ('ima', 'incendiaria', 'cadaver')
VARS_PATO_SAEM = ('upg_ima', 'queima_tempo', 'queima_intervalo', 'queima_dano', 'cadaver_dano', 'cadaver_raio',
                  'cadaver_repulsao', 'cadaver_som_volume')
ESTILHACO = [('estilhaco_qtd', 5), ('estilhaco_dano', 0.25), ('estilhaco_vel', 0.8), ('estilhaco_alcance', 260),
             ('estilhaco_abertura', 360), ('estilhaco_abertura_parede', 150), ('estilhaco_escala', 0.6),
             ('estilhaco_repulsao', 0.3)]
BASICOS = ('cadencia', 'dano', 'recarga', 'velocidade', 'pulo', 'vida')
EFEITOS = ('ricochete', 'perfuracao', 'eletricidade', 'vampirismo')
NIVEL = 'GlobalVariable(upgrades.estilhaco)'

ESTILHACA = [
    'try {',
    '  // Estilhaços (t205): cada bala marcada (estilhacar) solta pato.estilhaco_qtd estilhaços; some se estilhaco_some.',
    '  const lista = runtimeScene.getObjects("projetil").filter((p) => p.getVariables().get("estilhacar").getAsBoolean());',
    '  if (lista.length) {',
    '    const V = runtimeScene.getGame().getVariables();',
    '    const pato = runtimeScene.getObjects("pato")[0];',
    '    const P = pato.getVariables();',
    '    const n = (k) => P.get(k).getAsNumber();',
    '    const nivel = V.get("upgrades").getChild("estilhaco").getAsNumber();',
    '    const SV = runtimeScene.getVariables().has("serie_bala") ? runtimeScene.getVariables().get("serie_bala") : V.get("serie_bala");',
    '    // Inimigo é um grupo (getObjects não pega grupo): quem tem bala_serie é inimigo',
    '    const inimigos = runtimeScene.getAdhocListOfAllInstances().filter((e) => e.getVariables().has("bala_serie"));',
    '    for (const p of lista) {',
    '      const pv = p.getVariables();',
    '      const g = (k) => pv.get(k).getAsNumber();',
    '      const parede = pv.get("estilhaco_parede").getAsBoolean();',
    '      const f = p.getAverageForce();',
    '      const vel = Math.hypot(f.getX(), f.getY()) * n("estilhaco_vel");',
    '      const rumo = Math.atan2(f.getY(), f.getX()) + (parede ? Math.PI : 0);',
    '      // na parede, sai de onde a bala estava antes de entrar nela',
    '      const cx = parede ? g("px") + (p.getCenterXInScene() - p.getX()) : p.getCenterXInScene();',
    '      const cy = parede ? g("py") + (p.getCenterYInScene() - p.getY()) : p.getCenterYInScene();',
    '      // o inimigo que a bala acertou (ele guarda a série dela): os estilhaços nascem fora dele',
    '      const alvo = parede ? null : inimigos.find((e) => e.getVariables().get("bala_serie").getAsNumber() === g("serie"));',
    '      const caixa = alvo ? alvo.getAABB() : null;',
    '      const qtd = Math.max(1, Math.round(n("estilhaco_qtd")));',
    '      const abertura = Math.min(360, parede ? n("estilhaco_abertura_parede") : n("estilhaco_abertura")) * Math.PI / 180;',
    '      const passo = abertura / qtd;',
    '      const inicio = abertura >= 2 * Math.PI - 1e-6 ? rumo + Math.random() * passo : rumo - abertura / 2 + passo / 2;',
    '      for (let i = 0; i < qtd; i++) {',
    '        const a = inicio + passo * i;',
    '        const dx = Math.cos(a), dy = Math.sin(a);',
    '        const o = runtimeScene.createObject("projetil");',
    '        o.setLayer(p.getLayer());',
    '        o.setZOrder(p.getZOrder());',
    '        o.setScaleX(p.getScaleX() * n("estilhaco_escala"));',
    '        o.setScaleY(p.getScaleY() * n("estilhaco_escala"));',
    '        let sx = cx, sy = cy;',
    '        if (caixa) {',
    '          // anda do ponto do acerto até sair da caixa do inimigo, na direção do estilhaço',
    '          const tx = dx > 0 ? (caixa.max[0] - cx) / dx : dx < 0 ? (caixa.min[0] - cx) / dx : Infinity;',
    '          const ty = dy > 0 ? (caixa.max[1] - cy) / dy : dy < 0 ? (caixa.min[1] - cy) / dy : Infinity;',
    '          // + metade do estilhaço: ele nasce sem encostar no inimigo',
    '          const t = Math.max(0, Math.min(tx, ty)) + Math.max(o.getWidth(), o.getHeight()) / 2 + 2;',
    '          sx = cx + dx * t;',
    '          sy = cy + dy * t;',
    '        }',
    '        o.setAngle(a * 180 / Math.PI);',
    '        o.setX(sx - (o.getCenterXInScene() - o.getX()));',
    '        o.setY(sy - (o.getCenterYInScene() - o.getY()));',
    '        o.addForce(dx * vel, dy * vel, 1);',
    '        const ov = o.getVariables();',
    '        SV.add(1);',
    '        ov.get("serie").setNumber(SV.getAsNumber());',
    '        ov.get("dano").setNumber(g("dano") * g("fator") * n("estilhaco_dano") * nivel);',
    '        ov.get("dano_var").setNumber(g("dano_var"));',
    '        ov.get("dano_explosao").setNumber(0);',
    '        ov.get("raio").setNumber(0);',
    '        ov.get("furos").setNumber(0);',
    '        ov.get("ricochetes").setNumber(0);',
    '        ov.get("alcance").setNumber(n("estilhaco_alcance"));',
    '        ov.get("queda_min").setNumber(1);',
    '        ov.get("fator").setNumber(1);',
    '        ov.get("repulsao").setNumber(g("repulsao") * n("estilhaco_repulsao"));',
    '        ov.get("percorrido").setNumber(0);',
    '        ov.get("px").setNumber(o.getX());',
    '        ov.get("py").setNumber(o.getY());',
    '        ov.get("ox").setNumber(sx);',
    '        ov.get("oy").setNumber(sy);',
    '        ov.get("rcx").setNumber(sx);',
    '        ov.get("rcy").setNumber(sy);',
    '        ov.get("iniciado").setBoolean(true);',
    '        ov.get("fragmento").setBoolean(true);',
    '      }',
    '      // a bala que ainda atravessa segue (sem estilhaçar de novo); a outra vira os estilhaços',
    '      if (pv.get("estilhaco_some").getAsBoolean()) p.deleteFromScene(runtimeScene);',
    '      else { pv.get("estilhacar").setBoolean(false); pv.get("estilhaco_parede").setBoolean(false); }',
    '    }',
    '  }',
    '} catch (e) { /* sem estilhaços neste quadro: o tiro segue normal */ }',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def gv(d, nome):
    return next(v for v in d['variables'] if v['name'] == nome)


def migra(d):
    ids = Ids('t205')
    # --- saem ímã, incendiária e cadáver explosivo
    upg = gv(d, 'upgrades')
    upg['children'] = [c for c in upg['children'] if c['name'] not in SAEM]
    cat = gv(d, 'loja_catalogo')
    item = lambda it: {c['name']: c for c in it['children']}
    antes = len(cat['children'])
    cat['children'] = [it for it in cat['children'] if item(it)['id']['value'] not in SAEM]
    saiu = antes - len(cat['children'])
    pato = objeto(d, 'pato')
    pato['variables'] = [v for v in pato['variables'] if v['name'] not in VARS_PATO_SAEM]
    for o in next(g for g in d['objectsGroups'] if g['name'] == 'Inimigo')['objects']:
        ob = objeto(d, o['name'])
        ob['variables'] = [v for v in ob['variables'] if v['name'] not in ('queima', 'queima_tick')]

    com = folha(d, 'Combate')['events']
    morte = acha(com, 'Morte do Inimigo')['events'][0]
    por_inimigo = next(e for e in morte['events'] if e['type'].endswith('ForEach') and 'upgrades.vampirismo' in json.dumps(e))
    por_inimigo['events'] = [e for e in por_inimigo['events'] if 'upgrades.cadaver' not in json.dumps(e['conditions'])]
    ima = acha(com, 'Ímã e sumiço')['events'][0]
    c = next(c for c in ima['conditions'] if c['type']['value'] == 'Distance')
    assert c['parameters'][2] == 'moeda.iman_dist * (1 + pato.upg_ima * GlobalVariable(upgrades.ima))', c['parameters'][2]
    c['parameters'][2] = 'moeda.iman_dist'
    proj = acha(com, 'Projéteis')
    dano = acha(proj['events'], 'Dano da bala')['events'][0]
    dano['events'] = [e for e in dano['events'] if 'upgrades.incendiaria' not in json.dumps(e['conditions'])]
    proj['events'] = [e for e in proj['events'] if e.get('name') != 'Fogo da bala incendiária']
    for x in d['externalEvents'] + d['layouts']:
        s = json.dumps(x['events'])
        for k in ('upgrades.ima', 'upgrades.incendiaria', 'upgrades.cadaver', 'upg_ima', 'queima_tempo', 'cadaver_'):
            assert k not in s, (x['name'], k)

    # --- Estilhaços
    poe_vars(ids, upg['children'], 'upgrades', [('estilhaco', 0)])
    upg['children'].sort(key=lambda c: c['name'])
    entrou = 0
    if not any(item(it)['id']['value'] == 'estilhaco' for it in cat['children']):
        modelo = next(it for it in cat['children'] if item(it)['id']['value'] == 'vampirismo')
        it = copy.deepcopy(modelo)
        it['persistentUuid'] = ids('cat/estilhaco')
        for c in it['children']:
            c['persistentUuid'] = ids(f'cat/estilhaco/{c["name"]}')
            c['value'] = {'id': 'estilhaco', 'nome': 'Estilhacos', 'requer': '', 'preco_base': 200, 'preco_mult': 1.5,
                          'descricao': 'A bala que acerta vira 5 estilhacos que voam em volta; +dano dos estilhacos por nivel'
                          }.get(c['name'], c['value'])
        cat['children'].append(it)
        entrou = 1
    lin = gv(d, 'ui_m_lin_loja')['value']
    for nome in ('ui_rod_y', 'ui_m_h'):
        gv(d, nome)['value'] -= (saiu - entrou) * lin
    poe_vars(ids, pato['variables'], 'pato', ESTILHACO)
    poe_vars(ids, objeto(d, 'projetil')['variables'], 'projetil',
             [('fragmento', False), ('estilhacar', False), ('estilhaco_parede', False), ('estilhacou', False),
              ('estilhaco_some', False)])

    pode = [cmp(NIVEL, '>', '0'), bol('projetil', 'fragmento', False), num('projetil', 'raio', '<=', '0'),
            bol('projetil', 'estilhacou', False)]
    # no inimigo: o primeiro acerto marca a bala; se ela não atravessa mais, some nos estilhaços em vez de sumir aqui
    i = next(i for i, e in enumerate(dano['events'])
             if e['conditions'] == [num('projetil', 'furos', '<=', '0')] and e['actions'] == [X('Delete', 'projetil', '')])
    dano['events'][i]['conditions'].append(bol('projetil', 'estilhacar', False))
    dano['events'].insert(i + 1, ev([num('projetil', 'furos', '<=', '0'), bol('projetil', 'estilhacar', True)],
                                    [setb('projetil', 'estilhaco_some', True)]))
    dano['events'].insert(i, ev(pode, [setb('projetil', 'estilhacar', True), setb('projetil', 'estilhacou', True)]))
    # no terreno (depois do ricochete): a mesma faísca do impacto, e a bala é marcada em vez de sumir
    ter = acha(proj['events'], 'Balas no terreno')
    i = next(i for i, e in enumerate(ter['events'])
             if e['conditions'] and e['conditions'][0]['parameters'][:2] == ['projetil', 'Terreno'] and
             any(a['type']['value'] == 'Delete' for a in e['actions']))
    bate = ter['events'][i]
    bate['conditions'].append(bol('projetil', 'estilhacar', False))
    marca = ev([copy.deepcopy(bate['conditions'][0])] + pode,
               [copy.deepcopy(a) for a in bate['actions'] if a['type']['value'] != 'Delete'] +
               [setb('projetil', 'estilhacar', True), setb('projetil', 'estilhaco_parede', True),
                setb('projetil', 'estilhacou', True), setb('projetil', 'estilhaco_some', True)])
    ter['events'].insert(i, marca)
    proj['events'].append(grupo('Estilhaços', [js(ESTILHACA)]))

    # --- preços (só os que ainda estão no valor da t198)
    novos = {u: ((200, 2), (100, 1.5)) for u in BASICOS}
    novos.update({u: ((350, 2), (200, 1.5)) for u in EFEITOS})
    novos['laser'] = ((1500, 2), (800, 1.5))
    for it in cat['children']:
        c = item(it)
        u = c['id']['value']
        if u in novos and (c['preco_base']['value'], c['preco_mult']['value']) == novos[u][0]:
            c['preco_base']['value'], c['preco_mult']['value'] = novos[u][1]

    # --- moedas no começo
    m = gv(d, 'moedas_total')
    if m['value'] == 0:
        m['value'] = 300


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'estilhaco' for v in d['variables'] if v['name'] == 'upgrades'
                              for c in v['children']), 't205')
