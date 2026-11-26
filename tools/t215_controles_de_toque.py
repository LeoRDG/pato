"""Tarefa 215: controles de toque para jogar no navegador do celular, feitos com eventos do GDevelop.

Liga sozinho no celular (condição "é um dispositivo móvel") ou com a variável global toque.forcar (para testar no
computador; o clique do mouse vira um toque). Na camada HUD de cada cena com o pato aparecem:
- analógico da esquerda (metade esquerda da tela, a base vai para onde o dedo encosta): anda; empurrar para cima
  pula (toque.pulo_limiar), para baixo é o "s" (desce no voo do Paraíso);
- analógico da direita (metade direita, fora dos botões): mira para onde aponta e atira com ele empurrado além de
  toque.tiro_limiar; soltando, a mira fica onde estava;
- botões pulo, dash, recarga e usar (E: portal, loja, pegar a arma no pedestal do hub; nas fases a troca de
  arma por 1-4 está desligada desde a t186, então não há botão de troca).
Posições em fração da tela (toque.*_x, toque.*_y), tamanhos em px da HUD, cor e opacidades em toque.*.
Os eventos que liam teclas passam a aceitar também o toque: cada condição de tecla vira "tecla OU toque.<ação>"
(a, d, Space, LShift, r, w, s, e e o botão esquerdo do mouse do tiro). A mira passa a ler mira_x/mira_y (o mouse
no computador, o analógico no celular). Com o toque ligado, o toque só move o mouse dentro da loja (lá a loja é por
toque/clique); fora dela o primeiro dedo não mexe mais na mira. Nas cenas sem
o pato (Resultado) o toque volta a ser clique.
Rodar uma vez:  python3 tools/t215_controles_de_toque.py
"""
import re
from gd_mig import *

PASTA_ART = 'assets/toque'
BOTOES = ['pulo', 'dash', 'recarga', 'usar']
TOQUE = [
    ('forcar', False), ('ativo', False),
    ('cor', '255;255;255'), ('opacidade', 150), ('opacidade_ativa', 235),
    # analógico de andar
    ('mov_x', 0.12), ('mov_y', 0.74), ('mov_raio', 130), ('zona_morta', 0.3), ('pulo_limiar', 0.6), ('baixo_limiar', 0.6),
    # analógico de mirar e atirar
    ('mira_x', 0.78), ('mira_y', 0.40), ('mira_raio', 130), ('tiro_limiar', 0.35), ('mira_dist', 320),
    # botões (centro em fração da tela, raio em px; o toque vale até raio * folga)
    ('pulo_x', 0.68), ('pulo_y', 0.84), ('dash_x', 0.57), ('dash_y', 0.89),
    ('recarga_x', 0.93), ('recarga_y', 0.64), ('usar_x', 0.84), ('usar_y', 0.64),
    ('botao_raio', 72), ('folga', 1.2),
    # estado (o jogo escreve)
    ('mov_id', -1), ('mira_id', -1), ('pulo_id', -1), ('dash_id', -1), ('recarga_id', -1), ('usar_id', -1),
    ('mov_bx', 0), ('mov_by', 0), ('mira_bx', 0), ('mira_by', 0), ('mov_dx', 0), ('mov_dy', 0),
    ('mira_dx', 0), ('mira_dy', 0), ('mira_ang', 0), ('i', 0), ('id', -1), ('tx', 0), ('ty', 0), ('livre', False),
    ('esquerda', False), ('direita', False), ('cima', False), ('baixo', False),
    ('pulo', False), ('pulo_agora', False), ('pulo_antes', False),
    ('dash', False), ('dash_agora', False), ('dash_antes', False),
    ('recarga', False), ('usar', False), ('usar_agora', False), ('usar_antes', False), ('tiro', False),
    
]
# tecla (condição) -> ação do toque
SEGURA = {'"a"': 'esquerda', '"d"': 'direita', '"Space"': 'pulo', '"LShift"': 'dash', '"r"': 'recarga',
          '"w"': 'cima', '"s"': 'baixo'}
