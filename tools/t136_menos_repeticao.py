"""Tarefa 136: eventos repetidos viram um só (auditoria de repetição).

1. Perseguir o pato: condenado_azul, condenado_inchado e pigman tinham, dentro do estado "perseguir", o mesmo evento
   (longe mais que parar_dist: aperta para o lado do pato e quer_andar = True). Grupo de objetos Perseguidores e um
   evento só em Inimigos, logo depois de Estados (terrestres) (que pode trocar o estado antes, como antes). O
   condenado_em_chamas fica de fora: no frenesi ele fica em "perseguir" andando para frenesi_dir, não para o pato.
2. Investida: condenado_azul, pigman e roda_anjo tinham, no estado "atacar", o mesmo "anda para direcao". Grupo
   Investida e um evento só em Inimigos. Roda nesse ponto do quadro (antes da folha do reino), então no quadro em que
   a investida começa ou acaba a tecla é apertada um quadro antes ou depois.
3. Morte dos anjos: um evento por anjo -> um evento sobre o grupo Anjos (querubim, serafim, ofanim, roda_anjo).
4. Explosão de inimigo: condenado_inchado e mina_demoniaca tinham o mesmo dano em área no pato. Agora cada um só
   marca explodir = True (variável nova) e o dano fica num grupo no começo de Combate (mesmo quadro, depois das folhas
   dos inimigos), sobre o grupo Explosivos; ultimo_agressor = Explosivos.ObjectName() (o mesmo texto de antes).
5. Clarão do cano: um evento por arma -> um evento sobre o grupo Arma (animação = Arma.ObjectName(), que já eram os
   nomes das animações do flash_cano); o fogo extra da lança fica num evento à parte.
6. Cutulu: as ondas do chão (Mergulho e fim do salto) e o anel de bile (salto e rugido) eram copiados. Agora quem solta
   marca ondas_soltar / anel_soltar (variáveis novas) e um evento só solta, no mesmo quadro (o evento das ondas fica em
   Ondas do salto e combos, o do anel no fim de Preparo e fases, depois de onde as marcas são feitas).
7. Fase 2 do demônio: o golpe de cutelo, a explosão e a quebra grande tinham cada um o seu laço de quebrar tiles e
   soltar destroços. Agora cada um só diz a área (quebra_x0, quebra_x1, quebra_topo, quebra_qtd, quebra_tudo) e
   marca quebra_pedida; um grupo Quebrar o piso, logo depois da quebra grande, quebra: sorteando quebra_qtd tiles
   (quebra_qtd * quebra_tentativas tentativas) ou, com quebra_tudo, todos os tiles da área.
8. Hubs: Queda da borda era igual nos três hubs -> folha Hubs, ligada no lugar dela; o grupo Saída (só com um evento
   desativado) sai dos três.
Nenhum valor ajustável muda; as variáveis novas são de estado (começam em 0 / False).
Rodar uma vez:  python3 tools/t136_menos_repeticao.py
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_N = [0]


def uid():
    _N[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogo/t136/{_N[0]}'))


def X(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None, tipo='Standard', obj=None, rep=None):
    e = {'type': f'BuiltinCommonInstructions::{tipo}', 'conditions': conds, 'actions': acoes}
    if obj:
        e['object'] = obj
    if rep:
        e['repeatExpression'] = rep
    if filhos:
        e['events'] = filhos
    return e


def grupo(nome, evs):
    return {'type': 'BuiltinCommonInstructions::Group', 'colorB': 228, 'colorG': 176, 'colorR': 74,
            'creationTime': 0, 'name': nome, 'source': '', 'parameters': [], 'events': evs}


def acha(evs, nome):
    for e in evs:
        if e.get('name') == nome:
            return e
        r = acha(e.get('events') or [], nome)
        if r:
            return r
    return None


def todos(evs, pai=None):
    for e in evs:
        yield e, pai
        yield from todos(e.get('events') or [], e)


def txt(e):
    return json.dumps(e, sort_keys=True, ensure_ascii=False)


def troca_obj(e, de, para):
    """cópia do evento com o objeto `de` trocado por `para` (nome inteiro)."""
    import re
    return json.loads(re.sub(r'\b' + de + r'\b', para, txt(e)))


def addvar(obj, nome, tipo, valor):
    if not any(v['name'] == nome for v in obj['variables']):
        obj['variables'].append({'name': nome, 'persistentUuid': uid(), 'type': tipo, 'value': valor})


def anda_dir(o):
    return [ev([X('NumberObjectVariable', o, 'direcao', '<', '0')],
               [X('PlatformBehavior::SimulateLeftKey', o, 'PlatformerObject'),
                X('SetBooleanObjectVariable', o, 'quer_andar', 'True', '')]),
            ev([X('NumberObjectVariable', o, 'direcao', '>', '0')],
               [X('PlatformBehavior::SimulateRightKey', o, 'PlatformerObject'),
                X('SetBooleanObjectVariable', o, 'quer_andar', 'True', '')])]


def anda_pato(o):
    return ev([X('BuiltinCommonInstructions::CompareNumbers', f'abs(pato.CenterX() - {o}.CenterX())', '>',
                 f'{o}.parar_dist')], [], [
        ev([X('BuiltinCommonInstructions::CompareNumbers', f'pato.CenterX() - {o}.CenterX()', '<', '0')],
           [X('PlatformBehavior::SimulateLeftKey', o, 'PlatformerObject'),
            X('SetBooleanObjectVariable', o, 'quer_andar', 'True', '')]),
        ev([X('BuiltinCommonInstructions::CompareNumbers', f'pato.CenterX() - {o}.CenterX()', '>', '0')],
           [X('PlatformBehavior::SimulateRightKey', o, 'PlatformerObject'),
            X('SetBooleanObjectVariable', o, 'quer_andar', 'True', '')])])


def tira_filho(raiz, alvo_txt, n_esperado):
    """tira todo evento igual a alvo_txt (com os seus pais); devolve os pais."""
    pais = []
    for e, pai in list(todos(raiz)):
        if txt(e) == alvo_txt:
            pai['events'].remove(e)
            if not pai['events']:
                del pai['events']
            pais.append(pai)
    assert len(pais) == n_esperado, (len(pais), n_esperado, alvo_txt[:200])
    return pais


def migra(d):
    O = {o['name']: o for o in d['objects']}
    XE = {x['name']: x for x in d['externalEvents']}
    L = {l['name']: l for l in d['layouts']}
    grupos = {g['name'] for g in d['objectsGroups']}
    for g in ('Perseguidores', 'Investida', 'Anjos', 'Explosivos'):
        assert g not in grupos, f'grupo {g} já existe'

    def novo_grupo(nome, objs):
        d['objectsGroups'].append({'name': nome, 'objects': [{'name': n} for n in objs]})

    ini = XE['Inimigos']['events']
    i_terr = next(i for i, e in enumerate(ini) if e.get('name') == 'Estados (terrestres)')

    # 1. Perseguir o pato
    PERS = ['condenado_azul', 'condenado_inchado', 'pigman']
    for o in PERS:
        folha = 'InimigosPurgatorio' if o == 'pigman' else 'InimigosInferno'
        (pai,) = tira_filho(XE[folha]['events'], txt(anda_pato(o)), 1)
        assert pai['conditions'] == [X('StringObjectVariable', o, 'estado', '=', '"perseguir"')], pai['conditions']
    novo_grupo('Perseguidores', PERS)
    G = 'Perseguidores'
    pers = grupo('Perseguir o pato', [ev([X('BooleanObjectVariable', G, 'morto', 'False', ''),
                                          X('StringObjectVariable', G, 'estado', '=', '"perseguir"')], [],
                                         [anda_pato(G)], tipo='ForEach', obj=G)])

    # 2. Investida
    INV = ['condenado_azul', 'pigman', 'roda_anjo']
    folhas = {'condenado_azul': 'InimigosInferno', 'pigman': 'InimigosPurgatorio', 'roda_anjo': 'InimigosParaiso'}
    for o in INV:
        raiz = XE[folhas[o]]['events']
        ataque = [e for e, _ in todos(raiz)
                  if e.get('conditions') == [X('StringObjectVariable', o, 'estado', '=', '"atacar"')]
                  and txt(e.get('events') or []) == txt(anda_dir(o))]
        assert len(ataque) == 1, (o, len(ataque))
        e = ataque[0]
        del e['events']
        if not e['actions']:
            pai = next(p for x, p in todos(raiz) if x is e)
            pai['events'].remove(e)
    novo_grupo('Investida', INV)
    G = 'Investida'
    inv = grupo('Investida', [ev([X('BooleanObjectVariable', G, 'morto', 'False', ''),
                                  X('StringObjectVariable', G, 'estado', '=', '"atacar"')], [],
                                 anda_dir(G), tipo='ForEach', obj=G)])
    ini[i_terr + 1:i_terr + 1] = [pers, inv]

    # 3. Morte dos anjos
    ANJOS = ['querubim', 'serafim', 'ofanim', 'roda_anjo']
    morte = acha(XE['InimigosParaiso']['events'], 'Morte dos anjos (partículas de luz)')
    modelo = [troca_obj(e, a, 'Anjos') for e, a in zip(morte['events'], ANJOS)]
    assert len(morte['events']) == 4 and all(txt(m) == txt(modelo[0]) for m in modelo), 'anjos diferentes'
    novo_grupo('Anjos', ANJOS)
    morte['events'] = [modelo[0]]

    # 4. Explosão de inimigo
    EXP = {'condenado_inchado': 'InimigosInferno', 'mina_demoniaca': 'InimigosPurgatorio'}
    dano = None
    for o, folha in EXP.items():
        achados = [(e, p) for e, p in todos(XE[folha]['events'])
                   if any(c['type']['value'] == 'Distance' and c['parameters'][:3] == [o, 'pato', f'{o}.explosao_raio']
                          for c in e.get('conditions', []))]
        assert len(achados) == 1, (o, len(achados))
        e, pai = achados[0]
        norm = json.loads(txt(troca_obj(e, o, 'Explosivos'))
                          .replace('"\\"Explosivos\\""', '"Explosivos.ObjectName()"'))
        assert dano is None or txt(norm) == txt(dano), 'explosões diferentes'
        dano = norm
        i = pai['events'].index(e)
        pai['events'].pop(i)
        if not pai['events']:
            del pai['events']
        pai['actions'].append(X('SetBooleanObjectVariable', o, 'explodir', 'True', ''))
        addvar(O[o], 'explodir', 'boolean', False)
    assert 'Explosivos.ObjectName()' in txt(dano)
    novo_grupo('Explosivos', list(EXP))
    G = 'Explosivos'
    XE['Combate']['events'].insert(0, grupo('Explosão de inimigo', [
        ev([X('BooleanObjectVariable', G, 'explodir', 'True', '')],
           [X('SetBooleanObjectVariable', G, 'explodir', 'False', '')], [dano], tipo='ForEach', obj=G)]))

    # 5. Clarão do cano
    flash = acha(XE['Jogador']['events'], 'Muzzle Flash')
    armas = [e['conditions'][0]['parameters'][0] for e in flash['events']]
    assert sorted(armas) == ['doze', 'lanca', 'minigun', 'pistola'], armas
    base = None
    extra = None
    for e, a in zip(flash['events'], armas):
        n = json.loads(txt(e).replace(f'"\\"{a}\\""', '"Arma.ObjectName()"').replace(f'"{a}.', '"Arma.')
                       .replace(f'["{a}", "FireBullet"', '["Arma", "FireBullet"'))
        if a == 'lanca':
            extra = n['actions'][6:]
            n['actions'] = n['actions'][:6]
        assert base is None or txt(n) == txt(base), ('flash diferente', a)
        base = n
    assert [x['type']['value'] for x in extra] == ['Create', 'SetAngle'] and 'fogo_lanca' in txt(extra), extra
    assert txt(base).count('Arma') == 4 and 'pistola' not in txt(base)
    cond_lanca = copy.deepcopy(flash['events'][armas.index('lanca')]['conditions'])
    flash['events'] = [base, ev(cond_lanca, extra)]

    # 6. Cutulu
    cut = acha(XE['InimigosPurgatorio']['events'], 'Cutulu')
    c = O['cutulu']
    ondas_d = [e for e, _ in todos(cut['events'])
               if not e.get('conditions') and e.get('actions') and e['actions'][0]['type']['value'] == 'Create'
               and 'onda_abissal' in txt(e['actions'])]
    assert len(ondas_d) == 4, len(ondas_d)
    pares = {}
    for e, p in todos(cut['events']):
        if e in ondas_d:
            pares.setdefault(id(p), (p, []))[1].append(e)
    assert len(pares) == 2 and all(len(v[1]) == 2 for v in pares.values())
    (p1, o1), (p2, o2) = pares.values()
    assert txt(o1) == txt(o2)
    for p, os_ in ((p1, o1), (p2, o2)):
        i = p['events'].index(os_[0])
        assert p['events'][i + 1] is os_[1]
        del p['events'][i:i + 2]
        p['actions'].append(X('SetBooleanObjectVariable', 'cutulu', 'ondas_soltar', 'True', ''))
        if not p['events']:
            del p['events']
    addvar(c, 'ondas_soltar', 'boolean', False)
    ondas_g = acha(cut['events'], 'Ondas do salto e combos')
    assert any(p is p1 or p is p2 for p in ondas_g['events'])
    ondas_g['events'].insert(1, ev([X('BooleanObjectVariable', 'cutulu', 'ondas_soltar', 'True', '')],
                                   [X('SetBooleanObjectVariable', 'cutulu', 'ondas_soltar', 'False', '')],
                                   o1, tipo='ForEach', obj='cutulu'))

    aneis = [(e, p) for e, p in todos(cut['events'])
             if e['type'].endswith('Repeat') and e.get('repeatExpression') == 'cutulu.anel_qtd']
    assert len(aneis) == 2, len(aneis)
    blocos = []
    for e, p in aneis:
        i = p['events'].index(e)
        antes = p['events'][i - 1]
        assert antes.get('conditions') == [] and len(antes['actions']) == 1 and \
            antes['actions'][0]['parameters'][:2] == ['cutulu', 'i'], antes
        blocos.append(txt([antes, e]))
        del p['events'][i - 1:i + 1]
        if not p['events']:
            del p['events']
        p['actions'].append(X('SetBooleanObjectVariable', 'cutulu', 'anel_soltar', 'True', ''))
    assert blocos[0] == blocos[1]
    addvar(c, 'anel_soltar', 'boolean', False)
    prep = acha(cut['events'], 'Preparo e fases')
    andar = acha(cut['events'], 'Andar, salto e fúria')
    assert cut['events'].index(andar) < cut['events'].index(prep)
    prep['events'].append(ev([X('BooleanObjectVariable', 'cutulu', 'anel_soltar', 'True', '')],
                             [X('SetBooleanObjectVariable', 'cutulu', 'anel_soltar', 'False', '')],
                             json.loads(blocos[0]), tipo='ForEach', obj='cutulu'))

    # 7. Fase 2: um laço de quebrar o piso
    f2 = acha(XE['CenarioInferno']['events'], 'Fase 2')
    D = 'demonio_chefe'
    reqs = [e for e in f2['events'] if 'quebra_x1' in txt(e)]
    assert len(reqs) == 3
    cutelo, explo, grande = reqs
    assert '\\"cutelo\\"' in txt(cutelo['conditions']) and '\\"explosao\\"' in txt(explo['conditions']) \
        and '\\"grande\\"' in txt(grande['conditions'])

    def setup_de(e):
        (s,) = [s for s in e['events'] if any(a['parameters'][1] == 'quebra_x0' for a in s['actions']
                                               if a['type']['value'] == 'SetNumberObjectVariable')]
        return s
    sc, se, sg = setup_de(cutelo), setup_de(explo), setup_de(grande)
    par = lambda s, v: next(a['parameters'][3] for a in s['actions'] if a['parameters'][1] == v)
    assert txt(sc['events']) == txt(se['events'])
    laco_rand = sc['events'][0]                         # Repeat quebra_qtd * quebra_tentativas
    tira = laco_rand['events'][0]                       # tile existe -> remove, feitas + 1, destroços
    destrocos = tira['events'][0]
    assert destrocos.get('repeatExpression') == 'Variable(destroco_por_tile)'
    assert 'destroco_por_tile' in txt(sg) and txt(destrocos) in txt(sg)
    comum = ['quebra_c0', 'quebra_c1', 'quebra_r1']
    for v in comum:
        assert par(sc, v) == par(se, v) == par(sg, v), v
    assert par(sc, 'quebra_r0').endswith(' + Variable(quebra_topo_linhas)') and par(sg, 'quebra_r0').endswith(' + 0')

    def pedido(s, topo, qtd, tudo):
        a = [X('SetNumberObjectVariable', D, 'quebra_x0', '=', par(s, 'quebra_x0')),
             X('SetNumberObjectVariable', D, 'quebra_x1', '=', par(s, 'quebra_x1')),
             X('SetNumberObjectVariable', D, 'quebra_topo', '=', topo)]
        if qtd:
            a.append(X('SetNumberObjectVariable', D, 'quebra_qtd', '=', qtd))
        return a + [X('SetBooleanObjectVariable', D, 'quebra_tudo', tudo, ''),
                    X('SetBooleanObjectVariable', D, 'quebra_pedida', 'True', '')]
    for e, s, topo, tudo in ((cutelo, sc, 'Variable(quebra_topo_linhas)', 'False'),
                             (explo, se, 'Variable(quebra_topo_linhas)', 'False'),
                             (grande, sg, '0', 'True')):
        qtd = par(s, 'quebra_qtd') if tudo == 'False' else None
        i = e['events'].index(s)
        e['events'].pop(i)
        e['actions'] += pedido(s, topo, qtd, tudo)
        if not e['events']:
            del e['events']
    r0 = par(sc, 'quebra_r0').replace(' + Variable(quebra_topo_linhas)', ' + demonio_chefe.quebra_topo')
    larg = '(demonio_chefe.quebra_c1 - demonio_chefe.quebra_c0 + 1)'
    tira2 = copy.deepcopy(tira)
    assert tira2['conditions'][0]['parameters'] == ['demonio_chefe.quebra_feitas', '<', 'demonio_chefe.quebra_qtd']
    quebrar = grupo('Quebrar o piso', [
        ev([X('BooleanObjectVariable', D, 'quebra_pedida', 'True', '')],
           [X('SetBooleanObjectVariable', D, 'quebra_pedida', 'False', '')]
           + [X('SetNumberObjectVariable', D, v, '=', par(sc, v)) for v in ('quebra_c0', 'quebra_c1')]
           + [X('SetNumberObjectVariable', D, 'quebra_r0', '=', r0),
              X('SetNumberObjectVariable', D, 'quebra_r1', '=', par(sc, 'quebra_r1')),
              X('SetNumberObjectVariable', D, 'quebra_feitas', '=', '0'),
              X('SetNumberObjectVariable', D, 'quebra_i', '=', '0')], [
            ev([X('BooleanObjectVariable', D, 'quebra_tudo', 'True', '')],
               [X('SetNumberObjectVariable', D, 'quebra_qtd', '=',
                  f'{larg} * (demonio_chefe.quebra_r1 - demonio_chefe.quebra_r0 + 1)'),
                X('SetNumberObjectVariable', D, 'quebra_n', '=', 'demonio_chefe.quebra_qtd')]),
            ev([X('BooleanObjectVariable', D, 'quebra_tudo', 'False', '')],
               [X('SetNumberObjectVariable', D, 'quebra_n', '=',
                  'demonio_chefe.quebra_qtd * demonio_chefe.quebra_tentativas')]),
            ev(laco_rand['conditions'], [], [
                ev([X('BooleanObjectVariable', D, 'quebra_tudo', 'True', '')],
                   [X('SetNumberObjectVariable', D, 'quebra_c', '=',
                      f'demonio_chefe.quebra_c0 + mod(demonio_chefe.quebra_i, {larg})'),
                    X('SetNumberObjectVariable', D, 'quebra_r', '=',
                      f'demonio_chefe.quebra_r0 + floor(demonio_chefe.quebra_i / {larg})')]),
                ev([X('BooleanObjectVariable', D, 'quebra_tudo', 'False', '')], laco_rand['actions']),
                tira2,
                ev([], [X('SetNumberObjectVariable', D, 'quebra_i', '+', '1')]),
            ], tipo='Repeat', rep='demonio_chefe.quebra_n'),
        ])])
    f2['events'].insert(f2['events'].index(grande) + 1, quebrar)
    for n, t in (('quebra_topo', 'number'), ('quebra_tudo', 'boolean'), ('quebra_pedida', 'boolean'),
                 ('quebra_n', 'number'), ('quebra_i', 'number')):
        addvar(O[D], n, t, False if t == 'boolean' else 0)
    assert txt(quebrar).count('"Variable(destroco_por_tile)"') == 1

    # 8. Hubs
    HUBS = ['Hub', 'HubPurgatorio', 'HubParaiso']
    quedas = [next(e for e in L[h]['events'] if e.get('name') == 'Queda da borda') for h in HUBS]
    assert len({txt(q) for q in quedas}) == 1
    for h, q in zip(HUBS, quedas):
        evs = L[h]['events']
        saida = next(e for e in evs if e.get('name') == 'Saída')
        assert all(x.get('disabled') for x in saida['events']), h
        evs.remove(saida)
        evs[evs.index(q)] = {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0},
                             'target': 'Hubs'}
    d['externalEvents'].append({'associatedLayout': 'Hub', 'name': 'Hubs', 'events': [quedas[0]]})


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(g['name'] == 'Perseguidores' for g in d['objectsGroups']):
        sys.exit('t136 já foi aplicada; não roda de novo.')
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('repetições juntadas')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
