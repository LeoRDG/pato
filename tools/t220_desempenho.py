"""Tarefa 220: desempenho (celular), a partir das medições do jogo exportado.

1. Hubs: a tela de atributos regravava ~120 textos por quadro (ChangeColor e WrappingWidth redesenham o texto mesmo
   sem mudança, até nos escondidos). Agora o ForEach ui_txt só roda nos textos de cartões visíveis, e a cor e a
   largura só mudam quando o valor muda (ui_txt.cor_atual, ui_txt.larg_atual).
2. Paraíso: a "Lente negra" (BulgePinch) das camadas Fundo e Estrelas era um passe de tela cheia com força 0 quase
   o tempo todo; agora começa desligada e só liga enquanto o juízo a usa. No celular (desempenho.sem_filtros_celular)
   saem o brilho das estrelas (AdvancedBloom) e o "Menos vibrante" (Paraiso/Fundo e HubParaiso/fundo).
3. Celular renderiza em desempenho.resolucao_celular da resolução do jogo (o PIXI desenha num buffer menor; posições,
   câmera e toque não mudam). Inferno: com a noite toda à mostra (fundo_mistura >= desempenho.fundo_corte) o fundo
   de dia (coberto pelo céu noturno opaco) não é desenhado, e com o dia todo à mostra o de noite não é.
4. Inferno: bolhas de lava criadas fora da tela nunca terminavam a animação (o GDevelop não anima o que está fora
   da tela) e não eram apagadas: milhares em poucos minutos. Agora bolhas e brasas só nascem em lava perto da câmera
   (desempenho.lava_margem) e toda bolha some depois de desempenho.bolha_vida_max segundos.
5. O raio do laser (RaycastToPosition) só é calculado com o upgrade de laser.
6. O efeito "Brilho" (Brightness) dos inimigos ficava sempre ligado com brilho 1 (um passe por inimigo sem efeito
   visível): agora fica desligado e liga só durante o piscar. No celular saem também o Glow da moeda e o MotionBlur
   dos projéteis (desempenho.sem_filtros_celular).
7. FPS: no celular, máximo desempenho.fps_max_celular (30) e mínimo desempenho.fps_min_celular (20), para cair
   quadros em vez de o jogo ficar em câmera lenta; no computador continua 60 (propriedades do projeto).
Para testar o modo celular no computador: desempenho.forcar_celular.
Rodar uma vez:  python3 tools/t220_desempenho.py
"""
from gd_mig import *

D = 'desempenho'
VARS = [
    ('forcar_celular', False),
    ('resolucao_celular', 0.7),
    ('fps_max_celular', 30),
    ('fps_min_celular', 20),
    ('sem_filtros_celular', True),
    ('fundo_corte', 0.98),
    ('lava_margem', 400),
    ('bolha_vida_max', 2),
]
BRILHO = ['condenado_em_chamas', 'voador', 'pigman', 'cutulu', 'sapo', 'condenado_azul', 'condenado_inchado',
          'arvore_condenada', 'caveira_azul', 'moscas', 'olho_demoniaco', 'mina_demoniaca', 'cabeca_voadora',
          'diabinho', 'caveira_gigante', 'querubim', 'serafim', 'ofanim', 'roda_anjo', 'demonio_chefe', 'moscas2']
DIA = ['bg_inferno_ceu', 'bg_inferno_fundo', 'bg_inferno_meio', 'bg_inferno_frente']
NOITE = ['bg_inferno_noite_ceu', 'bg_inferno_noite_fundo', 'bg_inferno_noite_meio', 'bg_inferno_noite_frente']
EFEITO = 'EffectCapability::EffectBehavior::SetEffectDoubleParameter'
LIGA_EFEITO = 'EffectCapability::EffectBehavior::EnableEffect'


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': list(linhas), 'parameterObjects': '',
            'useStrict': True, 'eventsSheetExpanded': False}


