"""Tarefa 190: telas de atributos nos hubs, no visual "Plano" (do agente de design: só texto sobre painéis lisos,
sem moldura, sem ícones, sem barras; cores neutras, sem roxo/lilás).
- Pedestal (quando o pato está perto de uma arma): painel escuro em cima da arma com o nome dela, "VS <equipada>" e
  [E] PEGAR (substitui a dica "E - ARMA"). Cada linha: nome, valor da arma do pedestal e a diferença para a equipada
  ("+62", "-2.6"), verde quando é melhor e vermelho quando é pior (na recarga, menos é melhor).
- Mercador: um painel só, em três colunas: arma equipada | loja | pato, e um rodapé com o item escolhido
  (NOME, NIVEL n/m, descrição e [ESPACO] COMPRAR). Na loja: nome, nível "n/m", preço (vermelho se não dá para pagar),
  MAX; a linha escolhida tem uma faixa clara e ">". O upgrade escolhido mostra o que muda: valor verde e "+5" na arma
  ou no pato. Atributo zerado fica apagado.
- Números: inteiros para dano, dano/s, pente, vida, velocidade; uma casa no máximo para tiros/s e recarga (em SEG:
  na Name Smile o "s" parece um 5). A diferença é calculada com os números já arredondados.
- As contas são as do 'Aplicar upgrades' (folha Jogador). stats_arma[arma].atual/.novo e stats_pato.atual/.novo
  guardam os números (novo = com o upgrade escolhido na loja).
Como funciona: cada texto (objeto ui_txt) é criado uma vez no começo da cena, com as variáveis card / linha / dx / dy /
dir / campo e o tamanho da fonte. Todo quadro: ui_card[card] diz onde o cartão (ou a coluna) está e se aparece,
ui_lin[card][lN] tem o conteúdo de cada linha, e um ForEach posiciona e preenche cada texto. Painéis, linhas
divisórias, faixa da linha escolhida e teclas são retângulos de um desenhador (ui_fundo_mundo / ui_fundo_hud).
linha: >= 0 linha do cartão (centralizada na altura da linha); -1 cabeçalho (y = topo do cartão + dy).
dir: 0 x a partir da esquerda, 1 a partir da direita, 2 x feito à parte (encadeado com outro texto).
Rodar uma vez:  python3 tools/t190_stats.py
"""
import copy
from gd_mig import *

ids = Ids('t190')
G = lambda n: f'GlobalVariable({n})'
GS = lambda n: f'GlobalVariableString({n})'
ARMAS = [('pistola', 'PISTOLA'), ('doze', 'DOZE'), ('minigun', 'MINIGUN'), ('lanca', 'LANCA-GRANADAS')]
# (chave, rótulo, unidade, com casa decimal, menos é melhor)
STATS_ARMA = [('dano', 'DANO/TIRO', '', False, False), ('tiros', 'TIROS/S', '', True, False),
              ('dps', 'DANO/S', '', False, False), ('pente', 'PENTE', '', False, False),
              ('recarga', 'RECARGA', ' SEG', True, True), ('mobilidade', 'MOBILIDADE', '%', False, False)]
# (chave, rótulo, id do upgrade)
STATS_PATO = [('vida', 'VIDA', 'vida'), ('velocidade', 'VELOCIDADE', 'velocidade'), ('pulos', 'PULOS NO AR', 'pulo'),
              ('ricochete', 'RICOCHETE', 'ricochete'), ('perfuracao', 'PERFURACAO', 'perfuracao'),
              ('eletricidade', 'ELETRICIDADE', 'eletricidade'), ('laser', 'LASER', 'laser')]
CAMADA = {'arma': '', 'larma': 'HUD', 'loja': 'HUD', 'lpato': 'HUD', 'rodape': 'HUD'}
DRAW = {'arma': 'ui_fundo_mundo', 'rodape': 'ui_fundo_hud'}
T = 'ui_txt'

