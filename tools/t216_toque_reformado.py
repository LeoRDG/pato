"""Tarefa 216: reforma dos controles de toque (t215) e tela cheia no celular.

O que estava ruim na t215: posições em fração da LARGURA da tela (num celular 19.5:9 o jogo fica ~2400 px de largura
na HUD, então o botão de pulo ia parar no meio de baixo da tela, longe do polegar, e o dash quase no centro);
analógico da mira lá em cima à direita; o pulo dividia o polegar direito com a mira; alvos de toque pequenos
(raio 72 * 1.2) e desenho grande e opaco; pular pelo analógico só empurrando 60% para cima, sem histerese.

Esquema novo (tudo em toque.*, px da camada HUD, que tem sempre 1080 de altura):
- botões ancorados no canto de baixo à direita (distância da borda direita *_dir e de baixo *_baixo), em arco em
  volta do polegar direito: PULO grande logo acima da arma/munição, dash à esquerda, recarga em cima à esquerda e
  E em cima. A área de toque (pulo_toque, botao_toque) é bem maior que o desenho (pulo_raio, botao_raio); se duas
  áreas se cruzam, ganha o botão mais perto (em proporção do raio de toque).
- analógico de andar flutuante na metade esquerda (toque.mov_zona), descansando em mov_esq/mov_baixo; a base segue o
  dedo quando ele passa do raio (toque.segue), então voltar para o outro lado é imediato. Empurrar para cima também
  pula (toque.pulo_no_analogico, liga em pulo_limiar e solta em pulo_solta, para pular de novo no ar).
- analógico de mirar flutuante no resto da metade direita, descansando em mira_dir/mira_baixo: arrastar mira e atira
  além de tiro_limiar; segurar parado (sem arrastar) por mira_auto_espera atira no inimigo mais perto até
  mira_auto_alcance (toque.mira_auto; sem inimigo, atira para onde a mira está). Sem dedo na mira, ela vira para o
  lado em que o pato anda (toque.mira_segue_andar).
- analógicos parados ficam bem apagados (opacidade_repouso); o que está sendo tocado, forte (opacidade_ativa).
- tela cheia (toque.tela_cheia): no celular, cada toque que termina fora da tela cheia pede a tela cheia (a API só
  aceita isso num gesto do usuário, e o touchstart não conta) e trava em paisagem quando o navegador deixa.
Os eventos que leem teclas não mudam: continuam lendo toque.<ação> (t215). No computador nada muda.
Rodar uma vez:  python3 tools/t216_toque_reformado.py
"""
from gd_mig import *

PASTA_ART = 'assets/toque'
BOTOES = ['pulo', 'dash', 'recarga', 'usar']
NOVAS = [
    ('tela_cheia', True),
    ('opacidade_repouso', 70),
    # analógico de andar: descanso (px da borda esquerda e de baixo) e zona (fração da largura, da esquerda)
    ('mov_esq', 300), ('mov_baixo', 290), ('mov_zona', 0.5), ('segue', True),
    ('pulo_no_analogico', True), ('pulo_solta', 0.35),
    # analógico de mirar: descanso (px da borda direita e de baixo)
    ('mira_dir', 760), ('mira_baixo', 420),
    ('mira_auto', True), ('mira_auto_alcance', 1100), ('mira_auto_espera', 0.12), ('mira_segue_andar', True),
    # botões: centro (px da borda direita e de baixo), desenho (raio) e área de toque (raio)
    ('pulo_dir', 230), ('pulo_baixo', 330), ('pulo_raio', 95), ('pulo_toque', 165),
    ('dash_dir', 480), ('dash_baixo', 250),
    ('recarga_dir', 430), ('recarga_baixo', 530),
    ('usar_dir', 200), ('usar_baixo', 590),
    ('botao_toque', 120),
    # estado (o jogo escreve)
    ('pulo_analogico', False), ('mira_parado', 0), ('vx', 0), ('vy', 0), ('vd', 0), ('melhor', 1), ('qual', ''),
]
# posições da t215 em fração da tela: o esquema novo não usa mais
VELHAS = ['mov_x', 'mov_y', 'mira_x', 'mira_y', 'pulo_x', 'pulo_y', 'dash_x', 'dash_y', 'recarga_x', 'recarga_y',
          'usar_x', 'usar_y', 'folga']