CODIGO = [
    '// Desempenho (t220): números em desempenho.*. Roda todo quadro; o que é caro só acontece uma vez.',
    'const jogo = runtimeScene.getGame();',
    'const D = jogo.getVariables().get("desempenho");',
    'const num = k => D.getChild(k).getAsNumber(), bol = k => D.getChild(k).getAsBoolean();',
    'const cel = gdjs.evtTools.common.isMobile() || bol("forcar_celular");',
    'if (cel) {',
    '  // resolução do desenho: o PIXI desenha num buffer menor e estica na tela (posições, câmera e toque iguais)',
    '  const r = jogo.getRenderer().getPIXIRenderer();',
    '  const res = num("resolucao_celular");',
    '  if (r && res > 0 && r.resolution !== res) {',
    '    r.resolution = res;',
    '    r.resize(jogo.getGameResolutionWidth(), jogo.getGameResolutionHeight());',
    '  }',
    '  // fps: máximo e mínimo do celular (abaixo do mínimo o jogo fica em câmera lenta)',
    '  jogo.setMaximumFps(num("fps_max_celular"));',
    '  jogo._minFPS = num("fps_min_celular");',
    '}',
    'const semFiltros = cel && bol("sem_filtros_celular");',
    '// uma vez por cena: filtros de camada',
    'if (!runtimeScene._desempenhoCena) {',
    '  runtimeScene._desempenhoCena = true;',
    '  const desligaCamada = (camada, efeito) => {',
    '    if (runtimeScene.hasLayer(camada)) {',
    '      const l = runtimeScene.getLayer(camada);',
    '      if (l.hasEffect(efeito)) l.enableEffect(efeito, false);',
    '    }',
    '  };',
    '  // a lente negra só liga durante o juízo (InimigosParaiso)',
    '  desligaCamada("Fundo", "Lente negra");',
    '  desligaCamada("Estrelas", "Lente negra");',
    '  if (semFiltros) {',
    '    desligaCamada("Estrelas", "Brilho das estrelas");',
    '    desligaCamada("Fundo", "Menos vibrante");',
    '    desligaCamada("fundo", "Menos vibrante");',
    '  }',
    '}',
    '// uma vez por objeto criado: efeitos que começam ligados',
    'const desliga = (nomes, efeito, marca) => {',
    '  for (const nome of nomes) {',
    '    const lista = runtimeScene.getObjects(nome);',
    '    if (!lista) continue;',
    '    for (const o of lista) {',
    '      if (o[marca]) continue;',
    '      o[marca] = true;',
    '      if (o.hasEffect(efeito)) o.enableEffect(efeito, false);',
    '    }',
    '  }',
    '};',
    '// o "Brilho" dos inimigos só liga quando piscam (eventos dos inimigos)',
    'desliga(' + json.dumps(BRILHO) + ', "Brilho", "_brilhoIni");',
    'if (semFiltros) desliga(["moeda", "projetil", "projetil_inimigo"], "Effect", "_efeitoIni");',
]


def txt_de(x):
    return json.dumps(x, ensure_ascii=False)


def no(sheet_evs, caminho):
    e = None
    evs = sheet_evs
    for i in caminho:
        e = evs[i]
        evs = e.get('events', [])
    return e


def liga_brilho(d):
    """ao lado de cada SetEffectDoubleParameter "Brilho" brightness: liga se pisca, desliga se volta a 1."""
    n = 0
    for f in ('Inimigos', 'InimigosInferno', 'InimigosPurgatorio', 'InimigosParaiso'):
        for e in todos(folha(d, f)['events']):
            novas = []
            for a in e.get('actions', []):
                p = a.get('parameters', [])
                if a['type']['value'] == EFEITO and p[2] == '"Brilho"' and p[3] == '"brightness"':
                    novas.append(X(LIGA_EFEITO, p[0], 'Effect', '"Brilho"', 'no' if p[4] == '1' else 'yes'))
                    n += 1
                novas.append(a)
            e['actions'] = novas
    assert n == 14, n


def lente(d):
    """liga a lente negra junto com a força do juízo e desliga quando a força volta a 0."""
    n = 0
    for e in todos(folha(d, 'InimigosParaiso')['events']):
        novas = []
        for a in e.get('actions', []):
            novas.append(a)
            p = a.get('parameters', [])
            if a['type']['value'] == 'SetLayerEffectParameter' and p[2] == '"Lente negra"' and p[3] == '"strength"':
                novas.append(X('EnableLayerEffect', '', p[1], '"Lente negra"', 'no' if p[4] == '0' else 'yes'))
                n += 1
        e['actions'] = novas
    assert n == 10, n