APERTOU = {'"Space"': 'pulo_agora', '"LShift"': 'dash_agora', '"e"': 'usar_agora'}
FOLHAS = ['Jogador', 'Portais', 'Hubs']        # o "e" da Loja abre/fecha: só a condição dele entra (abaixo)

T = 'toque'
L = f'(CameraX("HUD", 0) - CameraWidth("HUD", 0) / 2)'
TOPO = f'(CameraY("HUD", 0) - CameraHeight("HUD", 0) / 2)'


def px(f):  return f'{L} + {T}.{f} * CameraWidth("HUD", 0)'
def py(f):  return f'{TOPO} + {T}.{f} * CameraHeight("HUD", 0)'
def ligado(): return cbol(f'{T}.ativo', True)
def tem_pato(): return cmp('SceneInstancesCount(pato)', '>', '0')
def setv(nome, v): return csetn(f'{T}.{nome}', '=', v)
def setbv(nome, v): return csetb(f'{T}.{nome}', v)
def bv(nome, v): return cbol(f'{T}.{nome}', v)


def OU(*conds):
    return {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': list(conds)}


def embrulha(conds, folha_inteira=True, so=None):
    """troca cada condição de tecla mapeada por (tecla OU toque.ação); devolve quantas trocou."""
    n = 0
    for k, c in enumerate(conds):
        t, p = c['type']['value'], c['parameters']
        if c['type'].get('inverted') or len(p) < 2:
            continue
        acao = None
        if t == 'KeyFromTextPressed':
            acao = SEGURA.get(p[1])
        elif t == 'KeyFromTextJustPressed':
            acao = APERTOU.get(p[1])
        elif t == 'MouseButtonFromTextPressed' and p[1] == '"Left"' and folha_inteira:
            acao = 'tiro'
        if acao and (so is None or p[1] in so):
            conds[k] = OU(c, bv(acao, True))
            n += 1
    return n


def percorre(evs, f):
    for e in evs:
        f(e)
        percorre(e.get('events') or [], f)


def objetos(d, ids):
    poe_recursos(d, [])
    for nome in ['base', 'alavanca'] + [f'botao_{b}' for b in BOTOES]:
        c = f'{PASTA_ART}/{nome}.png'
        if not any(r['name'] == c for r in d['resources']['resources']):
            d['resources']['resources'].append(dict(recurso(c), smoothed=True))
    def centro(o):
        for a in o['animations']:
            for q in a['directions'][0]['sprites']:
                q['originPoint'].update(x=128, y=128)
        return o
    papel = [var(ids, 'toque_obj', 'papel', '')]
    poe_objeto(d, centro(sprite(ids, 'toque_base', [('base', [f'{PASTA_ART}/base.png'], 1, 0.1, False)], papel)), 'toque')
    poe_objeto(d, centro(sprite(ids, 'toque_alavanca', [('alavanca', [f'{PASTA_ART}/alavanca.png'], 1, 0.1, False)],
                                [var(ids, 'toque_alavanca', 'papel', '')])), 'toque')
    poe_objeto(d, centro(sprite(ids, 'toque_botao', [(b, [f'{PASTA_ART}/botao_{b}.png'], 1, 0.1, False) for b in BOTOES],
                                [var(ids, 'toque_botao', 'papel', '')])), 'toque')


def cria(obj, papel, x, y, tam, anim_=None):
    acoes = [X('Create', '', obj, x, y, '"HUD"'),
             sets(obj, 'papel', papel),
             X('ResizableCapability::ResizableBehavior::SetSize', obj, 'Resizable', tam, tam),
             X('OpacityCapability::OpacityBehavior::SetValue', obj, 'Opacity', '=', f'{T}.opacidade'),
             X('ChangeColor', obj, f'{T}.cor')]
    if anim_:
        acoes.insert(2, anim(obj, anim_))
    return ev([], acoes)


def eventos():
    G = []
    # --- liga/desliga e cria os controles ---
    G.append(ev([X('DepartScene', '')], [setbv('ativo', False), setv('mov_id', '-1'), setv('mira_id', '-1')]
                + [setv(f'{b}_id', '-1') for b in BOTOES],
                [ev([OU(X('SystemInfo::IsMobile', ''), bv('forcar', True))], [setbv('ativo', True)]),
                 ev([ligado(), tem_pato()], [],
                    [cria('toque_base', 'mov', px('mov_x'), py('mov_y'), f'{T}.mov_raio * 2'),
                     cria('toque_alavanca', 'mov', px('mov_x'), py('mov_y'), f'{T}.mov_raio'),
                     cria('toque_base', 'mira', px('mira_x'), py('mira_y'), f'{T}.mira_raio * 2'),
                     cria('toque_alavanca', 'mira', px('mira_x'), py('mira_y'), f'{T}.mira_raio')]
                    + [cria('toque_botao', b, px(f'{b}_x'), py(f'{b}_y'), f'{T}.botao_raio * 2', b) for b in BOTOES])]))

    # --- a cada quadro ---
    quadro = []
    # dentro da loja o toque move o mouse (a loja é por clique); fora dela não (o dedo não pode mexer na mira)
    quadro.append(cada('pato', [bol('pato', 'na_loja', True)], [X('TouchSimulateMouse', '', 'yes')]))
    quadro.append(cada('pato', [bol('pato', 'na_loja', False)], [X('TouchSimulateMouse', '', 'no')]))
    # toques que acabaram
    fim = []
    for nome in ['mov', 'mira'] + BOTOES:
        extra = []
        if nome in ('mov', 'mira'):
            extra = [setv(f'{nome}_bx', px(f'{nome}_x')), setv(f'{nome}_by', py(f'{nome}_y')),
                     setv(f'{nome}_dx', '0'), setv(f'{nome}_dy', '0')]
        fim.append(ev([cmp(f'{T}.{nome}_id', '!=', '-1'), X('HasTouchEnded', '', f'{T}.{nome}_id')],
                      [setv(f'{nome}_id', '-1')] + extra))
    quadro += fim
    # quem não está sendo tocado fica no lugar de descanso (a janela pode mudar de tamanho)
    for nome in ('mov', 'mira'):
        quadro.append(ev([cmp(f'{T}.{nome}_id', '=', '-1')],
                         [setv(f'{nome}_bx', px(f'{nome}_x')), setv(f'{nome}_by', py(f'{nome}_y'))]))
    # toques novos: um botão ou um dos analógicos
    quadro.append(ev([], [setv('i', '0')]))
    perto = lambda b: cmp(f'DistanceBetweenPositions({T}.tx, {T}.ty, {px(b + "_x")}, {py(b + "_y")})', '<=',
                          f'{T}.botao_raio * {T}.folga')
    novo = [ev([], [setv('id', f'StartedTouchOrMouseId({T}.i)'),
                    setv('tx', f'TouchX({T}.id, "HUD", 0)'), setv('ty', f'TouchY({T}.id, "HUD", 0)'),
                    setbv('livre', True)])]
    for b in BOTOES:
        novo.append(ev([bv('livre', True), perto(b)], [setv(f'{b}_id', f'{T}.id'), setbv('livre', False)]))
    meio = f'{L} + CameraWidth("HUD", 0) / 2'
    novo.append(ev([bv('livre', True), cmp(f'{T}.tx', '<', meio), cmp(f'{T}.mov_id', '=', '-1')],
                   [setv('mov_id', f'{T}.id'), setv('mov_bx', f'{T}.tx'), setv('mov_by', f'{T}.ty'), setbv('livre', False)]))
    novo.append(ev([bv('livre', True), cmp(f'{T}.tx', '>=', meio), cmp(f'{T}.mira_id', '=', '-1')],
                   [setv('mira_id', f'{T}.id'), setv('mira_bx', f'{T}.tx'), setv('mira_by', f'{T}.ty'), setbv('livre', False)]))
    novo.append(ev([], [csetn(f'{T}.i', '+', '1')]))
    quadro.append(repete('StartedTouchOrMouseCount()', [], novo))
    # analógicos: vetor de -1 a 1 (comprimento até 1)
    for nome in ('mov', 'mira'):
        vx = f'(TouchX({T}.{nome}_id, "HUD", 0) - {T}.{nome}_bx)'
        vy = f'(TouchY({T}.{nome}_id, "HUD", 0) - {T}.{nome}_by)'
        r = f'{T}.{nome}_raio'
        k = f'(min(sqrt({vx} * {vx} + {vy} * {vy}), {r}) / max(sqrt({vx} * {vx} + {vy} * {vy}), 0.001) / {r})'
        quadro.append(ev([cmp(f'{T}.{nome}_id', '!=', '-1')],
                         [setv(f'{nome}_dx', f'{vx} * {k}'), setv(f'{nome}_dy', f'{vy} * {k}')]))
    # ações
    acoes = [setbv(n, False) for n in ('esquerda', 'direita', 'cima', 'baixo', 'pulo', 'dash', 'recarga', 'usar', 'tiro')]
    quadro.append(ev([], acoes))
    quadro.append(ev([cmp(f'{T}.mov_dx', '<', f'-{T}.zona_morta')], [setbv('esquerda', True)]))
    quadro.append(ev([cmp(f'{T}.mov_dx', '>', f'{T}.zona_morta')], [setbv('direita', True)]))
    quadro.append(ev([cmp(f'{T}.mov_dy', '<', f'-{T}.pulo_limiar')], [setbv('cima', True), setbv('pulo', True)]))
    quadro.append(ev([cmp(f'{T}.mov_dy', '>', f'{T}.baixo_limiar')], [setbv('baixo', True)]))
    for b in ('pulo', 'dash', 'recarga', 'usar'):
        quadro.append(ev([cmp(f'{T}.{b}_id', '!=', '-1')], [setbv(b, True)]))
    for b in ('pulo', 'dash', 'usar'):
        quadro.append(ev([], [setbv(f'{b}_agora', False)]))
        quadro.append(ev([bv(b, True), bv(f'{b}_antes', False)], [setbv(f'{b}_agora', True)]))
        quadro.append(ev([], [csetb(f'{T}.{b}_antes', False)]))
        quadro.append(ev([bv(b, True)], [setbv(f'{b}_antes', True)]))
    mag = f'sqrt({T}.mira_dx * {T}.mira_dx + {T}.mira_dy * {T}.mira_dy)'
    quadro.append(ev([cmp(f'{T}.mira_id', '!=', '-1'), cmp(mag, '>', f'{T}.zona_morta')],
                     [setv('mira_ang', f'atan2({T}.mira_dy, {T}.mira_dx)')]))
    quadro.append(ev([cmp(f'{T}.mira_id', '!=', '-1'), cmp(mag, '>', f'{T}.tiro_limiar')], [setbv('tiro', True)]))
    # desenho: base e alavanca seguem o dedo; botão apertado fica mais forte; tudo some na loja
    for nome in ('mov', 'mira'):
        quadro.append(ev([txt('toque_base', 'papel', nome)], [X('SetXY', 'toque_base', '=', f'{T}.{nome}_bx', '=', f'{T}.{nome}_by')]))
        quadro.append(ev([txt('toque_alavanca', 'papel', nome)],
                         [X('SetXY', 'toque_alavanca', '=', f'{T}.{nome}_bx + {T}.{nome}_dx * {T}.{nome}_raio',
                            '=', f'{T}.{nome}_by + {T}.{nome}_dy * {T}.{nome}_raio')]))
    quadro.append(ev([], [X('OpacityCapability::OpacityBehavior::SetValue', 'toque_botao', 'Opacity', '=', f'{T}.opacidade')]))
    for b in BOTOES:
        quadro.append(ev([txt('toque_botao', 'papel', b)], [X('SetXY', 'toque_botao', '=', px(f'{b}_x'), '=', py(f'{b}_y'))]))
        quadro.append(ev([bv(b, True), txt('toque_botao', 'papel', b)],
                         [X('OpacityCapability::OpacityBehavior::SetValue', 'toque_botao', 'Opacity', '=', f'{T}.opacidade_ativa')]))
    quadro.append(cada('pato', [bol('pato', 'na_loja', True)], [X('Hide', 'toque_base'), X('Hide', 'toque_alavanca')]))
    quadro.append(cada('pato', [bol('pato', 'na_loja', False)], [X('Show', 'toque_base'), X('Show', 'toque_alavanca')]))
    G.append(ev([ligado(), tem_pato()], [], quadro))
    # cenas sem o pato (Resultado): o toque volta a ser clique, para tocar e continuar
    G.append(ev([ligado(), cmp('SceneInstancesCount(pato)', '=', '0')], [X('TouchSimulateMouse', '', 'yes')]))

    # --- ponto de mira: mouse no computador; com o toque, na direção do analógico, a mira_dist do pato ---
    G.append(ev([bv('ativo', False)], [csetn('mira_x', '=', 'MouseX()'), csetn('mira_y', '=', 'MouseY()')]))
    G.append(ev([ligado(), tem_pato()],
                [csetn('mira_x', '=', f'pato.CenterX() + cos({T}.mira_ang) * {T}.mira_dist'),
                 csetn('mira_y', '=', f'pato.Y() + pato.Height() * 0.68 + sin({T}.mira_ang) * {T}.mira_dist')]))
    return grupo('Toque (celular)', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Controles de toque (t215): ligam no celular (ou com toque.forcar). Analógico esquerdo anda '
                    '(para cima pula), direito mira e atira; botões pulo, dash, recarga e usar (E). Números em toque.*. As condições de tecla aceitam também toque.<ação>.'}] + G)