T = 'toque'
ESQ = '(CameraX("HUD", 0) - CameraWidth("HUD", 0) / 2)'
DIR = '(CameraX("HUD", 0) + CameraWidth("HUD", 0) / 2)'
BAIXO = '(CameraY("HUD", 0) + CameraHeight("HUD", 0) / 2)'


def bx(b):  return f'{DIR} - {T}.{b}_dir'
def by(b):  return f'{BAIXO} - {T}.{b}_baixo'
def toque_raio(b): return f'{T}.pulo_toque' if b == 'pulo' else f'{T}.botao_toque'
def desenho_raio(b): return f'{T}.pulo_raio' if b == 'pulo' else f'{T}.botao_raio'


REPOUSO = {'mov': (f'{ESQ} + {T}.mov_esq', f'{BAIXO} - {T}.mov_baixo'),
           'mira': (bx('mira'), by('mira'))}


def ligado(): return cbol(f'{T}.ativo', True)
def tem_pato(): return cmp('SceneInstancesCount(pato)', '>', '0')
def setv(nome, v): return csetn(f'{T}.{nome}', '=', v)
def setbv(nome, v): return csetb(f'{T}.{nome}', v)
def bv(nome, v): return cbol(f'{T}.{nome}', v)
def opac(obj, v): return X('OpacityCapability::OpacityBehavior::SetValue', obj, 'Opacity', '=', v)
def tam(obj, v): return X('ResizableCapability::ResizableBehavior::SetSize', obj, 'Resizable', v, v)


def cria(obj, papel, x, y, tamanho, anim_=None, alfa=f'{T}.opacidade'):
    acoes = [X('Create', '', obj, x, y, '"HUD"'), sets(obj, 'papel', papel)]
    if anim_:
        acoes.append(anim(obj, anim_))
    acoes += [tam(obj, tamanho), opac(obj, alfa), X('ChangeColor', obj, f'{T}.cor')]
    return ev([], acoes)


TELA_CHEIA = [
    '// Tela cheia no celular (t216). O navegador só deixa pedir a tela cheia dentro de um gesto do usuário, e o',
    '// touchstart não conta (só o touchend): por isso o pedido sai do touchend, não de um evento do quadro.',
    '// Usa o setFullScreen do próprio GDevelop; a marca interna dele é acertada pelo estado real, para voltar à tela',
    '// cheia no próximo toque se o navegador sair dela (voltar, deslizar). Liga/desliga em toque.tela_cheia.',
    '// No iPhone o Safari não tem tela cheia para páginas: lá não acontece nada (Adicionar à Tela de Início).',
    'const S = gdjs._toqueTelaCheia || (gdjs._toqueTelaCheia = {});',
    'S.jogo = runtimeScene.getGame();',
    'if (!S.instalado) {',
    '  S.instalado = true;',
    '  const cheia = () => !!(document.fullscreenElement || document.webkitFullscreenElement);',
    '  const ligado = () => {',
    '    try {',
    '      const t = S.jogo.getVariables().get("toque");',
    '      return t.getChild("ativo").getAsBoolean() && t.getChild("tela_cheia").getAsBoolean();',
    '    } catch (e) { return false; }',
    '  };',
    '  const pode = () => { const el = document.documentElement; return !!(el.requestFullscreen || el.webkitRequestFullScreen); };',
    '  const trava = () => {',
    '    try { if (cheia() && screen.orientation && screen.orientation.lock) screen.orientation.lock("landscape").catch(() => {}); } catch (e) {}',
    '  };',
    '  const pede = () => {',
    '    if (!ligado() || cheia() || !pode()) return;',
    '    try {',
    '      const r = S.jogo.getRenderer();',
    '      r._isFullscreen = false;',
    '      r.setFullScreen(true);',
    '    } catch (e) {}',
    '  };',
    '  const mudou = () => { try { S.jogo.getRenderer()._isFullscreen = cheia(); } catch (e) {} trava(); };',
    '  document.addEventListener("touchend", pede, true);',
    '  document.addEventListener("fullscreenchange", mudou);',
    '  document.addEventListener("webkitfullscreenchange", mudou);',
    '  // pedido recusado: a marca do GDevelop volta a dizer a verdade',
    '  document.addEventListener("fullscreenerror", mudou);',
    '}',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': list(linhas), 'parameterObjects': '',
            'useStrict': True, 'eventsSheetExpanded': False}