VARS = [  # tudo em unidades do jogo (1920x1080)
    ('ui_z', 2000),
    # cores (sem roxo): fundo, divisórias, textos
    ('ui_cor_fundo', '12;12;12'), ('ui_op_fundo', 245), ('ui_cor_regra', '255;255;255'), ('ui_op_regra', 22),
    ('ui_regra_h', 1), ('ui_op_sel', 16), ('ui_cor_tecla', '8;8;8'), ('ui_op_tecla', 200), ('ui_tecla_borda', 2),
    ('ui_cor_texto', '244;234;210'), ('ui_cor_rotulo', '170;170;170'), ('ui_cor_dim', '105;105;105'),
    ('ui_cor_creme', '255;236;170'), ('ui_cor_ouro', '232;186;84'), ('ui_cor_moeda', '255;214;94'),
    ('ui_cor_verde', '134;224;124'), ('ui_cor_vermelho', '255;107;94'),
    # tamanhos de fonte
    ('ui_tam_nome_arma', 26), ('ui_tam_titulo', 24), ('ui_tam_sub', 14), ('ui_tam_rot', 16), ('ui_tam_val', 19),
    ('ui_tam_delta', 16), ('ui_tam_loja', 18), ('ui_tam_nivel', 16), ('ui_tam_moedas', 22), ('ui_tam_tecla', 16),
    ('ui_tam_desc', 16), ('ui_tam_desc_nome', 19), ('ui_tam_cursor', 18),
    # pedestal
    ('ui_w_arma', 360), ('ui_pad', 17), ('ui_ped_dy_nome', 12), ('ui_ped_dy_sub', 44), ('ui_ped_dy_tecla', 18),
    ('ui_ped_cab', 72), ('ui_ped_topo', 80), ('ui_lin_h', 26), ('ui_ped_base', 12), ('ui_ped_folga', 10),
    ('ui_col_val', 79), ('ui_col_delta', 17), ('ui_rab_w1', 14), ('ui_rab_w2', 5), ('ui_rab_h', 2),
    # mercador
    ('ui_w_larma', 360), ('ui_w_loja', 456), ('ui_w_lpato', 336), ('ui_m_h', 516), ('ui_m_pad', 24),
    ('ui_m_dy_titulo', 22), ('ui_m_dy_sub', 30), ('ui_m_dy_moedas', 24), ('ui_m_cab', 62),
    ('ui_m_topo_arma', 74), ('ui_m_lin_arma', 31), ('ui_m_topo_loja', 72), ('ui_m_lin_loja', 36),
    ('ui_m_col_val', 86), ('ui_m_col_delta', 24), ('ui_m_sel_inset', 10), ('ui_m_cur_x', 17), ('ui_m_nome_x', 36),
    ('ui_m_nivel_dir', 115), ('ui_m_preco_dir', 24), ('ui_regra_v_ini', 19), ('ui_regra_v_fim', 10),
    ('ui_rod_y', 446), ('ui_rod_h', 70), ('ui_rod_gap', 12), ('ui_rod_gap_desc', 29),
    ('ui_moeda_escala', 0.4), ('ui_moeda_gap', 6), ('ui_tecla_pad', 7), ('ui_tecla_pad_v', 4), ('ui_tecla_gap', 10),
    ('ui_mouse_lin', -1), ('ui_k', 0), ('ui_tmp_x', 0), ('ui_tmp_tecla', 0),
    ('stats_precisao', 10), ('stats_hover', ''), ('stats_ver_arma', False), ('stats_px', 0), ('stats_py', 0)]


# ---------------- variáveis e objetos ----------------
def estrutura(nome, filhos):
    return {'name': nome, 'persistentUuid': ids(f'var/g/{nome}'), 'type': 'structure', 'children': filhos}


def variaveis(d):
    niveis = [c['name'] for c in next(v for v in d['variables'] if v['name'] == 'upgrades')['children']]
    tem = {v['name'] for v in d['variables']}
    novas = [estrutura('stats_nivel', [var(ids, 'stats_nivel', n, 0) for n in niveis]),
             estrutura('stats_nome', [var(ids, 'stats_nome', a, n) for a, n in ARMAS]),
             estrutura('stats_arma', []), estrutura('stats_pato', []), estrutura('ui_card', []),
             estrutura('ui_lin', []), estrutura('ui_upg_max', [])]
    d['variables'] += [v for v in novas if v['name'] not in tem]
    poe_vars(ids, d['variables'], 'g', VARS)
    return niveis


def vars_elem(nome):
    return [var(ids, nome, n, v) for n, v in
            (('card', ''), ('linha', 0), ('dx', 0), ('dy', 0), ('dir', 0), ('campo', ''))]


def objetos(d):
    o = copy.deepcopy(objeto(d, 'loja_dica'))
    o.update(name=T, persistentUuid=ids('obj/' + T), variables=vars_elem(T), string='', textAlignment='left')
    o['content'].update(text='', textAlignment='left', isShadowEnabled=False, lineHeight=0)
    poe_objeto(d, o, 'ui')
    nomes_rec = {r['name'] for r in d['resources']['resources']}
    assert 'hud/moeda.png' in nomes_rec
    poe_objeto(d, sprite(ids, 'ui_moeda', [('idle', ['hud/moeda.png'], 1, 1, False)], vars_elem('ui_moeda')), 'ui')
    for n in ('ui_fundo_mundo', 'ui_fundo_hud'):
        o = copy.deepcopy(objeto(d, 'loja_painel'))
        o.update(name=n, persistentUuid=ids('obj/' + n), variables=[], outlineOpacity=255)
        poe_objeto(d, o, 'ui')
    if 'ui_elems' not in {g['name'] for g in d['objectsGroups']}:
        d['objectsGroups'].append({'name': 'ui_elems', 'objects': [{'name': T}, {'name': 'ui_moeda'}]})


