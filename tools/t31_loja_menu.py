"""Tarefa 31: eventos externos 'Loja' (ligados por último no Hub): dica, abrir/fechar, menu montado do catálogo e compra.

O menu não conhece nenhum upgrade: tudo vem de loja_catalogo (global). Cada linha lê o nível em upgrades[id]
(ou armas[id] se tipo = "arma"), o preço = round(preco_base * pow(preco_mult, nivel)) e o bloqueio por 'requer'.
Teclas: E abre/fecha perto do mercador calmo, Esc fecha, W/S ou mouse escolhem, Espaço ou clique compra.
Abrir/fechar passa por loja_acao ("abrir"/"fechar"), que outros eventos (mercador hostil) também podem pedir.
Rodar uma vez:  python3 tools/t31_loja_menu.py   (feche o projeto no GDevelop antes)
"""
from migra import carrega, salva, var, adiciona_var, cena, externo, C, A, E, comentario, grupo

N = 'GlobalVariableChildCount(loja_catalogo)'
ESQ = 'CameraBorderLeft("HUD")'
TOPO = 'CameraBorderTop("HUD")'
ITEM = 'loja_catalogo[loja_linha.indice]'

ESTADO_SCENA = dict(loja_acao='', loja_id='', loja_tipo='', loja_req='', loja_nivel=0, loja_max=0, loja_preco=0, loja_bloq=0,
                    loja_texto='', loja_sel_id='', loja_sel_tipo='', loja_sel_nivel=0, loja_sel_max=0, loja_sel_preco=0,
                    loja_sel_bloq=0)


def S(var_, op, valor):
    return A('SetNumberVariable', var_, op, valor)


def T(var_, valor):
    return A('SetStringVariable', var_, '=', valor)


def anim(obj, nome):
    return A('AnimatableCapability::AnimatableBehavior::SetName', obj, 'Animation', '=', f'"{nome}"')


def texto(obj, valor):
    return A('TextContainerCapability::TextContainerBehavior::SetValue', obj, 'Text', '=', valor)


def str_igual(expr, valor, op='='):
    return C('BuiltinCommonInstructions::CompareStrings', expr, op, valor)


def perto_do_mercador():
    return [C('StringObjectVariable', 'trader', 'estado', '=', '"calmo"'),
            C('BooleanObjectVariable', 'trader', 'morto', 'False', ''),
            C('Distance', 'trader', 'pato', 'trader.loja_raio', '')]


