"""Tarefa 209: música.
- 10 faixas em assets/musica/*.ogg (geradas por tools/gera_musica.py) viram recursos de áudio musica_*.
- Cada cena diz a sua faixa na variável de cena musica (e a de chefe em musica_chefe, nas fases); musica_volume é a
  porcentagem dessa cena. Hubs: musica_hub_inferno/purgatorio/paraiso; fases: musica_inferno,
  musica_purgatorio, musica_paraiso com as versões _chefe; Resultado: musica_resultado. (Menu fica sem: ele vai
  direto para o hub no primeiro quadro; Teste e Vitoria também ficam sem.)
- Nova folha de eventos Musica, ligada no fim dessas cenas (nos hubs logo antes da Loja, que fica por último):
  1) musica_chefe_ativo = falso; 2) com as mesmas condições da barra de chefe do HUD (HUD > Barras de chefe > Chefes:
  Chefes.barra_ativa, distância até o pato menor que Chefes.barra_dist e Chefes não morto) musica_chefe_ativo =
  verdadeiro (copiadas de lá, então a música e a barra concordam); 3) um JavaScript que toca a música.
- A música usa um AudioContext próprio (Web Audio, loop sem emenda), fora do gerenciador de sons do GDevelop: as
  cenas têm "parar sons ao começar" e isso pararia a música a cada troca de cena. Assim, cenas com a mesma faixa
  (morrer e voltar para a fase, por exemplo) não reiniciam a música. Ela começa com a primeira tecla/clique (o
  navegador bloqueia som antes disso) e segue o volume global do GDevelop (Howler).
- A faixa de chefe toca junto, muda, no mesmo ponto da música; quando musica_chefe_ativo liga, troca em
  musica.fade_chefe s; quando fica musica.espera_chefe s desligada, volta em musica.fade_volta s.
- Números na variável global musica: volume (0-100), ligada, fade, fade_chefe, fade_volta, espera_chefe, volume_chefe.
Rodar uma vez:  python3 tools/t209_musica.py
"""
import copy
from gd_mig import *

FAIXAS = ['resultado', 'hub_inferno', 'hub_purgatorio', 'hub_paraiso', 'inferno', 'inferno_chefe',
          'purgatorio', 'purgatorio_chefe', 'paraiso', 'paraiso_chefe']

CENAS = {   # cena: (faixa, faixa de chefe)
    'Hub': ('musica_hub_inferno', ''),
    'HubPurgatorio': ('musica_hub_purgatorio', ''),
    'HubParaiso': ('musica_hub_paraiso', ''),
    'Inferno': ('musica_inferno', 'musica_inferno_chefe'),
    'Purgatorio': ('musica_purgatorio', 'musica_purgatorio_chefe'),
    'Paraiso': ('musica_paraiso', 'musica_paraiso_chefe'),
    'Resultado': ('musica_resultado', ''),
}

GLOBAL = [('volume', 70), ('ligada', True), ('fade', 2), ('fade_chefe', 1.5), ('fade_volta', 3), ('espera_chefe', 3),
          ('volume_chefe', 100)]

