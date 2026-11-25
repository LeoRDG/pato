"""Tarefa 199: base do placar (leaderboard) por fase: tempo de ponta a ponta e pontos.
Uma "corrida" (global corrida) começa ao entrar numa fase (Inferno, Purgatorio, Paraiso) e termina no portal final (ou na
saída do Empíreo). Ela guarda tempo, abates, pontos dos abates, dano recebido, mortes e idas ao hub.
- Portais para o hub: a corrida continua. O tempo segue contando no hub (placar.tempo_no_hub; comprar custa tempo) e cada ida
  conta em corrida.idas_hub (com placar.pts_ida_hub de desconto, 0 por padrão). Morrer também não encerra: o pato volta pelo
  ponto de volta, o tempo segue e cada morte desconta placar.pts_morte.
- Só vale para o placar (corrida.valida) a corrida que começou no início da fase. Entrar pelo ponto de volta sem corrida em
  andamento (recarregou a página, ou foi para outra fase no meio) começa uma corrida "parcial", que não vale.
- Entrar em outra fase abandona a corrida anterior.
Pontos = abates (placar.pts_abate + vida máxima do inimigo * placar.pts_vida_inimigo cada) + placar.pts_conclusao
       + segundos abaixo de placar_niveis[fase].tempo_ref * placar.pts_segundo
       - dano recebido * placar.pts_dano - mortes * placar.pts_morte - idas ao hub * placar.pts_ida_hub   (mínimo 0)
No fim o resultado vai para corrida_fim; se valer, os recordes locais (recordes[fase].tempo/pontos) são atualizados e salvos
no navegador (localStorage), e, se placar_url não estiver vazia, o resultado é enviado (POST JSON) para o placar global.
Rodar uma vez:  python3 tools/t199_placar.py
"""
from gd_mig import *

NIVEIS = {'Inferno': 900, 'Purgatorio': 900, 'Paraiso': 600}   # tempo_ref inicial (s) de cada fase
G = lambda v: f'GlobalVariable({v})'
NIVEL = 'GlobalVariableString(corrida.nivel)'