def eventos():
    G = []
    # --- liga/desliga e cria os controles ---
    G.append(ev([X('DepartScene', '')],
                [setbv('ativo', False), setv('mov_id', '-1'), setv('mira_id', '-1'), setbv('pulo_analogico', False),
                 setv('mira_parado', '0')] + [setv(f'{b}_id', '-1') for b in BOTOES],
                [ev([OU(X('SystemInfo::IsMobile', ''), bv('forcar', True))], [setbv('ativo', True)]),
                 ev([ligado(), tem_pato()], [],
                    [cria('toque_base', 'mov', *REPOUSO['mov'], f'{T}.mov_raio * 2', 'base', f'{T}.opacidade_repouso'),
                     cria('toque_alavanca', 'mov', *REPOUSO['mov'], f'{T}.mov_raio', None, f'{T}.opacidade_repouso'),
                     cria('toque_base', 'mira', *REPOUSO['mira'], f'{T}.mira_raio * 2', 'mira', f'{T}.opacidade_repouso'),
                     cria('toque_alavanca', 'mira', *REPOUSO['mira'], f'{T}.mira_raio', None, f'{T}.opacidade_repouso')]
                    + [cria('toque_botao', b, bx(b), by(b), f'{desenho_raio(b)} * 2', b) for b in BOTOES])]))
    G.append(ev([ligado()], [], [js(TELA_CHEIA)]))

    q = []
    # dentro da loja o toque move o mouse (a loja é por clique); fora dela não (o dedo não pode mexer na mira)
    q.append(cada('pato', [bol('pato', 'na_loja', True)], [X('TouchSimulateMouse', '', 'yes')]))
    q.append(cada('pato', [bol('pato', 'na_loja', False)], [X('TouchSimulateMouse', '', 'no')]))
    # toques que acabaram
    for nome in ['mov', 'mira'] + BOTOES:
        extra = [setv(f'{nome}_dx', '0'), setv(f'{nome}_dy', '0')] if nome in ('mov', 'mira') else []
        q.append(ev([cmp(f'{T}.{nome}_id', '!=', '-1'), X('HasTouchEnded', '', f'{T}.{nome}_id')],
                    [setv(f'{nome}_id', '-1')] + extra))
    # analógico solto volta ao lugar de descanso (ancorado na borda: vale para qualquer largura de tela)
    for nome in ('mov', 'mira'):
        q.append(ev([cmp(f'{T}.{nome}_id', '=', '-1')],
                    [setv(f'{nome}_bx', REPOUSO[nome][0]), setv(f'{nome}_by', REPOUSO[nome][1]),
                     setv(f'{nome}_dx', '0'), setv(f'{nome}_dy', '0')]))
    # toques novos: o botão mais perto (dentro da área de toque), senão um dos analógicos
    q.append(ev([], [setv('i', '0')]))
    novo = [ev([], [setv('id', f'StartedTouchOrMouseId({T}.i)'),
                    setv('tx', f'TouchX({T}.id, "HUD", 0)'), setv('ty', f'TouchY({T}.id, "HUD", 0)'),
                    setbv('livre', True), setv('melhor', '1'), X('SetStringVariable', f'{T}.qual', '=', '""')])]
    for b in BOTOES:
        rel = f'DistanceBetweenPositions({T}.tx, {T}.ty, {bx(b)}, {by(b)}) / {toque_raio(b)}'
        novo.append(ev([cmp(rel, '<', f'{T}.melhor')],
                       [setv('melhor', rel), X('SetStringVariable', f'{T}.qual', '=', f'"{b}"')]))
    for b in BOTOES:
        novo.append(ev([X('StringVariable', f'{T}.qual', '=', f'"{b}"')], [setv(f'{b}_id', f'{T}.id'), setbv('livre', False)]))
    meio = f'{ESQ} + CameraWidth("HUD", 0) * {T}.mov_zona'
    novo.append(ev([bv('livre', True), cmp(f'{T}.tx', '<', meio), cmp(f'{T}.mov_id', '=', '-1')],
                   [setv('mov_id', f'{T}.id'), setv('mov_bx', f'{T}.tx'), setv('mov_by', f'{T}.ty'), setbv('livre', False)]))
    novo.append(ev([bv('livre', True), cmp(f'{T}.tx', '>=', meio), cmp(f'{T}.mira_id', '=', '-1')],
                   [setv('mira_id', f'{T}.id'), setv('mira_bx', f'{T}.tx'), setv('mira_by', f'{T}.ty'),
                    setv('mira_parado', '0'), setbv('livre', False)]))
    novo.append(ev([], [csetn(f'{T}.i', '+', '1')]))
    q.append(repete('StartedTouchOrMouseCount()', [], novo))
    # analógicos: vetor de -1 a 1; passando do raio a base vem atrás do dedo (toque.segue)
    for nome in ('mov', 'mira'):
        r = f'{T}.{nome}_raio'
        q.append(ev([cmp(f'{T}.{nome}_id', '!=', '-1')],
                    [setv('vx', f'TouchX({T}.{nome}_id, "HUD", 0) - {T}.{nome}_bx'),
                     setv('vy', f'TouchY({T}.{nome}_id, "HUD", 0) - {T}.{nome}_by'),
                     setv('vd', f'max(sqrt({T}.vx * {T}.vx + {T}.vy * {T}.vy), 0.001)')],
                    [ev([bv('segue', True), cmp(f'{T}.vd', '>', r)],
                        [csetn(f'{T}.{nome}_bx', '+', f'{T}.vx * (1 - {r} / {T}.vd)'),
                         csetn(f'{T}.{nome}_by', '+', f'{T}.vy * (1 - {r} / {T}.vd)')]),
                     ev([], [setv(f'{nome}_dx', f'{T}.vx * min({T}.vd, {r}) / {T}.vd / {r}'),
                             setv(f'{nome}_dy', f'{T}.vy * min({T}.vd, {r}) / {T}.vd / {r}')])]))
    # ações
    q.append(ev([], [setbv(n, False) for n in ('esquerda', 'direita', 'cima', 'baixo', 'pulo', 'dash', 'recarga',
                                               'usar', 'tiro')]))
    q.append(ev([cmp(f'{T}.mov_dx', '<', f'-{T}.zona_morta')], [setbv('esquerda', True)]))
    q.append(ev([cmp(f'{T}.mov_dx', '>', f'{T}.zona_morta')], [setbv('direita', True)]))
    q.append(ev([cmp(f'{T}.mov_dy', '<', f'-{T}.pulo_limiar')], [setbv('cima', True)]))
    q.append(ev([cmp(f'{T}.mov_dy', '>', f'{T}.baixo_limiar')], [setbv('baixo', True)]))
    # pulo pelo analógico: liga em pulo_limiar, solta em pulo_solta (para pular de novo no ar)
    q.append(ev([bv('pulo_no_analogico', True), cmp(f'{T}.mov_id', '!=', '-1'),
                 cmp(f'{T}.mov_dy', '<', f'-{T}.pulo_limiar')], [setbv('pulo_analogico', True)]))
    q.append(ev([cmp(f'{T}.mov_dy', '>', f'-{T}.pulo_solta')], [setbv('pulo_analogico', False)]))
    q.append(ev([bv('pulo_no_analogico', False)], [setbv('pulo_analogico', False)]))
    q.append(ev([bv('pulo_analogico', True)], [setbv('pulo', True)]))
    for b in BOTOES:
        q.append(ev([cmp(f'{T}.{b}_id', '!=', '-1')], [setbv(b, True)]))
    for b in ('pulo', 'dash', 'usar'):
        q.append(ev([], [setbv(f'{b}_agora', False)]))
        q.append(ev([bv(b, True), bv(f'{b}_antes', False)], [setbv(f'{b}_agora', True)]))
        q.append(ev([], [setbv(f'{b}_antes', False)]))
        q.append(ev([bv(b, True)], [setbv(f'{b}_antes', True)]))
    # mira: arrastar mira (e atira além de tiro_limiar); segurar parado atira no inimigo mais perto
    mag = f'sqrt({T}.mira_dx * {T}.mira_dx + {T}.mira_dy * {T}.mira_dy)'
    q.append(ev([cmp(f'{T}.mira_id', '!=', '-1'), cmp(mag, '>', f'{T}.zona_morta')],
                [setv('mira_ang', f'atan2({T}.mira_dy, {T}.mira_dx)'), setv('mira_parado', '0')]))
    q.append(ev([cmp(f'{T}.mira_id', '!=', '-1'), cmp(mag, '>', f'{T}.tiro_limiar')], [setbv('tiro', True)]))
    q.append(ev([cmp(f'{T}.mira_id', '!=', '-1'), cmp(mag, '<=', f'{T}.zona_morta')],
                [csetn(f'{T}.mira_parado', '+', 'TimeDelta()')]))
    q.append(ev([cmp(f'{T}.mira_id', '=', '-1')], [setv('mira_parado', '0')]))
    boca_y = 'pato.Y() + pato.Height() * 0.68'
    q.append(ev([cmp(f'{T}.mira_id', '!=', '-1'), cmp(mag, '<=', f'{T}.zona_morta'),
                 cmp(f'{T}.mira_parado', '>=', f'{T}.mira_auto_espera')], [setbv('tiro', True)],
                [ev([bv('mira_auto', True), X('PickNearest', 'Inimigo', 'pato.CenterX()', boca_y, ''),
                     cmp(f'DistanceBetweenPositions(Inimigo.CenterX(), Inimigo.CenterY(), pato.CenterX(), {boca_y})',
                         '<=', f'{T}.mira_auto_alcance')],
                    [setv('mira_ang', f'atan2(Inimigo.CenterY() - ({boca_y}), Inimigo.CenterX() - pato.CenterX())')])]))
    # sem dedo na mira, ela vira para o lado em que o pato anda
    vira = setv('mira_ang', f'atan2(sin({T}.mira_ang), -cos({T}.mira_ang))')
    q.append(ev([cmp(f'{T}.mira_id', '=', '-1'), bv('mira_segue_andar', True), bv('esquerda', True),
                 cmp(f'cos({T}.mira_ang)', '>', '0')], [vira]))
    q.append(ev([cmp(f'{T}.mira_id', '=', '-1'), bv('mira_segue_andar', True), bv('direita', True),
                 cmp(f'cos({T}.mira_ang)', '<', '0')], [vira]))
    # desenho: base e alavanca seguem o dedo; parado fica apagado, tocado fica forte; botão apertado fica forte
    for nome in ('mov', 'mira'):
        q.append(ev([txt('toque_base', 'papel', nome)],
                    [X('SetXY', 'toque_base', '=', f'{T}.{nome}_bx', '=', f'{T}.{nome}_by'),
                     tam('toque_base', f'{T}.{nome}_raio * 2'), opac('toque_base', f'{T}.opacidade_repouso')]))
        q.append(ev([txt('toque_alavanca', 'papel', nome)],
                    [X('SetXY', 'toque_alavanca', '=', f'{T}.{nome}_bx + {T}.{nome}_dx * {T}.{nome}_raio',
                       '=', f'{T}.{nome}_by + {T}.{nome}_dy * {T}.{nome}_raio'),
                     tam('toque_alavanca', f'{T}.{nome}_raio'), opac('toque_alavanca', f'{T}.opacidade_repouso')]))
        q.append(ev([cmp(f'{T}.{nome}_id', '!=', '-1'), txt('toque_base', 'papel', nome)],
                    [opac('toque_base', f'{T}.opacidade_ativa')]))
        q.append(ev([cmp(f'{T}.{nome}_id', '!=', '-1'), txt('toque_alavanca', 'papel', nome)],
                    [opac('toque_alavanca', f'{T}.opacidade_ativa')]))
    q.append(ev([], [opac('toque_botao', f'{T}.opacidade')]))
    for b in BOTOES:
        q.append(ev([txt('toque_botao', 'papel', b)],
                    [X('SetXY', 'toque_botao', '=', bx(b), '=', by(b)), tam('toque_botao', f'{desenho_raio(b)} * 2')]))
        q.append(ev([bv(b, True), txt('toque_botao', 'papel', b)], [opac('toque_botao', f'{T}.opacidade_ativa')]))
    q.append(cada('pato', [bol('pato', 'na_loja', True)], [X('Hide', 'toque_base'), X('Hide', 'toque_alavanca')]))
    q.append(cada('pato', [bol('pato', 'na_loja', False)], [X('Show', 'toque_base'), X('Show', 'toque_alavanca')]))
    G.append(ev([ligado(), tem_pato()], [], q))
    # cenas sem o pato (Resultado): o toque volta a ser clique, para tocar e continuar
    G.append(ev([ligado(), cmp('SceneInstancesCount(pato)', '=', '0')], [X('TouchSimulateMouse', '', 'yes')]))

    # --- ponto de mira: mouse no computador; com o toque, na direção toque.mira_ang, a mira_dist do pato ---
    G.append(ev([bv('ativo', False)], [csetn('mira_x', '=', 'MouseX()'), csetn('mira_y', '=', 'MouseY()')]))
    G.append(ev([ligado(), tem_pato()],
                [csetn('mira_x', '=', f'pato.CenterX() + cos({T}.mira_ang) * {T}.mira_dist'),
                 csetn('mira_y', '=', f'{boca_y} + sin({T}.mira_ang) * {T}.mira_dist')]))
    return [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Controles de toque (t215, reformados na t216): ligam no celular (ou com toque.forcar). Botões em arco '
                    'no canto de baixo à direita (pulo grande, dash, recarga, E), ancorados na borda (*_dir, *_baixo em px '
                    'da HUD), área de toque maior que o desenho. Analógico esquerdo anda (para cima também pula), direito '
                    'mira e atira; segurar parado nele atira no inimigo mais perto (mira_auto). Tela cheia no primeiro '
                    'toque (tela_cheia). Números em toque.*. As condições de tecla aceitam também toque.<ação>.'}] + G