JS = [
    'try {',
    '  // Música (t209): a faixa da cena (variável de cena musica) em loop; com musica_chefe_ativo ligada troca para a',
    '  // de chefe (musica_chefe), no mesmo ponto da música. Números na variável global musica.*.',
    '  const jogo = runtimeScene.getGame();',
    '  const G = jogo.getVariables().get("musica");',
    '  const n = (k) => G.getChild(k).getAsNumber();',
    '  const SV = runtimeScene.getVariables();',
    '  const txt = (k) => (SV.has(k) ? SV.get(k).getAsString() : "");',
    '  const M = gdjs._musica || (gdjs._musica = { faixas: {}, base: null, chefe: null, ultimaLuta: -1e9, geral: -1 });',
    '  M.jogo = jogo;',
    '  M.cena = runtimeScene;',
    '  if (!M.ctx) {',
    '    // contexto próprio: o "parar sons ao começar" das cenas (Howler.stop) não corta a música',
    '    const C = window.AudioContext || window.webkitAudioContext;',
    '    if (!C) return;',
    '    M.ctx = new C();',
    '    M.mestre = M.ctx.createGain();',
    '    M.mestre.gain.value = 0;',
    '    M.mestre.connect(M.ctx.destination);',
    '    // o navegador só deixa tocar depois da primeira tecla/clique',
    '    const destrava = () => { if (M.ctx.state !== "running") M.ctx.resume().catch(() => {}); };',
    '    for (const e of ["keydown", "pointerdown", "mousedown", "touchend", "click"]) document.addEventListener(e, destrava, true);',
    '    M.carrega = (nome) => {',
    '      if (M.faixas[nome]) return M.faixas[nome];',
    '      const f = (M.faixas[nome] = { nome, buf: null, erro: false });',
    '      const rl = jogo.getResourceLoader();',
    '      const r = rl.getResource(nome);',
    '      if (!r) { f.erro = true; console.warn("musica: recurso não existe", nome); return f; }',
    '      fetch(rl.getFullUrl(r.file))',
    '        .then((x) => x.arrayBuffer())',
    '        .then((b) => M.ctx.decodeAudioData(b))',
    '        .then((buf) => { f.buf = buf; })',
    '        .catch((e) => { f.erro = true; console.warn("musica: não carregou", nome, e); });',
    '      return f;',
    '    };',
    '    // começa uma faixa em silêncio; com "junto" começa no mesmo ponto (proporcional) da outra',
    '    M.toca = (f, junto) => {',
    '      const g = M.ctx.createGain();',
    '      g.gain.value = 0;',
    '      g.connect(M.mestre);',
    '      const src = M.ctx.createBufferSource();',
    '      src.buffer = f.buf;',
    '      src.loop = true;',
    '      src.connect(g);',
    '      let pos = 0;',
    '      if (junto) {',
    '        const d = junto.f.buf.duration;',
    '        pos = ((((M.ctx.currentTime - junto.t0) % d) + d) % d) / d * f.buf.duration;',
    '      }',
    '      src.start(0, pos);',
    '      return { f, nome: f.nome, g, src, t0: M.ctx.currentTime - pos, alvo: -1 };',
    '    };',
    '    M.rampa = (v, alvo, tempo) => {',
    '      if (Math.abs(v.alvo - alvo) < 1e-4) return;',
    '      const t = M.ctx.currentTime;',
    '      v.g.gain.cancelScheduledValues(t);',
    '      v.g.gain.setValueAtTime(v.alvo < 0 ? 0 : v.g.gain.value, t);',
    '      v.g.gain.setTargetAtTime(alvo, t, Math.max(tempo, 0.01) / 4);',
    '      v.alvo = alvo;',
    '    };',
    '    M.solta = (v, tempo) => {',
    '      M.rampa(v, 0, tempo);',
    '      try { v.src.stop(M.ctx.currentTime + Math.max(tempo, 0.05) * 1.5); } catch (e) {}',
    '    };',
    '    M.estado = () => ({',
    '      contexto: M.ctx.state, geral: M.mestre.gain.value, luta: !!M.luta,',
    '      base: M.base && { nome: M.base.nome, volume: M.base.g.gain.value, alvo: M.base.alvo },',
    '      chefe: M.chefe && { nome: M.chefe.nome, volume: M.chefe.g.gain.value, alvo: M.chefe.alvo },',
    '    });',
    '  }',
    '  // volume geral: musica.volume, musica.ligada e o volume global do GDevelop (Howler)',
    '  const H = window.Howler;',
    '  const geral = (H ? (H._muted ? 0 : H._volume) : 1) * (G.getChild("ligada").getAsBoolean() ? 1 : 0) * n("volume") / 100;',
    '  if (Math.abs(M.geral - geral) > 1e-4) {',
    '    M.geral = geral;',
    '    M.mestre.gain.setTargetAtTime(geral, M.ctx.currentTime, 0.05);',
    '  }',
    '  const nomeBase = txt("musica");',
    '  const nomeChefe = txt("musica_chefe");',
    '  const volCena = SV.has("musica_volume") ? SV.get("musica_volume").getAsNumber() / 100 : 1;',
    '  const agora = performance.now() / 1000;',
    '  if (SV.has("musica_chefe_ativo") && SV.get("musica_chefe_ativo").getAsBoolean()) M.ultimaLuta = agora;',
    '  // troca de faixa só quando a cena nova pede outra (a mesma faixa continua tocando)',
    '  if (M.base && M.base.nome !== nomeBase) {',
    '    M.solta(M.base, n("fade"));',
    '    M.base = null;',
    '    if (M.chefe) { M.solta(M.chefe, n("fade")); M.chefe = null; }',
    '  }',
    '  if (M.chefe && M.chefe.nome !== nomeChefe) { M.solta(M.chefe, n("fade_volta")); M.chefe = null; }',
    '  if (nomeBase && !M.base) {',
    '    const f = M.carrega(nomeBase);',
    '    if (f.buf) M.base = M.toca(f);',
    '  }',
    '  // a de chefe já começa (muda) junto com a da fase, para a troca ser no mesmo ponto da música',
    '  if (nomeChefe && M.base && !M.chefe) {',
    '    const f = M.carrega(nomeChefe);',
    '    if (f.buf) M.chefe = M.toca(f, M.base);',
    '  }',
    '  M.luta = !!(M.chefe && agora - M.ultimaLuta < n("espera_chefe"));',
    '  const tempoLuta = M.luta ? n("fade_chefe") : n("fade_volta");',
    '  if (M.base) M.rampa(M.base, (M.luta ? 0 : 1) * volCena, M.base.alvo < 0 ? n("fade") : tempoLuta);',
    '  if (M.chefe) M.rampa(M.chefe, (M.luta ? 1 : 0) * volCena * n("volume_chefe") / 100, tempoLuta);',
    '  // só as faixas desta cena ficam decodificadas na memória',
    '  for (const k in M.faixas) if (k !== nomeBase && k !== nomeChefe) delete M.faixas[k];',
    '} catch (e) {',
    '  console.warn("musica:", e);',
    '}',
]