CARREGA = [
    '// Placar (t199): recordes locais salvos no navegador; carrega uma vez por jogo.',
    'const jogo = runtimeScene.getGame();',
    'if (!jogo.__recordesCarregados) {',
    '  jogo.__recordesCarregados = true;',
    '  try {',
    '    const salvo = JSON.parse(localStorage.getItem("pato_recordes") || "{}");',
    '    const R = jogo.getVariables().get("recordes");',
    '    for (const fase in salvo) for (const k in salvo[fase]) R.getChild(fase).getChild(k).setNumber(Number(salvo[fase][k]) || 0);',
    '  } catch (e) {}',
    '}',
]
ENVIA = [
    '// Placar (t199): salva os recordes locais e, se houver placar_url, envia a corrida para o placar global.',
    'const V = runtimeScene.getGame().getVariables();',
    'try { localStorage.setItem("pato_recordes", JSON.stringify(V.get("recordes").toJSObject())); } catch (e) {}',
    'const fim = V.get("corrida_fim").toJSObject();',
    'const url = V.get("placar_url").getAsString();',
    'if (url && fim.valida) {',
    '  // a build (níveis de upgrade) vai junto: no placar dá para ver se a pontuação veio de habilidade ou de upgrades',
    '  const corpo = Object.assign({ jogo: V.get("placar_jogo").getAsString(), nome: V.get("jogador_nome").getAsString(),',
    '    upgrades: V.get("upgrades").toJSObject() }, fim);',
    '  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) }).catch(() => {});',
    '}',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def estrutura(ids, dono, nome, pares):
    filhos = []
    for k, v in pares:
        if isinstance(v, list):
            filhos.append(estrutura(ids, f'{dono}/{nome}', k, v))
        else:
            filhos.append(var(ids, f'{dono}/{nome}', k, v))
    return {'name': nome, 'persistentUuid': ids(f'var/{dono}/{nome}'), 'type': 'structure', 'children': filhos}


def OU(*conds):
    return {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': list(conds)}


def e_fase():
    return OU(*[X('BuiltinCommonInstructions::CompareStrings', 'CurrentSceneName()', '=', f'"{n}"') for n in NIVEIS])


CAMPOS_NUM = ['tempo', 'abates', 'pts_abates', 'dano', 'mortes', 'idas_hub', 'pontos']


def migra(d):
    ids = Ids('t199')
    tem = {v['name'] for v in d['variables']}
    novas = [
        ('placar', [('pts_abate', 50), ('pts_vida_inimigo', 0.5), ('pts_conclusao', 1000), ('pts_segundo', 10),
                    ('pts_dano', 20), ('pts_morte', 500), ('pts_ida_hub', 0), ('tempo_no_hub', True)]),
        ('placar_niveis', [(n, [('tempo_ref', t)]) for n, t in NIVEIS.items()]),
        ('corrida', [('nivel', ''), ('ativa', False), ('valida', False), ('nova', False), ('concluir', False)]
         + [(c, 0) for c in CAMPOS_NUM]),
        ('corrida_fim', [('nivel', ''), ('valida', False), ('recorde_tempo', False), ('recorde_pontos', False)]
         + [(c, 0) for c in CAMPOS_NUM]),
        ('recordes', [(n, [('tempo', 0), ('pontos', 0)]) for n in NIVEIS]),
    ]
    for nome, pares in novas:
        if nome not in tem:
            d['variables'].append(estrutura(ids, 'global', nome, pares))
    poe_vars(ids, d['variables'], 'global', [('placar_url', ''), ('placar_jogo', 'pato'), ('jogador_nome', '')])

    fim_copia = [X('SetStringVariable', 'corrida_fim.nivel', '=', NIVEL)] + \
        [csetn(f'corrida_fim.{c}', '=', G(f'corrida.{c}')) for c in CAMPOS_NUM] + \
        [csetb('corrida_fim.valida', False), csetb('corrida_fim.recorde_tempo', False), csetb('corrida_fim.recorde_pontos', False)]
    rec = f'recordes[{NIVEL}]'
    termina = ev([cbol('corrida.concluir', True)], [
        csetb('corrida.concluir', False), csetb('corrida.ativa', False),
        csetn('corrida.pontos', '=', 'max(0, round(' + ' + '.join([
            G('corrida.pts_abates'), G('placar.pts_conclusao'),
            f'max(0, GlobalVariable(placar_niveis[{NIVEL}].tempo_ref) - {G("corrida.tempo")}) * {G("placar.pts_segundo")}']) + ' - ' + ' - '.join([
            f'{G("corrida.dano")} * {G("placar.pts_dano")}', f'{G("corrida.mortes")} * {G("placar.pts_morte")}',
            f'{G("corrida.idas_hub")} * {G("placar.pts_ida_hub")}']) + '))')] + fim_copia, [
        ev([cbol('corrida.valida', True)], [csetb('corrida_fim.valida', True)], [
            ev([OU(cnum(f'{rec}.tempo', '<=', '0'), cnum(f'{rec}.tempo', '>', G('corrida.tempo')))], [
                csetn(f'{rec}.tempo', '=', G('corrida.tempo')), csetb('corrida_fim.recorde_tempo', True)]),
            ev([cnum(f'{rec}.pontos', '<', G('corrida.pontos'))], [
                csetn(f'{rec}.pontos', '=', G('corrida.pontos')), csetb('corrida_fim.recorde_pontos', True)])]),
        js(ENVIA)])
    comeca = ev([X('DepartScene', ''), e_fase()], [csetb('corrida.nova', True)], [
        ev([cbol('corrida.ativa', True), X('StringVariable', 'corrida.nivel', '=', 'CurrentSceneName()')], [csetb('corrida.nova', False)]),
        ev([cbol('corrida.nova', True)], [
            X('SetStringVariable', 'corrida.nivel', '=', 'CurrentSceneName()'), csetb('corrida.ativa', True),
            csetb('corrida.valida', True), csetb('corrida.concluir', False)] + [csetn(f'corrida.{c}', '=', '0') for c in CAMPOS_NUM], [
            ev([cbol('waypoints[CurrentSceneName()].ativo', True)], [csetb('corrida.valida', False)])]),
    ])
    relogio = ev([cbol('corrida.ativa', True)], [], [
        # conta sempre (fase e hub); com placar.tempo_no_hub desligado, só na fase
        ev([cbol('placar.tempo_no_hub', True)], [csetn('corrida.tempo', '+', 'TimeDelta()')]),
        ev([cbol('placar.tempo_no_hub', False), e_fase()], [csetn('corrida.tempo', '+', 'TimeDelta()')]),
    ])
    jog = folha(d, 'Jogador')['events']
    jog.append(grupo('Corrida (placar)', [js(CARREGA), termina, comeca, relogio]))

    # mortes contam, mas a corrida continua
    morte = next(e for e in acha(jog, 'Morte do Pato')['events']
                 if any(a['type']['value'] == 'SetBooleanObjectVariable' and a['parameters'][:3] == ['pato', 'morto', 'True']
                        for a in e.get('actions', [])))
    morte['actions'].append(csetn('corrida.mortes', '+', '1'))
    # dano recebido: no evento que já escala o dano (t196), antes de a vida ser corrigida
    n = 0
    for x in d['externalEvents']:
        for e in todos(x['events']):
            acs = e.get('actions', [])
            if acs and acs[0]['type']['value'] == 'SetNumberObjectVariable' and acs[0]['parameters'][:2] == ['pato', 'vida'] \
                    and acs[0]['parameters'][3].startswith('pato.vida_ref - max(1'):
                acs.insert(0, csetn('corrida.dano', '+', 'max(1, round((pato.vida_ref - pato.vida) * dificuldade_dano))'))
                n += 1
    assert n == 2, n
    # abates
    com = folha(d, 'Combate')['events']
    mi = acha(com, 'Morte do Inimigo')['events'][0]
    mi['events'].append(cada('Inimigo', [cbol('corrida.ativa', True)], [
        csetn('corrida.abates', '+', '1'),
        csetn('corrida.pts_abates', '+', f'{G("placar.pts_abate")} + Inimigo.max_vida * {G("placar.pts_vida_inimigo")}')]))
    # fim da fase: portal final e saída do Empíreo
    concluir = ev([cbol('corrida.ativa', True), X('StringVariable', 'corrida.nivel', '=', 'CurrentSceneName()')],
                  [csetb('corrida.concluir', True)])
    entra = acha(folha(d, 'Portais')['events'], 'Entrar no portal')['events'][1]
    final = next(e for e in entra['events'] if any(c['parameters'][:3] == ['portal', 'final', 'True'] for c in e['conditions']))
    final.setdefault('events', []).append(concluir)
    # ida ao hub pelo portal do meio da fase (o que grava o ponto de volta); voltar ao hub por morte não conta
    volta = next(e for e in entra['events'] if any(c['parameters'][:3] == ['portal', 'final', 'False'] for c in e['conditions']))
    volta.setdefault('events', []).append(ev([cbol('corrida.ativa', True)], [csetn('corrida.idas_hub', '+', '1')]))
    saida = acha(cena(d, 'Paraiso')['events'], 'Saída no Empíreo')['events'][1]
    assert any(a['type']['value'] == 'Scene' for a in saida['actions'])
    saida.setdefault('events', []).append(ev(concluir['conditions'], concluir['actions']))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'corrida' for v in d['variables']), 't199')
