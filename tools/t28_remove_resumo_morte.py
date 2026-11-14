"""Migração única: tira o texto de resumo da morte do pato e o rastreio de progresso da fase.

Mantém a câmera lenta da morte (pato.morte_escala_tempo por pato.morte_espera s);
quando ela acaba, o tempo volta ao normal e o pato vai direto para o Hub.
Remove: resumo_fundo, resumo_txt (e a pasta resumo_morte), pato.resumo,
globais ultima_run e recorde, e os eventos que calculavam/mostravam essas coisas.
Os marcadores inicio/safezone continuam na cena.
Não rode de novo.
"""
import json
import re

PATH = 'jogo.json'


def carrega():
    s = open(PATH, encoding='utf-8').read()
    return json.loads(s, parse_float=lambda t: '\x00F' + t + '\x00')


def salva(d):
    o = json.dumps(d, indent=2, ensure_ascii=False)
    o = re.sub(r'"\\u0000F(.*?)\\u0000"', r'\1', o)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(o + '\n')


def acha_grupo(evs, nome):
    for e in evs:
        if e.get('type') == 'BuiltinCommonInstructions::Group' and e.get('name') == nome:
            return e
        r = acha_grupo(e.get('events', []), nome)
        if r:
            return r


def cita(x, *nomes):
    s = json.dumps(x, ensure_ascii=False)
    return any(n in s for n in nomes)


def main():
    d = carrega()
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    g = acha_grupo(jog['events'], 'Morte do Pato')
    assert g, 'grupo Morte do Pato não encontrado'
    evs = g['events']

    # 1) Evento da morte: some o que guarda a run (ultima_run / recorde / progresso).
    morte = next(e for e in evs if cita(e.get('actions', []), 'pato.morte_escala_tempo'))
    morte['actions'] = [a for a in morte['actions'] if not cita(a, 'ultima_run')]
    morte['events'] = [s for s in morte.get('events', []) if not cita(s, 'ultima_run', 'recorde')]

    # 2) Fim da câmera lenta: volta o tempo e vai para o Hub (sem tela de resumo).
    ir_hub = next(e for e in evs if cita(e.get('conditions', []), 'AnyKeyReleased'))
    acao_hub = next(a for a in ir_hub['actions'] if a['type']['value'] == 'Scene')
    fim = next(e for e in evs if cita(e.get('conditions', []), 'pato.morte_espera'))
    fim['conditions'] = [c for c in fim['conditions'] if not cita(c, 'resumo')]
    fim['actions'] = [a for a in fim['actions'] if a['type']['value'] == 'ChangeTimeScale'] + [acao_hub]
    fim['events'] = []

    # 3) Eventos que só existiam para a tela de resumo.
    g['events'] = [e for e in evs if e is fim or not cita(e, 'resumo')]
    assert not cita(g['events'], 'resumo', 'ultima_run', 'recorde')

    # 4) Objetos, pasta, variável do pato e globais que ficaram sem uso.
    tirar = {'resumo_fundo', 'resumo_txt'}
    d['objects'] = [o for o in d['objects'] if o['name'] not in tirar]
    def limpa_pasta(p):
        p['children'] = [c for c in p.get('children', [])
                         if c.get('folderName') != 'resumo_morte' and c.get('objectName') not in tirar]
        for c in p['children']:
            if 'children' in c:
                limpa_pasta(c)
    limpa_pasta(d['objectsFolderStructure'])
    for lay in d['layouts']:
        lay['instances'] = [i for i in lay['instances'] if i['name'] not in tirar]
    pato = next(o for o in d['objects'] if o['name'] == 'pato')
    pato['variables'] = [v for v in pato['variables'] if v['name'] != 'resumo']
    d['variables'] = [v for v in d['variables'] if v['name'] not in ('ultima_run', 'recorde')]

    s = json.dumps(d, ensure_ascii=False)
    for n in ('resumo_txt', 'resumo_fundo', 'ultima_run', 'recorde.'):
        assert n not in s, n
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