# ---------------- criação dos textos (uma vez, no começo da cena) ----------------
def cria(card, campo, tam, linha=-1, dir=0, dx='0', dy='0', obj=T, extra=()):
    acs = [X('Create', '', obj, '0', '0', f'"{CAMADA[card]}"'),
           X('SetStringObjectVariable', obj, 'card', '=', f'"{card}"'),
           X('SetNumberObjectVariable', obj, 'linha', '=', str(linha)),
           X('SetNumberObjectVariable', obj, 'dx', '=', dx),
           X('SetNumberObjectVariable', obj, 'dir', '=', str(dir)),
           X('SetNumberObjectVariable', obj, 'dy', '=', dy),
           X('SetStringObjectVariable', obj, 'campo', '=', f'"{campo}"'),
           X('ChangePlan', obj, '=', f'{G("ui_z")} + 2'),
           X('Hide', obj)]
    if obj == T:
        acs.append(X('TextObject::Text::SetFontSize', T, '=', G(tam)))
    return acs + list(extra)


def criacao():
    evs = [ev([X('DepartScene', '')], [
        X('Create', '', 'ui_fundo_mundo', '0', '0', '""'), X('ChangePlan', 'ui_fundo_mundo', '=', f'{G("ui_z")} + 1'),
        X('Create', '', 'ui_fundo_hud', '0', '0', '"HUD"'), X('ChangePlan', 'ui_fundo_hud', '=', f'{G("ui_z")} + 1')])]
    E = lambda acs: evs.append(ev([X('DepartScene', '')], acs))
    p, mp = G('ui_pad'), G('ui_m_pad')
    # pedestal: nome, VS <equipada>, [E] PEGAR
    E(cria('arma', 'titulo', 'ui_tam_nome_arma', dx=p, dy=G('ui_ped_dy_nome')))
    E(cria('arma', 'sub', 'ui_tam_sub', dx=p, dy=G('ui_ped_dy_sub')))
    E(cria('arma', 'acao', 'ui_tam_tecla', dir=1, dx=p, dy=G('ui_ped_dy_tecla')))
    E(cria('arma', 'tecla', 'ui_tam_tecla', dir=2, dy=G('ui_ped_dy_tecla')))
    # cabeçalhos das colunas do mercador
    for c in ('larma', 'loja', 'lpato'):
        E(cria(c, 'titulo', 'ui_tam_titulo', dx=mp, dy=G('ui_m_dy_titulo')))
    E(cria('larma', 'sub', 'ui_tam_sub', dir=1, dx=mp, dy=G('ui_m_dy_sub')))
    E(cria('loja', 'moedas', 'ui_tam_moedas', dir=1, dx=mp, dy=G('ui_m_dy_moedas')))
    E(cria('loja', '', '', obj='ui_moeda', dir=2, extra=[
        X('ScalableCapability::ScalableBehavior::SetValue', 'ui_moeda', 'Scale', '=', G('ui_moeda_escala'))]))
    # linhas da arma (pedestal e mercador) e do pato: nome, valor, diferença
    for c, n, val, dl in (('arma', len(STATS_ARMA), 'ui_col_val', 'ui_col_delta'),
                          ('larma', len(STATS_ARMA), 'ui_m_col_val', 'ui_m_col_delta'),
                          ('lpato', len(STATS_PATO), 'ui_m_col_val', 'ui_m_col_delta')):
        dx_rot = p if c == 'arma' else mp
        for k in range(n):   # um Create por evento: o Create junta a nova instância às já escolhidas
            E(cria(c, 'rot', 'ui_tam_rot', k, dx=dx_rot))
            E(cria(c, 'val', 'ui_tam_val', k, dir=1, dx=G(val)))
            E(cria(c, 'delta', 'ui_tam_delta', k, dir=1, dx=G(dl)))
    # linhas da loja: cursor, nome, n/m, preço
    for campo, tam, dir, dx in (('cur', 'ui_tam_cursor', 0, 'ui_m_cur_x'), ('rot', 'ui_tam_loja', 0, 'ui_m_nome_x'),
                                ('nivel', 'ui_tam_nivel', 1, 'ui_m_nivel_dir'), ('val', 'ui_tam_loja', 1, 'ui_m_preco_dir')):
        evs.append(ev([X('DepartScene', '')], [X('SetNumberVariable', 'ui_k', '=', '0')], [
            repete('GlobalVariableChildCount(loja_catalogo)', [
                *cria('loja', campo, tam, G('ui_k'), dir=dir, dx=G(dx)), X('SetNumberVariable', 'ui_k', '+', '1')])]))
    # rodapé: NOME  NIVEL n/m  descrição ......  [ESPACO] COMPRAR
    E(cria('rodape', 'nome', 'ui_tam_desc_nome', 0, dx=mp))
    E(cria('rodape', 'nivel', 'ui_tam_sub', 0, dir=2))
    E(cria('rodape', 'desc', 'ui_tam_desc', 0, dir=2, extra=[X('TextObject::SetWrapping', T, 'yes')]))
    E(cria('rodape', 'acao', 'ui_tam_tecla', 0, dir=1, dx=mp))
    E(cria('rodape', 'tecla', 'ui_tam_tecla', 0, dir=2))
    return evs