def atributos(d):
    g = acha(folha(d, 'Hubs')['events'], 'Atributos')
    pega = [e for e in g['events'] if e.get('type') == 'BuiltinCommonInstructions::ForEach' and e.get('object') == 'ui_txt']
    assert len(pega) == 1, 'ForEach ui_txt'
    fe = pega[0]
    fe['conditions'].append(cmp('GlobalVariable(ui_card[ui_txt.card].vis)', '=', '1'))
    trocas = 0
    for sub in fe['events']:
        acoes = []
        for a in sub['actions']:
            if a['type']['value'] == 'TextObject::ChangeColor':
                acoes.append(X('SetStringObjectVariable', 'ui_txt', 'cor_nova', '=', a['parameters'][1]))
                sub.setdefault('events', []).append(ev(
                    [X('StringObjectVariable', 'ui_txt', 'cor_nova', '!=', 'ui_txt.cor_atual')],
                    [X('TextObject::ChangeColor', 'ui_txt', 'ui_txt.cor_nova'),
                     X('SetStringObjectVariable', 'ui_txt', 'cor_atual', '=', 'ui_txt.cor_nova')]))
                trocas += 1
            else:
                acoes.append(a)
        sub['actions'] = acoes
    assert trocas == 2, trocas
    larg = [e for e in g['events'] if any(a['type']['value'] == 'TextObject::WrappingWidth' for a in e.get('actions', []))]
    assert len(larg) == 1
    e = larg[0]
    acoes = []
    for a in e['actions']:
        if a['type']['value'] == 'TextObject::WrappingWidth':
            acoes.append(X('SetNumberObjectVariable', 'ui_txt', 'larg_nova', '=', a['parameters'][2]))
            e.setdefault('events', []).append(ev(
                [X('NumberObjectVariable', 'ui_txt', 'larg_nova', '!=', 'ui_txt.larg_atual')],
                [X('TextObject::WrappingWidth', 'ui_txt', '=', 'ui_txt.larg_nova'),
                 X('SetNumberObjectVariable', 'ui_txt', 'larg_atual', '=', 'ui_txt.larg_nova')]))
        else:
            acoes.append(a)
    e['actions'] = acoes
    poe_vars(Ids('t220'), objeto(d, 'ui_txt').setdefault('variables', []), 'obj/ui_txt',
             [('cor_nova', ''), ('cor_atual', ''), ('larg_nova', 0), ('larg_atual', -1)])


def lava(d):
    g = acha(folha(d, 'CenarioInferno')['events'], 'Lava')
    fe = next(e for e in g['events'] if e.get('type') == 'BuiltinCommonInstructions::ForEach' and e.get('object') == 'lava'
              and 'Create' in txt_de(e))
    m = f'{D}.lava_margem'
    fe['conditions'] += [
        cmp('lava.X() + lava.Width()', '>', f'CameraBorderLeft("", 0) - {m}'),
        cmp('lava.X()', '<', f'CameraBorderRight("", 0) + {m}'),
        cmp('lava.Y() + lava.Height()', '>', f'CameraBorderTop("", 0) - {m}'),
        cmp('lava.Y()', '<', f'CameraBorderBottom("", 0) + {m}'),
    ]
    cria = next(e for e in fe['events'] if '"lava_bolha"' in txt_de(e['actions']))
    cria['actions'].append(zera('lava_bolha', 'vida'))
    g['events'].append(ev([timer('lava_bolha', 'vida', '>', f'{D}.bolha_vida_max')], [X('Delete', 'lava_bolha', '')]))


def fundos(d):
    g = acha(folha(d, 'CenarioInferno')['events'], 'Fundo escuro')
    op = next(e for e in g['events'] if '"bg_inferno_noite_ceu", "Opacity", "=", "255 * fundo_mistura"' in txt_de(e['actions']))
    corte = f'{D}.fundo_corte'
    op.setdefault('events', []).extend([
        ev([cmp('fundo_mistura', '>=', corte)], [X('Hide', o) for o in DIA]),
        ev([cmp('fundo_mistura', '<', corte)], [X('Show', o, '') for o in DIA]),
        ev([cmp('fundo_mistura', '<=', f'1 - {corte}')], [X('Hide', o) for o in NOITE]),
        ev([cmp('fundo_mistura', '>', f'1 - {corte}')], [X('Show', o, '') for o in NOITE]),
    ])


def laser(d):
    ray = [e for e in todos(folha(d, 'Jogador')['events'])
           if any(c['type']['value'] == 'RaycastToPosition' and c['parameters'][3:5] == ['laser_x', 'laser_y']
                  for c in e.get('conditions', []))]
    assert len(ray) == 1
    ray[0]['conditions'].insert(0, cmp('GlobalVariable(upgrades.laser)', '>', '0'))


def migra(d):
    ids = Ids('t220')
    globais = {v['name']: v for v in d['variables']}
    if D not in globais:
        d['variables'].append({'name': D, 'persistentUuid': ids(f'var/global/{D}'), 'type': 'structure', 'children': []})
        globais[D] = d['variables'][-1]
    poe_vars(ids, globais[D]['children'], f'global/{D}', VARS)

    atributos(d)
    lente(d)
    lava(d)
    fundos(d)
    laser(d)
    liga_brilho(d)

    combate = folha(d, 'Combate')['events']
    combate.insert(0, grupo('Desempenho (celular)', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Desempenho (t220). No celular (ou com desempenho.forcar_celular): resolução do desenho '
                    '(resolucao_celular), fps máximo/mínimo (fps_max_celular, fps_min_celular) e, com sem_filtros_celular, '
                    'sem brilho das estrelas, "Menos vibrante", Glow da moeda e MotionBlur dos projéteis. Em todo lugar: '
                    'a lente negra do Paraíso começa desligada e o "Brilho" dos inimigos só liga quando piscam.'},
        js(CODIGO)]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == D for v in d['variables']), 't220')
