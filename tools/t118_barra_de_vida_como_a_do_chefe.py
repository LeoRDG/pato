"""Tarefa 118: barra de vida dos inimigos igual à do chefe (sem moldura), em cima da cabeça.

A barrinha (barra_de_vida, PanelSpriteContinuousBar) tinha moldura branca grossa. A do chefe são três faixas lisas
do mesmo tamanho, uma em cima da outra: trilho (hud/boss_trilho.png, branco translúcido), rastro (branco, vai
encolhendo depois do dano) e preenchimento (vermelho). Três objetos novos copiados delas, na pasta efeitos:
inimigo_barra_trilho, inimigo_barra_rastro e inimigo_barra_fill, com o Sticker da barra antiga (somem com o inimigo).
Cada inimigo com barra cria os três, ligados a ele. Todo quadro, para cada Personagem com barra:
- largura cheia = clamp(largura da caixa de colisão * barra_fator, barra_min, barra_max), altura barra_altura,
  centrada no meio da caixa de colisão, barra_folga px acima do topo;
- preenchimento = largura cheia * vida / max_vida; o rastro encolhe até ele a barra_rastro_vel px/s.
Variáveis no inimigo_barra_fill: barra_fator, barra_min, barra_max e barra_folga com os valores atuais da barra
antiga, barra_altura 6 (sem moldura, a barra inteira é a faixa; a do chefe tem 8) e barra_rastro_vel 60 (a do chefe
é 300 numa barra de 720 px). A barra_de_vida antiga deixa de ser criada (o objeto continua no projeto).
Rodar uma vez:  python3 tools/t118_barra_de_vida_como_a_do_chefe.py
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P, T, R, F = 'Personagem', 'inimigo_barra_trilho', 'inimigo_barra_rastro', 'inimigo_barra_fill'
MOLDES = {T: 'hud_boss_trilho', R: 'hud_boss_rastro', F: 'hud_boss_fill'}


def uid(n):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t118/' + n))


def x(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None, tipo='Standard', obj=None):
    e = {'type': 'BuiltinCommonInstructions::' + tipo, 'conditions': conds, 'actions': acoes}
    if obj:
        e['object'] = obj
    if filhos:
        e['events'] = filhos
    return e


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    O = {o['name']: o for o in d['objects']}
    if F in O:
        sys.exit('t118 já foi aplicada; não roda de novo.')
    for l in d['layouts']:                          # os moldes podem estar na cena (não são globais)
        for o in l.get('objects', []):
            if o['name'] in MOLDES.values() and o['name'] not in O:
                O[o['name']] = o
    velha = O['barra_de_vida']
    sticker = next(b for b in velha['behaviors'] if b['type'] == 'Sticker::Sticker')
    vv = {v['name']: v['value'] for v in velha['variables']}
    novos = []
    for nome, molde in MOLDES.items():
        o = copy.deepcopy(O[molde])
        o.update(name=nome, persistentUuid=uid('obj/' + nome), variables=[])
        o['behaviors'] = [b for b in o['behaviors'] if b['type'] != 'AnchorBehavior::AnchorBehavior'] + [copy.deepcopy(sticker)]
        novos.append(o)
    fill = novos[-1]
    for n, v in [('barra_fator', vv.get('barra_fator', 0.8)), ('barra_min', vv.get('barra_min', 36)),
                 ('barra_max', vv.get('barra_max', 110)), ('barra_altura', 6), ('barra_folga', vv.get('barra_folga', 8)),
                 ('barra_rastro_vel', 60), ('larg', 0)]:
        fill['variables'].append({'name': n, 'persistentUuid': uid('var/' + n), 'type': 'number', 'value': v})
    d['objects'] += novos

    def pasta(n):
        for c in n.get('children', []):
            if c.get('objectName') == 'barra_de_vida':
                return n
            if 'folderName' in c:
                r = pasta(c)
                if r:
                    return r
    pasta(d['objectsFolderStructure'])['children'] += [{'objectName': o['name']} for o in novos]

    com = next(e for e in d['externalEvents'] if e['name'] == 'Combate')['events']
    g = next(e for e in todos(com) if e.get('name') == 'Barra de Vida')
    cria = next(e for e in g['events'] if e['type'].endswith('ForEach') and e.get('object') == P)
    atual = next(e for e in g['events'] if e['type'].endswith('ForEach') and e.get('object') == 'barra_de_vida')
    acoes = [a for a in cria['actions'] if 'barra_de_vida' not in a['parameters']]   # fica o tem_barra_de_vida True
    for k, n in enumerate((T, R, F)):
        acoes += [x('Create', '', n, f'{P}.X()', f'{P}.Y()', ''),
                  x('LinkedObjects::LinkObjects', '', P, n),
                  x('Sticker::Sticker::Stick', n, 'Sticker', P, ''),
                  x('ChangePlan', n, '=', f'{P}.ZOrder() + {k + 1}')]
    cria['actions'] = acoes

    larg = f'{F}.larg'
    topo = f'{P}.BoundingBoxTop() - {F}.barra_folga - {F}.barra_altura'
    novo_atual = ev(
        [x('LinkedObjects::PickObjectsLinkedTo', '', T, P, ''), x('LinkedObjects::PickObjectsLinkedTo', '', R, P, ''),
         x('LinkedObjects::PickObjectsLinkedTo', '', F, P, '')],
        [x('SetNumberObjectVariable', F, 'larg', '=',
           f'clamp(({P}.BoundingBoxRight() - {P}.BoundingBoxLeft()) * {F}.barra_fator, {F}.barra_min, {F}.barra_max)'),
         x('ResizableCapability::ResizableBehavior::SetWidth', T, 'Resizable', '=', larg),
         x('ResizableCapability::ResizableBehavior::SetHeight', T, 'Resizable', '=', f'{F}.barra_altura'),
         x('SetXY', T, '=', f'{P}.BoundingBoxCenterX() - {larg} / 2', '=', topo),
         x('ResizableCapability::ResizableBehavior::SetWidth', F, 'Resizable', '=',
           f'{larg} * clamp({P}.vida / {P}.max_vida, 0, 1)'),
         x('ResizableCapability::ResizableBehavior::SetHeight', F, 'Resizable', '=', f'{F}.barra_altura'),
         x('SetXY', F, '=', f'{T}.X()', '=', f'{T}.Y()'),
         x('ResizableCapability::ResizableBehavior::SetWidth', R, 'Resizable', '=', f'min({R}.Width(), {larg})'),
         x('ResizableCapability::ResizableBehavior::SetHeight', R, 'Resizable', '=', f'{F}.barra_altura'),
         x('SetXY', R, '=', f'{T}.X()', '=', f'{T}.Y()')],
        [ev([x('BuiltinCommonInstructions::CompareNumbers', f'{R}.Width()', '>', f'{F}.Width()')],
            [x('ResizableCapability::ResizableBehavior::SetWidth', R, 'Resizable', '-', f'{F}.barra_rastro_vel * TimeDelta()')]),
         ev([x('BuiltinCommonInstructions::CompareNumbers', f'{R}.Width()', '<', f'{F}.Width()')],
            [x('ResizableCapability::ResizableBehavior::SetWidth', R, 'Resizable', '=', f'{F}.Width()')])],
        tipo='ForEach', obj=P)
    g['events'][g['events'].index(atual)] = novo_atual
    com_ev = next(e for e in g['events'] if e['type'].endswith('Comment'))
    com_ev['comment'] = ('Cria e atualiza a barrinha de vida em cima de cada inimigo, igual à do chefe: trilho, rastro e '
                         'preenchimento (inimigo_barra_*), ligados ao inimigo. Largura pela caixa de colisão (barra_fator, '
                         'barra_min, barra_max), altura barra_altura, barra_folga px acima; o rastro encolhe a '
                         'barra_rastro_vel px/s. O pato não tem, a vida dele fica no HUD.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('barra de vida como a do chefe')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