def migra(d):
    ids = Ids('t215')
    objetos(d, ids)
    if not any(v['name'] == T for v in d['variables']):
        d['variables'].append({'name': T, 'persistentUuid': ids('var/global/toque'), 'type': 'structure',
                               'children': [var(ids, 'global/toque', k, v) for k, v in TOQUE]})
    poe_vars(ids, d['variables'], 'global', [('mira_x', 0), ('mira_y', 0)])

    trocas = {}
    for nome in FOLHAS:
        n = [0]
        percorre(folha(d, nome)['events'], lambda e: n.__setitem__(0, n[0] + embrulha(e.get('conditions', []), nome == 'Jogador')))
        trocas[nome] = n[0]
    n = [0]
    percorre(folha(d, 'Loja')['events'],
             lambda e: n.__setitem__(0, n[0] + embrulha(e.get('conditions', []), False, so={'"e"'})))
    trocas['Loja'] = n[0]
    n = [0]
    voo = acha(cena(d, 'Paraiso')['events'], 'Voo do pato')
    percorre([voo], lambda e: n.__setitem__(0, n[0] + embrulha(e.get('conditions', []), False)))
    trocas['Paraiso/Voo do pato'] = n[0]

    # a mira lê mira_x/mira_y
    jog = folha(d, 'Jogador')['events']
    mira = 0
    for g in ('Mira e posicionamento', 'Flipa a Arma para nao ficar de cabeca para baixo ao girar'):
        def troca(e):
            nonlocal mira
            for lista in ('conditions', 'actions'):
                for x in e.get(lista, []):
                    for i, p in enumerate(x['parameters']):
                        q = p.replace('MouseX()', 'mira_x').replace('MouseY()', 'mira_y')
                        if q != p:
                            x['parameters'][i] = q
                            mira += 1
        percorre([acha(jog, g)], troca)
    trocas['mira'] = mira

    # o grupo novo roda antes de tudo que lê teclas
    jog.insert(1, eventos())
    print('trocas:', trocas)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'toque_botao') is not None, 't215')
