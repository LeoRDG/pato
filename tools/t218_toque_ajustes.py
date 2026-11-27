"""Tarefa 218: ajustes nos controles de toque (t216) depois de jogar no celular.

- Pulo só pelo botão: empurrar o analógico para cima pulava e deixava toque.pulo ligado enquanto o dedo ficava em
  cima, então o botão de pulo não dava um aperto novo (pulo_agora) e não pulava. Sai o pulo pelo analógico (eventos
  e variáveis pulo_no_analogico, pulo_solta, pulo_analogico). No Paraíso, empurrar para cima continua subindo no voo.
- Tiro sozinho: um toque que começa com o toque simulando o mouse (dentro da loja, ou tocando para continuar no
  Resultado) aperta o botão esquerdo do mouse no GDevelop; se a simulação desliga antes do dedo sair (fechar a loja,
  entrar numa cena com o pato), o touchend não solta mais o botão e o pato atira para sempre. Agora, ao desligar a
  simulação, o botão do mouse preso é solto.
- Sem botão de recarga (a arma já recarrega sozinha quando o pente acaba; r no teclado continua).
- O botão E só aparece (e só pega toque) quando há o que usar: loja aberta, mercador perto, portal de E aberto ou
  arma no pedestal ao alcance (toque.usar_pode).
- Analógicos mais apagados: parados em opacidade_repouso (era 70) e tocados em opacidade_analogico (nova), em vez de
  opacidade_ativa dos botões.
Arte nova dos botões de pulo e dash em tools/arte_toque.py.
Rodar uma vez:  python3 tools/t218_toque_ajustes.py
"""
from gd_mig import *

T = 'toque'
VARS_SAI = ['pulo_no_analogico', 'pulo_solta', 'pulo_analogico', 'recarga_dir', 'recarga_baixo', 'recarga_id']
NOVAS = [('usar_pode', False), ('opacidade_analogico', 110)]
REPOUSO_VELHO, REPOUSO_NOVO = 70, 25

SOLTA_MOUSE = [
    '// Desliga o toque simulando o mouse (fora da loja). Um toque que começou com a simulação ligada apertou o botão',
    '// esquerdo do mouse, e com ela desligada o touchend não o solta mais: o pato atiraria para sempre (t218).',
    'const im = runtimeScene.getGame().getInputManager();',
    'if (im.isSimulatingMouseWithTouch()) {',
    '  im.touchSimulateMouse(false);',
    '  const esq = gdjs.InputManager.MOUSE_LEFT_BUTTON;',
    '  if (im.isMouseButtonPressed(esq)) im.onMouseButtonReleased(esq);',
    '}',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': list(linhas), 'parameterObjects': '',
            'useStrict': True, 'eventsSheetExpanded': False}


def txt_de(lista):
    return json.dumps(lista, ensure_ascii=False)


def tira_recarga_e_pulo_analogico(evs):
    """apaga eventos/ações do botão de recarga e do pulo pelo analógico (recursivo)."""
    novos = []
    for e in evs:
        c, a = txt_de(e.get('conditions', [])), txt_de(e.get('actions', []))
        if ('recarga' in c or 'toque.pulo_analogico' in c or 'toque.pulo_no_analogico' in c or 'toque.pulo_solta' in c
                or '"papel", "=", "\\"recarga\\""' in a):
            continue
        if 'actions' in e:
            e['actions'] = [x for x in e['actions']
                            if 'toque.recarga_id' not in txt_de(x) and 'toque.pulo_analogico' not in txt_de(x)]
        if e.get('events'):
            e['events'] = tira_recarga_e_pulo_analogico(e['events'])
        novos.append(e)
    return novos


def pode_usar():
    s = lambda v: csetb(f'{T}.usar_pode', v)
    return [
        ev([], [s(False)]),
        ev([cbol('loja_aberta', True)], [s(True)]),
        ev([X('StringObjectVariable', 'trader', 'estado', '=', '"calmo"'), bol('trader', 'morto', False),
            cmp('abs(trader.CenterX() - pato.CenterX())', '<=', 'trader.loja_raio'),
            cmp('abs(trader.Y() + trader.Height() - pato.Y() - pato.Height())', '<=', 'trader.loja_raio')], [s(True)]),
        ev([X('CollisionNP', 'pato', 'portal', '', '', ''), bol('portal', 'entrar_com_e', True),
            bol('portal', 'aberto', True), bol('pato', 'morto', False), bol('pato', 'na_loja', False)], [s(True)]),
        ev([bol('pato', 'na_loja', False), X('Visible', 'expositor_arma'),
            X('Distance', 'expositor_arma', 'pato', 'pato.arma_raio', '')], [s(True)]),
    ]