# ---------------- contas ----------------
def contas(niveis):
    evs = [ev([], [X('SetNumberVariable', f'stats_nivel.{n}', '=', G(f'upgrades.{n}')) for n in niveis]),
           # prévia: o upgrade escolhido na loja, se ainda não está no máximo, conta um nível a mais
           ev([cbol('loja_aberta', True), X('NumberVariable', 'loja_sel_nivel', '<', 'loja_sel_max')],
              [X('SetNumberVariable', 'stats_nivel[loja_sel_id]', '+', '1')]),
           ev([], [X('SetNumberVariable', 'ui_k', '=', '0')], [
               repete('GlobalVariableChildCount(loja_catalogo)', [
                   X('SetNumberVariable', f'ui_upg_max[{GS("loja_catalogo[" + G("ui_k") + "].id")}]', '=',
                     G(f'loja_catalogo[{G("ui_k")}].nivel_max')),
                   X('SetNumberVariable', 'ui_k', '+', '1')])])]
    acs_arma, acs_pato = [], []
    for pref, L in (('atual', 'upgrades'), ('novo', 'stats_nivel')):
        n = lambda k: G(f'{L}.{k}')
        dano = f'(Arma.dano * Arma.FireBullet::BulletQuantity() + Arma.dano_explosao) * (1 + pato.upg_dano * {n("dano")})'
        tiros = f'1 / (Arma.cooldown_base * pow(pato.upg_cadencia, {n("cadencia")}))'
        for k, e in (('dano', dano), ('tiros', tiros), ('dps', f'{dano} * {tiros}'),
                     ('pente', 'Arma.FireBullet::ShotsPerReload()'),
                     ('recarga', f'Arma.recarga_base * pow(pato.upg_recarga, {n("recarga")})'),
                     ('mobilidade', 'Arma.vel_mov * 100')):
            acs_arma.append(X('SetNumberVariable', f'stats_arma[Arma.ObjectName()].{pref}.{k}', '=', e))
        for k, e in (('vida', f'pato.upg_vida_base + pato.upg_vida_nivel * {n("vida")}'),
                     ('velocidade', f'pato.velocidade_base * (1 + pato.upg_velocidade * {n("velocidade")})'),
                     ('pulos', f'pato.pulos_ar_base + pato.upg_pulo * {n("pulo")}'),
                     ('ricochete', n('ricochete')), ('perfuracao', n('perfuracao')),
                     ('eletricidade', f'round(pato.eletro_dano * {n("eletricidade")} * (1 + pato.upg_dano * {n("dano")}))'),
                     ('laser', n('laser'))):
            acs_pato.append(X('SetNumberVariable', f'stats_pato.{pref}.{k}', '=', e))
    evs.append(cada('Arma', [], acs_arma))
    evs.append(ev([], acs_pato))
    return evs


# ---------------- conteúdo das linhas ----------------
def S(path, v):
    return X('SetStringVariable', path, '=', v)


def N(path, v):
    return X('SetNumberVariable', path, '=', v)


def linhas_arma(c, a_base, b_base):
    """a_base: referência (a equipada agora); b_base: o que a coluna mostra."""
    evs = []
    for k, (s, rot, un, decimal, menos) in enumerate(STATS_ARMA):
        L = f'ui_lin.{c}.l{k}'
        m = G('stats_precisao') if decimal else '1'
        va, vb = G(L + '.a'), G(L + '.b')
        u = f' + "{un}"' if un else ''
        evs.append(ev([], [N(f'{L}.a', f'round({G(f"{a_base}.{s}")} * {m}) / {m}'),
                           N(f'{L}.b', f'round({G(f"{b_base}.{s}")} * {m}) / {m}'),
                           S(f'{L}.rot', f'"{rot}"'), S(f'{L}.rot_cor', GS('ui_cor_rotulo')),
                           S(f'{L}.val', f'ToString({vb}){u}'), S(f'{L}.val_cor', GS('ui_cor_texto')),
                           S(f'{L}.delta', '""'), S(f'{L}.delta_cor', GS('ui_cor_texto'))]))
        dif = f'ToString(round(abs({vb} - {va}) * {m}) / {m})'
        for op, sinal, bom in (('>', '+', not menos), ('<', '-', menos)):
            cor = GS('ui_cor_verde' if bom else 'ui_cor_vermelho')
            evs.append(ev([cmp(vb, op, va)], [S(f'{L}.delta', f'"{sinal}" + {dif}'), S(f'{L}.delta_cor', cor),
                                              S(f'{L}.val_cor', cor), S(f'{L}.rot_cor', GS('ui_cor_texto'))]))
    return evs


