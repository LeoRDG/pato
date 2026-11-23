"""Tarefa 126: ondas do cutulu para os dois lados, golpes corpo a corpo que acertam e aviso certo para cada ataque.

1. Ondas: as duas eram criadas na mesma lista de ações, e no GDevelop o segundo Create soma à seleção do primeiro;
   as ações da onda da esquerda (posição, força para a esquerda, espelhar) iam também para a da direita, então as
   duas saíam pela esquerda. Cada onda passa para o seu próprio subevento.
2. Golpes: ataque_1 (rasgo de energia) e ataque_2 (chicote de tentáculos) só tocavam como aviso, sem acertar nada.
   Viram ataques: com o pato a até golpe_escolha_dist px, com chance golpe_chance, o sorteio pega o rasgo (7) ou o
   chicote (8), sem repetir. Cada golpe acerta uma vez entre *_ini e *_fim s (os quadros em que a arte vai para a
   frente), numa caixa à frente do corpo: *_alcance da largura a partir do centro, entre *_topo e *_base da altura
   (medidas dos quadros). Dano *_dano, empurrão golpe_coice; termina em *_duracao s (a animação inteira). Ele fica
   virado para o lado em que começou (direcao).
3. Aviso: o salto agora é escolhido como 9 no "preparar" (para Inimigos não tocar o chicote como aviso) e vira 2 ao
   pular. No preparar: salto, mergulho, espiral e invocação batem as asas (voando); chuva fica parado (idle); os
   golpes mostram o 2º quadro do próprio golpe parado (a energia ou os tentáculos se juntando). Rugido e invocação
   batem as asas em vez de tocar o rasgo; o combo prepara com idle.
Só adiciona variáveis que não existem; o resto da folha Cutulu fica.
Rodar uma vez:  python3 tools/t126_cutulu_golpes.py
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARS = [
    ('golpe_escolha_dist', 380), ('golpe_chance', 0.7), ('golpe_coice', 600), ('golpe_acertou', False),
    ('rasgo_ini', 0.16), ('rasgo_fim', 0.4), ('rasgo_duracao', 0.56), ('rasgo_alcance', 0.47),
    ('rasgo_topo', 0.35), ('rasgo_base', 0.69), ('rasgo_dano', 22),
    ('chicote_ini', 0.24), ('chicote_fim', 0.56), ('chicote_duracao', 0.72), ('chicote_alcance', 0.5),
    ('chicote_topo', 0.41), ('chicote_base', 0.63), ('chicote_dano', 18),
]
_N = [0]


def uid():
    _N[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogo/t126/{_N[0]}'))


def X(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acoes}
    if filhos:
        e['events'] = filhos
    return e


def cada(conds, acoes, filhos=None):
    e = ev(conds, acoes, filhos)
    e['type'] = 'BuiltinCommonInstructions::ForEach'
    e['object'] = 'cutulu'
    return e


def num(v, op, val):  return X('NumberObjectVariable', 'cutulu', v, op, val)
def txt(v, val):      return X('StringObjectVariable', 'cutulu', v, '=', f'"{val}"')
def bol(v, val):      return X('BooleanObjectVariable', 'cutulu', v, 'True' if val else 'False', '')
def cmp(a, op, b):    return X('BuiltinCommonInstructions::CompareNumbers', a, op, b)
def setn(v, op, val): return X('SetNumberObjectVariable', 'cutulu', v, op, val)
def sets(v, val):     return X('SetStringObjectVariable', 'cutulu', v, '=', f'"{val}"')
def setb(v, val):     return X('SetBooleanObjectVariable', 'cutulu', v, 'True' if val else 'False', '')
def anim(n):          return X('AnimatableCapability::AnimatableBehavior::SetName', 'cutulu', 'Animation', '=', f'"{n}"')
def quadro(i):        return X('AnimatableCapability::AnimatableBehavior::SetIndex', 'cutulu', 'Animation', '=', i)
PAUSA = X('AnimatableCapability::AnimatableBehavior::PauseAnimation', 'cutulu', 'Animation')
TOCA = X('AnimatableCapability::AnimatableBehavior::PlayAnimation', 'cutulu', 'Animation')
VIVO = bol('morto', False)


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def coment(t):
    return {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0,
            'textG': 0, 'textR': 0}, 'comment': t, 'comment2': ''}


def golpe(nome, som):
    p = f'cutulu.{nome}_'
    frente = '(pato.CenterX() - cutulu.CenterX()) * cutulu.direcao'
    return cada([VIVO, txt('estado', nome)], [], [
        ev([cmp('cutulu.direcao', '<', '0')], [X('FlippableCapability::FlippableBehavior::FlipX', 'cutulu',
                                                 'Flippable', 'yes')]),
        ev([cmp('cutulu.direcao', '>', '0')], [X('FlippableCapability::FlippableBehavior::FlipX', 'cutulu',
                                                 'Flippable', 'no')]),
        ev([bol('golpe_acertou', False),
            X('CompareObjectTimer', 'cutulu', '"estado"', '>', p + 'ini'),
            X('CompareObjectTimer', 'cutulu', '"estado"', '<', p + 'fim'),
            cmp(f'{frente} - pato.Width() / 2', '<', f'{p}alcance * cutulu.Width()'),
            cmp(f'{frente} + pato.Width() / 2', '>', '0'),
            cmp('pato.Y()', '<', f'cutulu.Y() + cutulu.Height() * {p}base'),
            cmp('pato.Y() + pato.Height()', '>', f'cutulu.Y() + cutulu.Height() * {p}topo'),
            X('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
            X('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
           [setb('golpe_acertou', True),
            X('SetNumberObjectVariable', 'pato', 'vida', '-', p + 'dano'),
            X('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
            X('ResetObjectTimer', 'pato', '"iframes"'),
            X('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', '"cutulu"'),
            X('SetNumberObjectVariable', 'pato', 'coice_vx', '=', 'cutulu.direcao * cutulu.golpe_coice'),
            X('PlaySound', '', som, '', '70', '0.8')]),
        ev([X('CompareObjectTimer', 'cutulu', '"estado"', '>', p + 'duracao')],
           [sets('estado', 'perseguir'), X('ResetObjectTimer', 'cutulu', '"estado"'),
            X('ResetObjectTimer', 'cutulu', '"ataque"'), setb('firme', False), setb('fim_ataque', True),
            anim('caminhando')]),
    ])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cut = next(o for o in d['objects'] if o['name'] == 'cutulu')
    if any(v['name'] == 'golpe_acertou' for v in cut['variables']):
        sys.exit('t126 já foi aplicada; não roda de novo.')
    for n, v in VARS:
        if not any(x['name'] == n for x in cut['variables']):
            cut['variables'].append({'name': n, 'persistentUuid': uid(),
                                     'type': 'boolean' if isinstance(v, bool) else 'number', 'value': v})
    folha = next(x for x in d['externalEvents'] if x['name'] == 'Cutulu')
    grupos = {e.get('name'): e for e in folha['events']}

    # 1. cada onda no seu subevento
    partidas = 0
    for e in todos(folha['events']):
        acs = e.get('actions', [])
        ini = [i for i, a in enumerate(acs) if a['type']['value'] == 'Create' and a['parameters'][1] == 'projetil_inimigo'
               and i + 1 < len(acs) and acs[i + 1]['parameters'][3:4] == ['"onda_abissal"']]
        if len(ini) == 2:
            fim = ini[1] + (ini[1] - ini[0])
            blocos = [acs[ini[0]:ini[1]], acs[ini[1]:fim]]
            assert all(b[-1]['parameters'][1] == 'ttl' for b in blocos)
            e['actions'] = acs[:ini[0]] + acs[fim:]
            e['events'] = [ev([], b) for b in blocos] + (e.get('events') or [])
            partidas += 1
    assert partidas == 2, partidas

    # 3a. animações de rugido, invocação, chuva e combo
    trocas = {'rugido': 'voando', 'invocar': 'voando', 'chuva': 'idle'}
    for e in todos(folha['events']):
        acs = e.get('actions', [])
        est = [a['parameters'][3].strip('"') for a in acs
               if a['type']['value'] == 'SetStringObjectVariable' and a['parameters'][1] == 'estado']
        for a in acs:
            if a['type']['value'].endswith('::SetName') and a['parameters'][0] == 'cutulu':
                if est and est[0] in trocas:
                    a['parameters'][3] = f'"{trocas[est[0]]}"'
                if est == ['preparar'] and a['parameters'][3] == '"ataque_1"':
                    a['parameters'][3] = '"idle"'

    # 2 e 3b. sorteio: golpes perto do pato, salto vira 9 no preparar, animação de aviso
    sorteio = next(e for e in grupos['Escolha do ataque']['events']
                   if e.get('type', '').endswith('ForEach') and 'sorteado' in json.dumps(e['actions']))
    filhos = sorteio['events']
    i_formula = next(i for i, e in enumerate(filhos) if 'mod(' in json.dumps(e['actions']))
    filhos.insert(i_formula + 1, ev(
        [cmp('abs(pato.CenterX() - cutulu.CenterX())', '<', 'cutulu.golpe_escolha_dist'),
         cmp('RandomFloat(1)', '<', 'cutulu.golpe_chance')],
        [setn('escolha', '=', '7 + RandomInRange(0, 1)')],
        [ev([cmp('cutulu.escolha', '=', 'cutulu.ultima_escolha')], [setn('escolha', '=', '15 - cutulu.escolha')])]))
    filhos += [
        ev([num('escolha', '=', '2')], [setn('escolha', '=', '9')]),
        ev([num('escolha', '=', '9')], [anim('voando'), TOCA]),
        ev([num('escolha', '=', '3')], [anim('voando'), TOCA]),
        ev([num('escolha', '=', '4')], [anim('voando'), TOCA]),
        ev([num('escolha', '=', '6')], [anim('voando'), TOCA]),
        ev([num('escolha', '=', '5')], [anim('idle'), TOCA]),
        ev([num('escolha', '=', '7')], [anim('ataque_1'), quadro('1'), PAUSA]),
        ev([num('escolha', '=', '8')], [anim('ataque_2'), quadro('1'), PAUSA]),
    ]
    grupos['Escolha do ataque']['events'][0]['comment'] += (
        ' Com o pato a até golpe_escolha_dist px, chance golpe_chance de um golpe (7 rasgo, 8 chicote). O salto fica '
        '9 no preparar e vira 2 ao pular.')

    # começo: 9 pula (as ações do salto de Inimigos), 7 e 8 golpeiam
    ini = next(e for e in grupos['Começo dos ataques novos']['events']
               if e.get('type', '').endswith('ForEach'))
    ini['actions'].append(TOCA)
    ext = {x['name']: x for x in d['externalEvents']}
    salto = next(e for e in todos(ext['Inimigos']['events'])
                 if any(a['type']['value'] == 'PlatformBehavior::SimulateJumpKey' and a['parameters'][0] == 'cutulu'
                        for a in e.get('actions', [])))
    ini['events'].insert(0, ev([num('escolha', '=', '9')],
                               [setn('escolha', '=', '2'), setb('firme', False)] + copy.deepcopy(salto['actions'])))
    for n, a, som in ((7, 'ataque_1', 'som_investida.wav'), (8, 'ataque_2', 'som_lingua.wav')):
        nome = 'rasgo' if n == 7 else 'chicote'
        ini['events'].append(ev([num('escolha', '=', str(n))],
                                [sets('estado', nome), anim(a), quadro('0'), setb('golpe_acertou', False),
                                 setn('direcao', '=', 'sign(pato.CenterX() - cutulu.CenterX() + 0.001)'),
                                 X('PlaySound', '', som, '', '70', '0.7')]))
    pos = folha['events'].index(grupos['Começo dos ataques novos']) + 1
    folha['events'].insert(pos, {
        'type': 'BuiltinCommonInstructions::Group', 'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0,
        'name': 'Golpes', 'source': '', 'parameters': [], 'events': [
            coment('Rasgo (ataque_1) e chicote (ataque_2): acertam uma vez entre *_ini e *_fim s, numa caixa à frente '
                   'do corpo (*_alcance da largura a partir do centro, entre *_topo e *_base da altura). Fica virado '
                   'para direcao. Termina em *_duracao s.'),
            golpe('rasgo', 'som_impacto.wav'), golpe('chicote', 'som_impacto.wav')]})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cutulu: ondas separadas, golpes rasgo e chicote')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
