"""Tarefa 206: placar de cada fase no hub, em cima do portal dela.
- Os três portais dos hubs ficam lado a lado no chão (Inferno, Purgatório, Paraíso, da esquerda para a direita), e as duas
  plataformas que seguravam os portais de cima saem do tilemap (a parede volta a ser lisa). Só muda o portal/tile que ainda
  está onde a t122 deixou; se o usuário já mexeu, fica como está.
- Nos hubs, ficar em cima do portal não leva mais à fase: é preciso apertar E (variável do portal entrar_com_e, ligada nas
  instâncias dos hubs). Os portais das fases continuam como eram.
- Com o pato em cima de um portal do hub, aparecem acima dele duas caixas pretas: MAIS RAPIDOS e MAIS PONTOS daquela fase
  (hub_placar.top_n linhas, o nome do jogador em dourado), com o recorde local embaixo e "[E] ENTRAR NO ..." acima.
  Os placares vêm do placar global (GET placar_url), pedidos quando o pato sobe no portal e guardados por
  hub_placar.recarga s. Sem placar global (desligado, fora do ar) as caixas dizem isso e mostram o recorde local.
- Tamanhos e distâncias em hub_placar.*, cores ui_cor_*. Objetos próprios hub_placar_txt e hub_placar_fundo.
Rodar uma vez:  python3 tools/t206_placar_no_hub.py
"""
import copy
from gd_mig import *

HUBS = ('Hub', 'HubPurgatorio', 'HubParaiso')
# onde a t122 deixou -> onde ficam (x, y do canto do portal)
PORTAIS = {'Inferno': ((2261, 787), (1620, 787)), 'Purgatorio': ((2260, 506), (1930, 787)),
           'Paraiso': ((2257, 227), (2240, 787))}
# plataformas: linhas 17 e 21, colunas 46..53 (77 e depois 89 ou 55); a coluna 54 é a parede (78 vira 68)
PLATAFORMAS = {17: [77] + [89] * 7, 21: [77] + [55] * 7}

CAIXA = [
    ('top_n', 5), ('recarga', 60), ('caixa_w', 460), ('gap', 24), ('pad', 22), ('lin_h', 36), ('tam_titulo', 24),
    ('tam_linha', 24), ('tam_dica', 26), ('col_nome_x', 58), ('acima', 70), ('dica_gap', 18), ('opacidade', 235),
]