def linhas_pato():
    evs = []
    for k, (s, rot, up) in enumerate(STATS_PATO):
        L = f'ui_lin.lpato.l{k}'
        va, vb = G(L + '.a'), G(L + '.b')
        evs.append(ev([], [N(f'{L}.a', f'round({G("stats_pato.atual." + s)})'),
                           N(f'{L}.b', f'round({G("stats_pato.novo." + s)})'),
                           S(f'{L}.rot', f'"{rot}"'), S(f'{L}.rot_cor', GS('ui_cor_rotulo')),
                           S(f'{L}.val', '"SIM"' if s == 'laser' else f'ToString({vb})'),
                           S(f'{L}.val_cor', GS('ui_cor_texto')), S(f'{L}.delta', '""'),
                           S(f'{L}.delta_cor', GS('ui_cor_ouro'))], [
            ev([cmp(vb, '<=', '0')], [S(f'{L}.rot_cor', GS('ui_cor_dim')), S(f'{L}.val_cor', GS('ui_cor_dim'))] +
               ([S(f'{L}.val', '"--"')] if s == 'laser' else [])),
            ev([cmp(G(f'upgrades.{up}'), '>=', G(f'ui_upg_max.{up}'))], [S(f'{L}.delta', '"MAX"')]),
            ev([cmp(vb, '>', va)], [S(f'{L}.val_cor', GS('ui_cor_verde')), S(f'{L}.rot_cor', GS('ui_cor_texto')),
                                    S(f'{L}.delta', '"+" + ToString(' + f'{vb} - {va})' if s != 'laser' else '""'),
                                    S(f'{L}.delta_cor', GS('ui_cor_verde'))]),
        ]))
    return evs


def cartoes():
    """onde cada cartão/coluna fica e os textos dos cabeçalhos."""
    C = lambda c, f: f'ui_card.{c}.{f}'
    atual = GS('stats_nome[GlobalVariableString(arma_atual)]')
    ped = [N(C('arma', 'w'), G('ui_w_arma')), N(C('arma', 'topo'), G('ui_ped_topo')),
           N(C('arma', 'lin_h'), G('ui_lin_h')), N(C('arma', 'linhas'), str(len(STATS_ARMA))),
           N(C('arma', 'h'), f'{G("ui_ped_topo")} + {G(C("arma", "linhas"))} * {G("ui_lin_h")} + {G("ui_ped_base")}')]
    col = []
    for c, w, topo, lin, n in (('larma', 'ui_w_larma', 'ui_m_topo_arma', 'ui_m_lin_arma', str(len(STATS_ARMA))),
                               ('loja', 'ui_w_loja', 'ui_m_topo_loja', 'ui_m_lin_loja',
                                'GlobalVariableChildCount(loja_catalogo)'),
                               ('lpato', 'ui_w_lpato', 'ui_m_topo_arma', 'ui_m_lin_arma', str(len(STATS_PATO)))):
        col += [N(C(c, 'w'), G(w)), N(C(c, 'topo'), G(topo)), N(C(c, 'lin_h'), G(lin)), N(C(c, 'linhas'), n),
                N(C(c, 'h'), G('ui_m_h'))]
    col += [N(C('rodape', 'topo'), '0'), N(C('rodape', 'lin_h'), G('ui_rod_h')), N(C('rodape', 'linhas'), '1'),
            N(C('rodape', 'w'), f'{G("ui_w_larma")} + {G("ui_w_loja")} + {G("ui_w_lpato")}')]
    txt = [S(C('arma', 'titulo'), GS('stats_nome[GlobalVariableString(stats_hover)]')),
           S(C('arma', 'sub'), f'"VS " + {atual}'), S(C('arma', 'tecla'), '"E"'), S(C('arma', 'acao'), '"PEGAR"'),
           S(C('larma', 'titulo'), atual), S(C('larma', 'sub'), '"EQUIPADA"'),
           S(C('loja', 'titulo'), '"MERCADOR"'), S(C('loja', 'moedas'), f'ToString({G("moedas_total")})'),
           S(C('lpato', 'titulo'), '"PATO"')]
    for c in ('arma', 'larma', 'loja', 'lpato'):
        txt.append(S(C(c, 'titulo_cor'), GS('ui_cor_creme')))
    txt += [S(C('arma', 'sub_cor'), GS('ui_cor_dim')), S(C('larma', 'sub_cor'), GS('ui_cor_dim')),
            S(C('arma', 'tecla_cor'), GS('ui_cor_ouro')), S(C('arma', 'acao_cor'), GS('ui_cor_ouro')),
            S(C('loja', 'moedas_cor'), GS('ui_cor_moeda'))]
    R = 'ui_lin.rodape.l0'
    rod = [S(f'{R}.nome', f'ToUpperCase({GS("loja_catalogo[loja_sel].nome")})'), S(f'{R}.nome_cor', GS('ui_cor_ouro')),
           S(f'{R}.nivel', '"NIVEL " + ToString(loja_sel_nivel) + "/" + ToString(loja_sel_max)'),
           S(f'{R}.nivel_cor', GS('ui_cor_dim')),
           S(f'{R}.desc', GS('loja_catalogo[loja_sel].descricao')), S(f'{R}.desc_cor', GS('ui_cor_texto')),
           S(f'{R}.tecla', '"ESPACO"'), S(f'{R}.tecla_cor', GS('ui_cor_ouro')),
           S(f'{R}.acao', '"COMPRAR"'), S(f'{R}.acao_cor', GS('ui_cor_ouro'))]
    evs = [ev([], [N(C(c, 'vis'), '0') for c in CAMADA] + ped + col + txt + rod)]
    # pedestal: em cima da arma, com o rabicho embaixo
    evs.append(ev([cbol('stats_ver_arma', True)], [
        N(C('arma', 'vis'), '1'),
        N(C('arma', 'x'), f'{G("stats_px")} - {G(C("arma", "w"))} / 2'),
        N(C('arma', 'y'), f'{G("stats_py")} - {G(C("arma", "h"))} - {G("ui_ped_folga")} - 2 * {G("ui_rab_h")}')]))
    # mercador: um painel no meio da tela, três colunas e o rodapé
    x0 = f'CameraBorderLeft("HUD") + (CameraWidth("HUD") - {G(C("rodape", "w"))}) / 2'
    y0 = f'CameraBorderTop("HUD") + (CameraHeight("HUD") - {G("ui_m_h")}) / 2'
    evs.append(ev([cbol('loja_aberta', True)], [N(C(c, 'vis'), '1') for c in ('larma', 'loja', 'lpato', 'rodape')] + [
        N(C('larma', 'x'), x0), N(C('larma', 'y'), y0),
        N(C('loja', 'x'), f'{G(C("larma", "x"))} + {G("ui_w_larma")}'), N(C('loja', 'y'), y0),
        N(C('lpato', 'x'), f'{G(C("loja", "x"))} + {G("ui_w_loja")}'), N(C('lpato', 'y'), y0),
        N(C('rodape', 'x'), x0), N(C('rodape', 'y'), f'{y0} + {G("ui_rod_y")}')]))
    return evs