def migra(d):
    toque = next(v for v in d['variables'] if v['name'] == T)
    filhos = toque['children']
    rep = next(c for c in filhos if c['name'] == 'opacidade_repouso')
    if rep.get('value') == REPOUSO_VELHO:               # só se o usuário não mexeu
        rep['value'] = REPOUSO_NOVO
    toque['children'] = [c for c in filhos if c['name'] not in VARS_SAI]
    poe_vars(Ids('t218'), toque['children'], 'global/toque', NOVAS)

    # arte: o botão de recarga sai
    botao = objeto(d, 'toque_botao')
    botao['animations'] = [a for a in botao['animations'] if a['name'] != 'recarga']
    d['resources']['resources'] = [r for r in d['resources']['resources'] if r['name'] != 'assets/toque/botao_recarga.png']

    g = acha(folha(d, 'Jogador')['events'], 'Toque (celular)')
    assert g['events'][0]['comment'].startswith('Controles de toque (t215, reformados na t216)'), 'o grupo mudou'
    g['events'][0]['comment'] = g['events'][0]['comment'].replace('(pulo grande, dash, recarga, E)', '(pulo grande, dash, E)') \
        .replace('Analógico esquerdo anda (para cima também pula)', 'Analógico esquerdo anda (pulo só pelo botão, t218)') \
        + ' t218: E só aparece quando há o que usar (usar_pode); sem botão de recarga (recarrega sozinha).'
    g['events'] = tira_recarga_e_pulo_analogico(g['events'])

    q = next(e for e in g['events'] if '"pato", "na_loja", "True"' not in txt_de(e.get('conditions', []))
             and any(c['type']['value'] == 'BuiltinCommonInstructions::CompareNumbers'
                     and c['parameters'][0] == 'SceneInstancesCount(pato)' and c['parameters'][1] == '>'
                     for c in e.get('conditions', [])) and len(e.get('events', [])) > 20)['events']

    # simulação do mouse: desligar solta o botão preso
    for e in q:
        if (e['type'] == 'BuiltinCommonInstructions::ForEach' and '"na_loja", "False"' in txt_de(e['conditions'])
                and txt_de(e['actions']) == txt_de([X('TouchSimulateMouse', '', 'no')])):
            e['actions'] = []
            e['events'] = [js(SOLTA_MOUSE)]
            break
    else:
        raise SystemExit('evento do TouchSimulateMouse "no" não encontrado')

    # E só quando há o que usar: calcula antes dos toques novos, e o toque só vai para o E se puder
    i_novos = next(i for i, e in enumerate(q) if e['type'] == 'BuiltinCommonInstructions::Repeat')
    q[i_novos:i_novos] = pode_usar()
    for e in todos(q):
        a = txt_de(e.get('actions', []))
        if 'toque.qual' in a and '"\\"usar\\""' in a and 'toque.melhor' in a:
            e['conditions'].append(cbol(f'{T}.usar_pode', True))
    q += [ev([cbol(f'{T}.usar_pode', False), txt('toque_botao', 'papel', 'usar')], [X('Hide', 'toque_botao')]),
          ev([cbol(f'{T}.usar_pode', True), txt('toque_botao', 'papel', 'usar')], [X('Show', 'toque_botao')])]

    # analógicos tocados ficam em opacidade_analogico (os botões continuam em opacidade_ativa)
    for e in todos(q):
        if '"toque_base", "papel"' in txt_de(e.get('conditions', [])) or '"toque_alavanca", "papel"' in txt_de(e.get('conditions', [])):
            for x in e.get('actions', []):
                if x['type']['value'] == 'OpacityCapability::OpacityBehavior::SetValue' and x['parameters'][3] == f'{T}.opacidade_ativa':
                    x['parameters'][3] = f'{T}.opacidade_analogico'


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'usar_pode' for v in d['variables'] if v['name'] == T
                              for c in v['children']), 't218')