def OU(*conds):
    return {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': list(conds)}


def migra(d):
    ids = Ids('t216')
    # arte nova (tools/arte_toque.py): a base da mira ganha a cruz
    if not any(r['name'] == f'{PASTA_ART}/base_mira.png' for r in d['resources']['resources']):
        d['resources']['resources'].append(dict(recurso(f'{PASTA_ART}/base_mira.png'), smoothed=True))
    base = objeto(d, 'toque_base')
    if not any(a['name'] == 'mira' for a in base['animations']):
        nova = json.loads(json.dumps(base['animations'][0]))
        nova['name'] = 'mira'
        nova['directions'][0]['sprites'][0]['image'] = f'{PASTA_ART}/base_mira.png'
        base['animations'].append(nova)

    toque = next(v for v in d['variables'] if v['name'] == T)
    toque['children'] = [c for c in toque['children'] if c['name'] not in VELHAS]
    poe_vars(ids, toque['children'], 'global/toque', NOVAS)

    grupo_ = acha(folha(d, 'Jogador')['events'], 'Toque (celular)')
    assert grupo_['events'][0]['comment'].startswith('Controles de toque (t215)'), 'o grupo do toque mudou desde a t215'
    grupo_['events'] = eventos()


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'tela_cheia' for v in d['variables'] if v['name'] == T
                              for c in v['children']), 't216')