def mouse():
    """a linha da loja sob o cursor (-1 = nenhuma); a folha Loja usa no lugar do texto da linha."""
    C = lambda f: G(f'ui_card.loja.{f}')
    mx, my = 'CursorX("HUD", 0)', 'CursorY("HUD", 0)'
    return [ev([], [N('ui_mouse_lin', '-1')]),
            ev([cbol('loja_aberta', True), cmp(mx, '>=', C('x')), cmp(mx, '<=', f'{C("x")} + {C("w")}'),
                cmp(my, '>=', f'{C("y")} + {C("topo")}'),
                cmp(my, '<', f'{C("y")} + {C("topo")} + {C("linhas")} * {C("lin_h")}')],
               [N('ui_mouse_lin', f'floor(({my} - {C("y")} - {C("topo")}) / {C("lin_h")})')])]


# ---------------- desenho: painéis, divisórias, linha escolhida, rabicho ----------------
def ret(D, a, b, c, d):
    return X('PrimitiveDrawing::Rectangle', D, a, b, c, d)


def cor(D, n, op):
    return [X('PrimitiveDrawing::FillColor', D, GS(n)), X('PrimitiveDrawing::FillOpacity', D, '=', G(op))]


def desenho():
    evs = []
    D = 'ui_fundo_mundo'
    C = lambda f: G(f'ui_card.arma.{f}')
    x2, y2, rh = f'{C("x")} + {C("w")}', f'{C("y")} + {C("h")}', G('ui_rab_h')
    meio = f'{C("x")} + {C("w")} / 2'
    regra_y = f'{C("y")} + {G("ui_ped_cab")}'
    evs.append(ev([cmp(C('vis'), '=', '1')], cor(D, 'ui_cor_fundo', 'ui_op_fundo') + [
        ret(D, C('x'), C('y'), x2, y2),
        ret(D, f'{meio} - {G("ui_rab_w1")} / 2', y2, f'{meio} + {G("ui_rab_w1")} / 2', f'{y2} + {rh}'),
        ret(D, f'{meio} - {G("ui_rab_w2")} / 2', f'{y2} + {rh}', f'{meio} + {G("ui_rab_w2")} / 2', f'{y2} + 2 * {rh}')] +
        cor(D, 'ui_cor_regra', 'ui_op_regra') + [
        ret(D, f'{C("x")} + {G("ui_pad")}', regra_y, f'{x2} - {G("ui_pad")}', f'{regra_y} + {G("ui_regra_h")}')]))
    D = 'ui_fundo_hud'
    M = lambda c, f: G(f'ui_card.{c}.{f}')
    y, mp, rgh = M('larma', 'y'), G('ui_m_pad'), G('ui_regra_h')
    xf = f'{M("lpato", "x")} + {M("lpato", "w")}'
    acs = cor(D, 'ui_cor_fundo', 'ui_op_fundo') + [ret(D, M('larma', 'x'), y, xf, f'{y} + {G("ui_m_h")}')]
    acs += cor(D, 'ui_cor_regra', 'ui_op_regra')
    for c in ('loja', 'lpato'):   # divisórias verticais entre as colunas
        acs.append(ret(D, M(c, 'x'), f'{y} + {G("ui_regra_v_ini")}', f'{M(c, "x")} + {rgh}',
                       f'{M("rodape", "y")} - {G("ui_regra_v_fim")}'))
    for c in ('larma', 'loja', 'lpato'):   # linha embaixo do cabeçalho de cada coluna
        acs.append(ret(D, f'{M(c, "x")} + {mp}', f'{y} + {G("ui_m_cab")}', f'{M(c, "x")} + {M(c, "w")} - {mp}',
                       f'{y} + {G("ui_m_cab")} + {rgh}'))
    acs.append(ret(D, f'{M("larma", "x")} + {mp}', M('rodape', 'y'), f'{xf} - {mp}', f'{M("rodape", "y")} + {rgh}'))
    ys = f'{M("loja", "y")} + {M("loja", "topo")} + loja_sel * {M("loja", "lin_h")}'
    acs += cor(D, 'ui_cor_regra', 'ui_op_sel') + [
        ret(D, f'{M("loja", "x")} + {G("ui_m_sel_inset")}', ys, f'{M("loja", "x")} + {M("loja", "w")} - {G("ui_m_sel_inset")}',
            f'{ys} + {M("loja", "lin_h")}')]
    evs.append(ev([cmp(M('loja', 'vis'), '=', '1')], acs))
    return evs