def recurso_audio(nome, arquivo):
    return {'file': arquivo, 'kind': 'audio', 'metadata': '', 'name': nome, 'preloadAsMusic': False,
            'preloadAsSound': False, 'preloadInCache': False, 'userAdded': True}


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def migra(d):
    ids = Ids('t209')
    tem = {r['name'] for r in d['resources']['resources']}
    for f in FAIXAS:
        nome = 'musica_' + f
        arq = f'assets/musica/{f}.ogg'
        assert os.path.exists(os.path.join(RAIZ, arq)), arq
        if nome not in tem:
            d['resources']['resources'].append(recurso_audio(nome, arq))

    if not any(v['name'] == 'musica' for v in d['variables']):
        d['variables'].append({'name': 'musica', 'persistentUuid': ids('var/global/musica'), 'type': 'structure',
                               'children': [var(ids, 'global/musica', k, v) for k, v in GLOBAL]})
    else:
        g = next(v for v in d['variables'] if v['name'] == 'musica')
        poe_vars(ids, g.setdefault('children', []), 'global/musica', GLOBAL)

    for nome, (faixa, chefe) in CENAS.items():
        c = cena(d, nome)
        pares = [('musica', faixa), ('musica_volume', 100), ('musica_chefe_ativo', False)]
        if chefe:
            pares.insert(1, ('musica_chefe', chefe))
        poe_vars(ids, c['variables'], nome, pares)
        if not any(e['type'] == 'BuiltinCommonInstructions::Link' and e.get('target') == 'Musica' for e in c['events']):
            link = {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'Musica'}
            fim = c['events'][-1] if c['events'] else None
            if fim and fim['type'] == 'BuiltinCommonInstructions::Link' and fim.get('target') == 'Loja':
                c['events'].insert(len(c['events']) - 1, link)    # a Loja continua por último nos hubs
            else:
                c['events'].append(link)

    # as mesmas condições da barra de chefe do HUD
    barra = acha(acha(folha(d, 'HUD')['events'], 'Barras de chefe')['events'], 'Chefes')['events'][0]
    conds = copy.deepcopy(barra['conditions'])
    assert [c['type']['value'] for c in conds] == ['BooleanObjectVariable', 'Distance', 'BooleanObjectVariable'], conds
    d['externalEvents'].append({'associatedLayout': 'Inferno', 'name': 'Musica', 'events': [grupo('Música', [
        ev([], [csetb('musica_chefe_ativo', False)]),
        ev(conds, [csetb('musica_chefe_ativo', True)]),
        js(JS),
    ])]})


if __name__ == '__main__':
    roda(migra, lambda d: any(x['name'] == 'Musica' for x in d['externalEvents']), 't209')