def eventos():
    dica = grupo('Dica', [
        comentario('Um "E" aparece sobre o mercador calmo quando o pato está perto e a loja está fechada.'),
        E([C('SceneJustBegins', '')], [A('Create', '', 'loja_dica', 'trader.CenterX()', 'trader.Y()', ''),
                                       A('ChangePlan', 'loja_dica', '=', '900')]),
        E([], [A('Hide', 'loja_dica')]),
        E(perto_do_mercador() + [C('BooleanVariable', 'loja_aberta', 'False', '')],
          [A('Show', 'loja_dica', ''),
           A('SetXY', 'loja_dica', '=', 'trader.CenterX() - loja_dica.Width() / 2', '=', 'trader.Y() - loja_dica.Height() - 8')]),
    ])

    abrir_linhas = E([], [
        A('Create', '', 'loja_linha', f'{ESQ} + loja_x', f'{TOPO} + loja_y + loja_i * loja_linha_alt', '"HUD"'),
        A('SetNumberObjectVariable', 'loja_linha', 'indice', '=', 'loja_i'),
        A('ChangePlan', 'loja_linha', '=', '1000'),
        S('loja_i', '+', '1'),
    ], tipo='BuiltinCommonInstructions::Repeat', repeatExpression=N)

    abrir_fechar = grupo('Abrir e fechar', [
        comentario('E abre perto do mercador calmo e fecha; Esc fecha. Quem quiser abrir/fechar a loja muda loja_acao.'),
        E([C('KeyFromTextJustPressed', '', '"e"')], [], [
            E([C('BooleanVariable', 'loja_aberta', 'True', '')], [T('loja_acao', '"fechar"')]),
            E([C('BooleanVariable', 'loja_aberta', 'False', '')] + perto_do_mercador(), [T('loja_acao', '"abrir"')]),
        ]),
        E([C('KeyFromTextJustPressed', '', '"Escape"'), C('BooleanVariable', 'loja_aberta', 'True', '')],
          [T('loja_acao', '"fechar"')]),
        E([C('StringVariable', 'loja_acao', '=', '"abrir"')], [
            A('SetBooleanVariable', 'loja_aberta', 'True', ''),
            A('SetBooleanObjectVariable', 'pato', 'na_loja', 'True', ''),
            S('loja_sel', '=', '0'),
            anim('trader', 'dialogo'),
            A('Create', '', 'loja_painel', '0', '0', '"HUD"'),
            A('ChangePlan', 'loja_painel', '=', '950'),
            S('loja_i', '=', '0'),
        ], [
            abrir_linhas,
            E([], [A('Create', '', 'loja_desc', f'{ESQ} + loja_x', f'{TOPO} + loja_y + {N} * loja_linha_alt + 16', '"HUD"'),
                   A('ChangePlan', 'loja_desc', '=', '1000'),
                   T('loja_acao', '""')]),
        ]),
        E([C('StringVariable', 'loja_acao', '=', '"fechar"')], [
            A('Delete', 'loja_painel', ''), A('Delete', 'loja_linha', ''), A('Delete', 'loja_desc', ''),
            A('SetBooleanVariable', 'loja_aberta', 'False', ''),
            A('SetBooleanObjectVariable', 'pato', 'na_loja', 'False', ''),
            T('loja_acao', '""'),
        ], [
            E([C('StringObjectVariable', 'trader', 'estado', '=', '"calmo"')], [anim('trader', 'idle')]),
        ]),
    ])

    aberta = C('BooleanVariable', 'loja_aberta', 'True', '')
    tem_itens = C('BuiltinCommonInstructions::CompareNumbers', N, '>', '0')
    cor = lambda nome: A('TextObject::ChangeColor', 'loja_linha', f'{nome}')
    linha = E([], [
        T('loja_id', f'GlobalVariableString({ITEM}.id)'),
        T('loja_tipo', f'GlobalVariableString({ITEM}.tipo)'),
        T('loja_req', f'GlobalVariableString({ITEM}.requer)'),
        S('loja_max', '=', f'GlobalVariable({ITEM}.nivel_max)'),
        S('loja_bloq', '=', '0'),
    ], [
        E([str_igual('loja_tipo', '"arma"')], [S('loja_nivel', '=', 'GlobalVariable(armas[loja_id])')]),
        E([str_igual('loja_tipo', '"arma"', '!=')], [S('loja_nivel', '=', 'GlobalVariable(upgrades[loja_id])')]),
        E([], [S('loja_preco', '=', f'round(GlobalVariable({ITEM}.preco_base) * pow(GlobalVariable({ITEM}.preco_mult), loja_nivel))'),
               T('loja_texto', f'GlobalVariableString({ITEM}.nome) + "   " + ToString(loja_nivel) + "/" + ToString(loja_max) + "   "')]),
        E([str_igual('loja_req', '""', '!='),
           C('BuiltinCommonInstructions::CompareNumbers', 'GlobalVariable(upgrades[loja_req])', '<', '1')],
          [S('loja_bloq', '=', '1')]),
        comentario('Texto e cor: a última regra que vale ganha (selecionada > bloqueada > no máximo > cara > ok).'),
        E([], [texto('loja_linha', 'loja_texto + ToString(loja_preco) + " moedas"'), cor('loja_cor_ok')]),
        E([C('NumberVariable', 'moedas_total', '<', 'loja_preco')], [cor('loja_cor_caro')]),
        E([C('NumberVariable', 'loja_nivel', '>=', 'loja_max')], [texto('loja_linha', 'loja_texto + "MÁX"'), cor('loja_cor_max')]),
        E([C('NumberVariable', 'loja_bloq', '=', '1')], [texto('loja_linha', 'loja_texto + "precisa de " + loja_req'),
                                                         cor('loja_cor_bloq')]),
        E([C('NumberObjectVariable', 'loja_linha', 'indice', '=', 'loja_sel')], [
            cor('loja_cor_sel'),
            T('loja_sel_id', 'loja_id'), T('loja_sel_tipo', 'loja_tipo'),
            S('loja_sel_nivel', '=', 'loja_nivel'), S('loja_sel_max', '=', 'loja_max'),
            S('loja_sel_preco', '=', 'loja_preco'), S('loja_sel_bloq', '=', 'loja_bloq'),
        ]),
    ], tipo='BuiltinCommonInstructions::ForEach', object='loja_linha')

    menu = grupo('Menu', [
        comentario('W/S ou o mouse escolhem a linha. Cada linha é recalculada a partir do catálogo a cada quadro.'),
        E([aberta, tem_itens, C('KeyFromTextJustPressed', '', '"w"')], [S('loja_sel', '=', f'mod(loja_sel - 1 + {N}, {N})')]),
        E([aberta, tem_itens, C('KeyFromTextJustPressed', '', '"s"')], [S('loja_sel', '=', f'mod(loja_sel + 1, {N})')]),
        E([aberta, C('SourisSurObjet', 'loja_linha', '', 'yes')], [S('loja_sel', '=', 'loja_linha.indice')]),
        E([aberta], [A('PrimitiveDrawing::Rectangle', 'loja_painel', f'{ESQ} + loja_x - 24', f'{TOPO} + loja_y - 24',
                       f'{ESQ} + loja_x + loja_largura', f'{TOPO} + loja_y + {N} * loja_linha_alt + 72'),
                     texto('loja_desc', f'GlobalVariableString(loja_catalogo[loja_sel].descricao)')]),
        linha,
    ])

    ou = C('BuiltinCommonInstructions::Or')
    ou['subInstructions'] = [C('KeyFromTextJustPressed', '', '"Space"'), C('MouseButtonFromTextReleased', '', '"Left"')]
    compra = grupo('Compra', [
        comentario('Espaço ou clique compra a linha selecionada se não estiver no máximo, nem bloqueada, e houver moedas.'),
        E([aberta, ou, C('NumberVariable', 'loja_sel_bloq', '=', '0'),
           C('NumberVariable', 'loja_sel_nivel', '<', 'loja_sel_max'),
           C('NumberVariable', 'moedas_total', '>=', 'loja_sel_preco')], [
            S('moedas_total', '-', 'loja_sel_preco'),
            A('SetBooleanObjectVariable', 'pato', 'reaplicar_upgrades', 'True', ''),
            anim('trader', 'aprovado'),
        ], [
            E([str_igual('loja_sel_tipo', '"arma"')], [A('SetBooleanVariable', 'armas[loja_sel_id]', 'True', '')]),
            E([str_igual('loja_sel_tipo', '"arma"', '!=')], [S('upgrades[loja_sel_id]', '+', '1')]),
        ]),
        E([C('AnimatableCapability::AnimatableBehavior::Name', 'trader', 'Animation', '=', '"aprovado"'),
           C('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', 'trader', 'Animation')], [anim('trader', 'idle')], [
            E([aberta], [anim('trader', 'dialogo')]),
        ]),
    ])

    mercador = grupo('Mercador', [comentario('Mercador como inimigo secreto (tarefa 32).')])
    barra = grupo('Barra do mercador', [comentario('Barra de vida do mercador hostil (tarefa 32).')])
    return [comentario('Loja do Hub: o menu é montado a partir da global loja_catalogo. Para criar um upgrade, adicione um item lá.'),
            dica, abrir_fechar, menu, compra, mercador, barra]


def main():
    d = carrega()
    if externo(d, 'Loja'):
        print('Loja já existe; nada feito'); return
    hub = cena(d, 'Hub')
    for k, v in ESTADO_SCENA.items():
        adiciona_var(hub['variables'], var(k, v))
    d['externalEvents'].append({'associatedLayout': 'Hub', 'name': 'Loja', 'events': eventos()})
    hub['events'].append({'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'Loja'})
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