def teclas():
    """o fundo das teclas [E] e [ESPACO]: retângulo escuro com borda dourada em volta do texto (depois de posicionar)."""
    evs = []
    for c, D in DRAW.items():
        p, pv = G('ui_tecla_pad'), G('ui_tecla_pad_v')
        evs.append(ev([cmp(G(f'ui_card.{c}.vis'), '=', '1'), X('StringObjectVariable', T, 'card', '=', f'"{c}"'),
                       X('StringObjectVariable', T, 'campo', '=', '"tecla"')], cor(D, 'ui_cor_tecla', 'ui_op_tecla') + [
            X('PrimitiveDrawing::OutlineSize', D, '=', G('ui_tecla_borda')),
            X('PrimitiveDrawing::OutlineColor', D, GS('ui_cor_ouro')),
            ret(D, f'{T}.X() - {p}', f'{T}.Y() - {pv}', f'{T}.X() + {T}.Width() + {p}', f'{T}.Y() + {T}.Height() + {pv}'),
            X('PrimitiveDrawing::OutlineSize', D, '=', '0')]))
    return evs


# ---------------- posição, visibilidade e conteúdo ----------------
def pecas():
    E = 'ui_elems'
    C = lambda o, f: G(f'ui_card[{o}.card].{f}')
    evs = [
        cada(E, [], [X('Hide', E)], [
            ev([cmp(C(E, 'vis'), '=', '1')], [X('Show', E, '')], [
                ev([X('NumberObjectVariable', E, 'linha', '>=', C(E, 'linhas'))], [X('Hide', E)]),
                ev([X('NumberObjectVariable', E, 'dir', '=', '0')], [X('SetX', E, '=', f'{C(E, "x")} + {E}.dx')]),
                ev([X('NumberObjectVariable', E, 'dir', '=', '1')],
                   [X('SetX', E, '=', f'{C(E, "x")} + {C(E, "w")} - {E}.dx - {E}.Width()')]),
                ev([X('NumberObjectVariable', E, 'linha', '>=', '0')], [X('SetY', E, '=',
                    f'{C(E, "y")} + {C(E, "topo")} + {E}.linha * {C(E, "lin_h")} + ({C(E, "lin_h")} - {E}.Height()) / 2')]),
                ev([X('NumberObjectVariable', E, 'linha', '<', '0')], [X('SetY', E, '=', f'{C(E, "y")} + {E}.dy')]),
            ])]),
        cada(T, [], [], [
            ev([X('NumberObjectVariable', T, 'linha', '>=', '0')], [
                X('TextContainerCapability::TextContainerBehavior::SetValue', T, 'Text', '=',
                  f'GlobalVariableString(ui_lin[{T}.card]["l" + ToString({T}.linha)][{T}.campo])'),
                X('TextObject::ChangeColor', T,
                  f'GlobalVariableString(ui_lin[{T}.card]["l" + ToString({T}.linha)][{T}.campo + "_cor"])')]),
            ev([X('NumberObjectVariable', T, 'linha', '<', '0')], [
                X('TextContainerCapability::TextContainerBehavior::SetValue', T, 'Text', '=',
                  f'GlobalVariableString(ui_card[{T}.card][{T}.campo])'),
                X('TextObject::ChangeColor', T, f'GlobalVariableString(ui_card[{T}.card][{T}.campo + "_cor"])')])]),
    ]
    sel = lambda c, campo: [X('StringObjectVariable', T, 'card', '=', f'"{c}"'),
                            X('StringObjectVariable', T, 'campo', '=', f'"{campo}"')]
    gap, p = G('ui_tecla_gap'), G('ui_tecla_pad')
    # [tecla] ação: a tecla fica à esquerda da ação
    for c in ('arma', 'rodape'):
        evs += [ev(sel(c, 'acao'), [N('ui_tmp_x', f'{T}.X()')]),
                ev(sel(c, 'tecla'), [X('SetX', T, '=', f'{G("ui_tmp_x")} - {gap} - {p} - {T}.Width()'),
                                     N('ui_tmp_tecla', f'{T}.X() - {p}')])]
    # rodapé: NOME, NIVEL n/m e descrição em sequência; a descrição quebra antes da tecla
    evs += [ev(sel('rodape', 'nome'), [N('ui_tmp_x', f'{T}.X() + {T}.Width()')]),
            ev(sel('rodape', 'nivel'), [X('SetX', T, '=', f'{G("ui_tmp_x")} + {G("ui_rod_gap")}'),
                                        N('ui_tmp_x', f'{T}.X() + {T}.Width()')]),
            ev(sel('rodape', 'desc'), [X('SetX', T, '=', f'{G("ui_tmp_x")} + {G("ui_rod_gap_desc")}'),
                                       X('TextObject::WrappingWidth', T, '=',
                                         f'{G("ui_tmp_tecla")} - {G("ui_rod_gap_desc")} - {T}.X()')]),
            # moeda à esquerda do número de moedas
            ev(sel('loja', 'moedas'), [
                X('SetX', 'ui_moeda', '=', f'{T}.X() - {G("ui_moeda_gap")} - ui_moeda.Width()'),
                X('SetY', 'ui_moeda', '=', f'{T}.Y() + ({T}.Height() - ui_moeda.Height()) / 2')])]
    return evs