PLACAR = [
    'try {',
    '  // Placar no portal (t206): com o pato em cima de um portal do hub, duas caixas com os placares da fase dele.',
    '  const jogo = runtimeScene.getGame();',
    '  const V = jogo.getVariables();',
    '  const T = V.get("hub_placar");',
    '  const n = (k) => T.getChild(k).getAsNumber();',
    '  const cor = (k) => V.get(k).getAsString();',
    '  const limpa = (s) => String(s).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toUpperCase();',
    '  const tempo = (s) => { const m = Math.floor(s / 60); return String(m).padStart(2, "0") + ":" + (s - m * 60).toFixed(2).padStart(5, "0"); };',
    '  const pts = (v) => Math.round(v).toLocaleString("pt-BR");',
    '  // cada chegada ao hub pede os placares de novo (a corrida que acabou de terminar já aparece)',
    '  if (!runtimeScene.__hubPlacar) jogo.__hubPlacar = {};',
    '  const st = runtimeScene.__hubPlacar || (runtimeScene.__hubPlacar = { textos: {}, fundo: null });',
    '  const cache = jogo.__hubPlacar || (jogo.__hubPlacar = {});',
    '  const usados = new Set();',
    '  const txt = (id, s, x, y, tam, c, alinha) => {',
    '    let o = st.textos[id];',
    '    if (!o) { o = runtimeScene.createObject("hub_placar_txt"); o.setLayer(""); o.setZOrder(100000); st.textos[id] = o; }',
    '    usados.add(id);',
    '    o.setString(limpa(s));',
    '    o.setCharacterSize(tam);',
    '    o.setColor(c);',
    '    o.hide(false);',
    '    o.setX(alinha === "dir" ? x - o.getWidth() : alinha === "meio" ? x - o.getWidth() / 2 : x);',
    '    o.setY(y);',
    '    return o;',
    '  };',
    '  if (!st.fundo) { st.fundo = runtimeScene.createObject("hub_placar_fundo"); st.fundo.setLayer(""); st.fundo.setZOrder(99999); }',
    '  const fundo = st.fundo;',
    '  fundo.clear();',
    '  const pato = runtimeScene.getObjects("pato")[0];',
    '  const sobre = (a, b) => { const A = a.getAABB(), B = b.getAABB(); return A.min[0] < B.max[0] && A.max[0] > B.min[0] && A.min[1] < B.max[1] && A.max[1] > B.min[1]; };',
    '  const portal = pato && !pato.getVariables().get("morto").getAsBoolean()',
    '    ? runtimeScene.getObjects("portal").find((p) => p.getVariables().get("entrar_com_e").getAsBoolean() && sobre(pato, p)) : null;',
    '  if (portal) {',
    '    const fase = portal.getVariables().get("cena").getAsString();',
    '    const url = V.get("placar_url").getAsString();',
    '    // placares da fase: pede de novo depois de hub_placar.recarga s',
    '    const c = cache[fase] || (cache[fase] = { t: -Infinity, tempo: null, pontos: null, pedindo: false });',
    '    const agora = Date.now();',
    '    if (url && !c.pedindo && agora - c.t > n("recarga") * 1000) {',
    '      c.pedindo = true;',
    '      const pede = (tipo) => {',
    '        const lim = typeof AbortSignal !== "undefined" && AbortSignal.timeout ? { signal: AbortSignal.timeout(8000) } : {};',
    '        return fetch(url + "?nivel=" + encodeURIComponent(fase) + "&tipo=" + tipo + "&n=" + n("top_n"), lim)',
    '          .then((r) => r.json()).then((j) => (j && Array.isArray(j.linhas) ? j.linhas : null)).catch(() => null);',
    '      };',
    '      Promise.all([pede("tempo"), pede("pontos")]).then(([a, b]) => { c.tempo = a; c.pontos = b; })',
    '        .catch(() => { c.tempo = null; c.pontos = null; })',
    '        .then(() => { c.t = Date.now(); c.pedindo = false; });',
    '    }',
    '    const nome = V.get("jogador_nome").getAsString();',
    '    const R = V.get("recordes");',
    '    const local = R.hasChild(fase) ? R.getChild(fase).toJSObject() : {};',
    '    // caixas lado a lado, centradas no portal e dentro da tela',
    '    const L = runtimeScene.getLayer("");',
    '    const zoom = L.getCameraZoom();',
    '    const vw = jogo.getGameResolutionWidth() / zoom;',
    '    const cw = n("caixa_w"), gap = n("gap"), pad = n("pad"), lh = n("lin_h");',
    '    const total = cw * 2 + gap;',
    '    const linhas = n("top_n");',
    '    const ch = pad * 2 + n("tam_titulo") + lh * 0.5 + lh * (linhas + 1);',
    '    let x0 = portal.getCenterXInScene() - total / 2;',
    '    const cx0 = L.getCameraX() - vw / 2, cx1 = L.getCameraX() + vw / 2;',
    '    // não passa do último portal (depois dele vem a parede) nem sai da tela',
    '    const fimPortais = Math.max(...runtimeScene.getObjects("portal").filter((p) => p.getVariables().get("entrar_com_e").getAsBoolean()).map((p) => p.getX() + p.getWidth()));',
    '    x0 = Math.max(cx0 + pad, Math.min(x0, cx1 - pad - total, fimPortais + pad - total));',
    '    const y1 = portal.getY() - n("acima");',
    '    const y0 = y1 - ch;',
    '    fundo.setFillColor(cor("ui_cor_fundo"));',
    '    fundo.setFillOpacity(n("opacidade"));',
    '    fundo.setOutlineSize(0);',
    '    const caixa = (bx, id, titulo, lista, valor) => {',
    '      fundo.drawRectangle(bx, y0, bx + cw, y0 + ch);',
    '      let yy = y0 + pad;',
    '      txt(id + "_t", titulo, bx + pad, yy, n("tam_titulo"), cor("ui_cor_ouro"));',
    '      yy += n("tam_titulo") + lh * 0.5;',
    '      const linha = (k, a, b, v, c1, c2) => {',
    '        txt(id + "_p" + k, a, bx + pad, yy, n("tam_linha"), c2 || c1);',
    '        txt(id + "_n" + k, b, bx + pad + n("col_nome_x"), yy, n("tam_linha"), c1);',
    '        txt(id + "_v" + k, v, bx + cw - pad, yy, n("tam_linha"), c1, "dir");',
    '        yy += lh;',
    '      };',
    '      if (!url) txt(id + "_m", "PLACAR GLOBAL DESLIGADO", bx + pad, yy, n("tam_linha"), cor("ui_cor_dim"));',
    '      else if (!lista && c.t === -Infinity) txt(id + "_m", "CARREGANDO...", bx + pad, yy, n("tam_linha"), cor("ui_cor_dim"));',
    '      else if (!lista) txt(id + "_m", "PLACAR FORA DO AR", bx + pad, yy, n("tam_linha"), cor("ui_cor_dim"));',
    '      else if (!lista.length) txt(id + "_m", "NINGUEM AINDA", bx + pad, yy, n("tam_linha"), cor("ui_cor_dim"));',
    '      else lista.slice(0, linhas).forEach((l, i) => {',
    '        const eu = nome && l.nome === nome;',
    '        linha(i, "#" + l.posicao, l.nome, valor(l), eu ? cor("ui_cor_ouro") : cor("ui_cor_texto"), eu ? cor("ui_cor_ouro") : cor("ui_cor_dim"));',
    '      });',
    '      // o recorde local na última linha da caixa',
    '      yy = y0 + ch - pad - lh + (lh - n("tam_linha")) / 2;',
    '      const rec = id === "t" ? (local.tempo > 0 ? tempo(local.tempo) : "-") : (local.pontos > 0 ? pts(local.pontos) : "-");',
    '      txt(id + "_rl", "SEU RECORDE", bx + pad, yy, n("tam_linha"), cor("ui_cor_rotulo"));',
    '      txt(id + "_rv", rec, bx + cw - pad, yy, n("tam_linha"), cor("ui_cor_texto"), "dir");',
    '    };',
    '    caixa(x0, "t", "MAIS RAPIDOS", c.tempo, (l) => tempo(l.tempo));',
    '    caixa(x0 + cw + gap, "p", "MAIS PONTOS", c.pontos, (l) => pts(l.pontos));',
    '    const fx = V.get("placar_niveis");',
    '    const titulo = fx.hasChild(fase) && fx.getChild(fase).hasChild("nome") ? fx.getChild(fase).getChild("nome").getAsString() : fase;',
    '    // a dica fica acima das caixas (embaixo delas está o nome do portal)',
    '    txt("dica", "[E] ENTRAR NO " + titulo, x0 + total / 2, y0 - n("dica_gap") - n("tam_dica"), n("tam_dica"), cor("ui_cor_creme"), "meio");',
    '  }',
    '  for (const id in st.textos) if (!usados.has(id)) st.textos[id].hide(true);',
    '} catch (e) { /* o placar do hub nunca trava o jogo */ }',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def migra(d):
    ids = Ids('t206')
    if not any(v['name'] == 'hub_placar' for v in d['variables']):
        d['variables'].append({'name': 'hub_placar', 'persistentUuid': ids('var/global/hub_placar'), 'type': 'structure',
                               'children': [var(ids, 'global/hub_placar', k, v) for k, v in CAIXA]})
    if not objeto(d, 'hub_placar_txt'):
        o = copy.deepcopy(objeto(d, 'ui_txt'))
        o.update(name='hub_placar_txt', persistentUuid=ids('obj/hub_placar_txt'), variables=[], string='')
        poe_objeto(d, o, 'ui')
    if not objeto(d, 'hub_placar_fundo'):
        o = copy.deepcopy(objeto(d, 'ui_fundo_mundo'))
        o.update(name='hub_placar_fundo', persistentUuid=ids('obj/hub_placar_fundo'), variables=[])
        poe_objeto(d, o, 'ui')
    poe_vars(ids, objeto(d, 'portal')['variables'], 'portal', [('entrar_com_e', False)])

    for h in HUBS:
        l = cena(d, h)
        for i in l['instances']:
            if i['name'] != 'portal':
                continue
            iv = i.setdefault('initialVariables', [])
            fase = next(v['value'] for v in iv if v['name'] == 'cena')
            if not any(v['name'] == 'entrar_com_e' for v in iv):
                iv.append({'name': 'entrar_com_e', 'type': 'boolean', 'value': True})
            antes, depois = PORTAIS[fase]
            if (round(i['x']), round(i['y'])) == antes:
                i['x'], i['y'] = depois
        tm = next(i for i in l['instances'] if i['name'].startswith('tiles_'))
        prop = tm['stringProperties'][0]
        t = json.loads(prop['value'])
        T = t['layers'][0]['tiles']
        for r, esperado in PLATAFORMAS.items():
            if T[r][46:54] == esperado and T[r][54] == 78:
                T[r][46:54] = [-1] * 8
                T[r][54] = 68
        prop['value'] = json.dumps(t, separators=(',', ':'))

    # E para entrar nos portais do hub; os outros portais continuam entrando sozinhos
    entra = acha(folha(d, 'Portais')['events'], 'Entrar no portal')
    auto = entra['events'][1]
    assert auto['type'].endswith('ForEach')
    assert any(a['type']['value'] == 'Scene' for a in auto['actions'])
    auto['conditions'].append(bol('portal', 'entrar_com_e', False))
    entra['events'].insert(2, cada('portal', [
        X('CollisionNP', 'pato', 'portal', '', '', ''), bol('portal', 'entrar_com_e', True),
        X('KeyFromTextJustPressed', '', '"e"'), bol('pato', 'morto', False), bol('pato', 'na_loja', False),
        bol('portal', 'aberto', True)], [X('Scene', '', 'portal.cena', '')]))

    folha(d, 'Hubs')['events'].append(grupo('Placar no portal', [js(PLACAR)]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'hub_placar' for v in d['variables']), 't206')