def esconde():
    return [ev([], [X('Hide', 'loja_painel'), X('Hide', 'loja_faixa'), X('Hide', 'loja_linha'), X('Hide', 'loja_desc'),
                    X('Hide', 'arma_dica'), X('SetBooleanVariable', 'stats_ver_arma', 'False', '')])]


def loja_linhas(d):
    """no ForEach da loja (folha Loja): copia o que cada linha mostra para ui_lin.loja.lN; o mouse passa a usar a
    linha sob o cursor (ui_mouse_lin) em vez do texto da linha, que agora fica escondido."""
    menu = acha(folha(d, 'Loja')['events'], 'Menu')
    fe = next(e for e in menu['events'] if e['type'].endswith('ForEach') and e.get('object') == 'loja_linha')
    L = 'ui_lin.loja["l" + ToString(loja_linha.indice)]'
    fe['events'].append(ev([], [
        S(f'{L}.rot', f'ToUpperCase({GS("loja_catalogo[loja_linha.indice].nome")})'),
        S(f'{L}.rot_cor', GS('ui_cor_rotulo')), S(f'{L}.cur', '""'), S(f'{L}.cur_cor', GS('ui_cor_ouro')),
        S(f'{L}.nivel', 'ToString(loja_nivel) + "/" + ToString(loja_max)'), S(f'{L}.nivel_cor', GS('ui_cor_dim')),
        S(f'{L}.val', 'ToString(loja_preco)'), S(f'{L}.val_cor', GS('ui_cor_moeda'))], [
        ev([X('NumberVariable', 'moedas_total', '<', 'loja_preco')], [S(f'{L}.val_cor', GS('ui_cor_vermelho'))]),
        ev([X('NumberObjectVariable', 'loja_linha', 'indice', '=', 'loja_sel')],
           [S(f'{L}.rot_cor', GS('ui_cor_texto')), S(f'{L}.cur', '">"')]),
        ev([X('NumberVariable', 'loja_bloq', '=', '1')], [S(f'{L}.val', '"BLOQ"'), S(f'{L}.val_cor', GS('ui_cor_vermelho'))]),
        ev([X('NumberVariable', 'loja_nivel', '>=', 'loja_max')],
           [S(f'{L}.val', '"MAX"'), S(f'{L}.val_cor', GS('ui_cor_ouro')), S(f'{L}.rot_cor', GS('ui_cor_dim'))]),
    ]))
    for e in todos(folha(d, 'Loja')['events']):
        for i, c in enumerate(e.get('conditions', [])):
            if c['type']['value'] == 'SourisSurObjet' and c['parameters'][0] == 'loja_linha':
                e['conditions'][i] = cmp('ui_mouse_lin', '>=', '0')
        for a in e.get('actions', []):
            if a['parameters'] == ['loja_sel', '=', 'loja_linha.indice']:
                a['parameters'] = ['loja_sel', '=', 'ui_mouse_lin']


def eventos(d, niveis):
    folha(d, 'Hubs')['events'].append(grupo('Atributos', [
        *criacao(), *contas(niveis), *cartoes(), *mouse(),
        *linhas_arma('arma', 'stats_arma[GlobalVariableString(arma_atual)].atual',
                     'stats_arma[GlobalVariableString(stats_hover)].atual'),
        *linhas_arma('larma', 'stats_arma[GlobalVariableString(arma_atual)].atual',
                     'stats_arma[GlobalVariableString(arma_atual)].novo'),
        *linhas_pato(), *desenho(), *pecas(), *teclas(), *esconde()]))
    # o evento da dica das armas (já escolhe a mais próxima) avisa o cartão do pedestal
    dica = next(e for e in todos(acha(folha(d, 'Hubs')['events'], 'Armas no hub')['events'])
                if any(c['type']['value'] == 'PickNearest' for c in e.get('conditions', [])))
    dica['actions'] += [X('SetStringVariable', 'stats_hover', '=', 'expositor_arma.arma'),
                        X('SetNumberVariable', 'stats_px', '=', 'expositor_arma.CenterX()'),
                        X('SetNumberVariable', 'stats_py', '=', 'expositor_arma.Y()'),
                        X('SetBooleanVariable', 'stats_ver_arma', 'True', '')]


def migra(d):
    niveis = variaveis(d)
    objetos(d)
    eventos(d, niveis)
    loja_linhas(d)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'ui_txt') is not None, 't190')
