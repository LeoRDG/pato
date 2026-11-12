"""Tarefa 32: liga os sons de t31_sons_jogo.py nos eventos (e registra os arquivos como recursos de áudio).

  Pato:      pulo do chão (e de coiote e do buffer), pulo no ar (com o giro), dash, pouso de queda (mais alto quanto mais rápido caiu),
             dano (quack) e morte.
  Moedas:    pegar (tom variando um pouco) e caindo do inimigo morto.
  Inimigos:  acerto de bala (no lugar do hit.wav), morte, e o aviso de cada um no lugar do test.wav provisório; tiros do atirador,
             do sapo e do olho; cura do sapo; fogo da caveira gigante; explosão do inchado e da mina (o som da granada, mais grave).
  Armas:     troca de arma.
Cada ação de som que este script põe leva o arquivo som_*.wav de t31; rodar de novo tira as antigas e põe de novo.
Rodar:  python3 tools/t32_sons_eventos.py   (depois de t31_sons_jogo.py). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, C, E, PATH

PL = ('pato', 'PlatformerObject')
FB = 'FireBullet::FireBullet::HasJustFired'
# sons que este script ACRESCENTA (rodar de novo tira e põe de novo); avisos e acerto SUBSTITUEM um som existente e não entram aqui
ACRESCENTA = {'som_pulo.wav', 'som_pulo_ar.wav', 'som_dash.wav', 'som_pouso.wav', 'som_pato_dano.wav', 'som_pato_morte.wav',
              'som_moeda.wav', 'som_moedas_soltas.wav', 'som_inimigo_morte.wav', 'som_tiro_inimigo.wav', 'som_cuspe.wav',
              'som_tiro_olho.wav', 'som_cura.wav', 'som_fogo_caveira.wav', 'som_troca_arma.wav'}


def som(arq, vol, tom='1'):
    return A('PlaySound', '', arq, '', str(vol), tom)


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def grupo_de(evs, nome):
    return next(e for e in walk(evs) if e.get('name') == nome)


def tem_a(e, tipo, *ini):
    return any(a['type']['value'] == tipo and a['parameters'][:len(ini)] == list(ini) for a in e.get('actions') or [])


def tem_c(e, tipo, *ini, inv=None):
    return any(c['type']['value'] == tipo and c['parameters'][:len(ini)] == list(ini) and (inv is None or bool(c['type'].get('inverted')) == inv)
               for c in e.get('conditions') or [])


def limpa(evs):
    """Tira as ações de som que este script acrescenta e os eventos que ficaram vazios por isso (para poder rodar de novo)."""
    out = []
    for e in evs:
        antes = len(e.get('actions') or [])
        if antes:
            e['actions'] = [a for a in e['actions'] if not (a['type']['value'] == 'PlaySound' and a['parameters'][1] in ACRESCENTA)]
        if e.get('events'):
            e['events'] = limpa(e['events'])
        if antes and not e['actions'] and not e.get('events'):
            continue   # só tocava um som nosso
        out.append(e)
    return out


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    nossos = sorted(receitas_nomes())
    # recursos
    res = d['resources']['resources']
    for n in nossos:
        res[:] = [r for r in res if r['name'] != n] + [{'file': f'assets/{n}', 'kind': 'audio', 'metadata': '', 'name': n, 'preloadAsMusic': False,
                                                       'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True}]
    ext = {x['name']: x for x in d['externalEvents']}
    for x in ext.values():
        x['events'] = limpa(x['events'])
    jog, ini, comb = ext['Jogador']['events'], ext['Inimigos']['events'], ext['Combate']['events']

    # ------------------------------------------------------------------ pato
    mov = grupo_de(jog, 'Movimento')
    vivo = next(e for e in mov['events'] if tem_c(e, 'BooleanObjectVariable', 'pato', 'morto'))
    giro = next(e for e in vivo['events'] if tem_a(e, 'Tween::TweenBehavior::AddObjectAngleTween2', 'pato'))
    giro['actions'].append(som('som_pulo_ar.wav', 45, 'RandomFloatInRange(0.95, 1.05)'))
    i = vivo['events'].index(giro)
    aperta = [C('KeyFromTextJustPressed', '', '"Space"'), C('PlatformBehavior::CanJump', *PL)]
    vivo['events'][i:i] = [
        E(aperta + [C('PlatformBehavior::IsOnFloor', *PL)], [som('som_pulo.wav', 40, 'RandomFloatInRange(0.95, 1.05)')]),
        E(aperta + [C('PlatformBehavior::IsOnFloor', *PL, inv=True), C('AdvancedJump::AdvancedJump::CanCoyoteJump', 'pato', 'AdvancedJump', '')],
          [som('som_pulo.wav', 40, 'RandomFloatInRange(0.95, 1.05)')]),
    ]
    dash = next(e for e in vivo['events'] if tem_c(e, 'AdvancedJump::HorizontalDash::IsDashing', 'pato') and tem_a(e, 'Create', '', 'propulsor'))
    dash['actions'].append(som('som_dash.wav', 50, 'RandomFloatInRange(0.95, 1.05)'))

    sens = grupo_de(jog, 'Sensação do pato')
    buf = next(e for e in sens['events'] if tem_c(e, 'BooleanObjectVariable', 'pato', 'buf_ativo') and tem_a(e, 'PlatformBehavior::SimulateJumpKey'))
    buf['actions'].append(som('som_pulo.wav', 40, 'RandomFloatInRange(0.95, 1.05)'))
    pouso = next(e for e in sens['events'] if tem_c(e, 'NumberObjectVariable', 'pato', 'queda_vy'))
    pouso['actions'].insert(0, som('som_pouso.wav', '35 + 45 * clamp((pato.queda_vy - 250) / 450, 0, 1)', 'RandomFloatInRange(0.92, 1.05)'))

    morte = grupo_de(jog, 'Morte do Pato')
    m = next(e for e in morte['events'] if tem_a(e, 'SetBooleanObjectVariable', 'pato', 'morto', 'True'))
    m['actions'].append(som('som_pato_morte.wav', 90))

    # dano no pato: a vida caiu desde o último quadro (vida_controle é atualizada no Feedback, logo depois)
    comb[:] = [e for e in comb if e.get('name') != 'Sons de dano']
    comb.insert(next(k for k, e in enumerate(comb) if e.get('name') == 'Feedback'), {'type': 'BuiltinCommonInstructions::Group', 'name': 'Sons de dano', 'source': '', 'creationTime': 0,
                       'colorR': 74, 'colorG': 176, 'colorB': 228, 'parameters': [], 'events': [
        {'type': 'BuiltinCommonInstructions::Comment', 'comment': 'Quack quando o pato perde vida (antes do Feedback atualizar vida_controle). A morte tem som próprio.',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0}},
        E([C('NumberObjectVariable', 'pato', 'vida', '<', 'pato.vida_controle'), C('NumberObjectVariable', 'pato', 'vida', '>', '0')],
          [som('som_pato_dano.wav', 80, 'RandomFloatInRange(0.95, 1.08)')]),
    ]})

    # ------------------------------------------------------------------ moedas, acerto e morte dos inimigos
    col = grupo_de(comb, 'Coleta')
    pega = next(e for e in col['events'] if tem_a(e, 'Delete', 'moeda'))
    pega['actions'].insert(0, som('som_moeda.wav', 25, 'RandomFloatInRange(0.97, 1.12)'))
    for e in walk(comb):
        for a in e.get('actions') or []:
            if a['type']['value'] == 'PlaySound' and a['parameters'][1] == 'hit.wav':
                a['parameters'][1], a['parameters'][3], a['parameters'][4] = 'som_acerto.wav', '35', 'RandomFloatInRange(0.9, 1.1)'
    mi = grupo_de(comb, 'Morte do Inimigo')
    mm = next(e for e in mi['events'] if tem_a(e, 'SetBooleanObjectVariable', 'Inimigo', 'morto', 'True'))
    mm['actions'] += [som('som_inimigo_morte.wav', 55, 'RandomFloatInRange(0.9, 1.1)'), som('som_moedas_soltas.wav', 35)]

    # ------------------------------------------------------------------ inimigos: avisos no lugar do test.wav
    AVISO = {'Pigman': 'som_aviso_pigman.wav', 'Atirador': 'som_aviso_atirador.wav', 'Sapo': 'som_aviso_sapo.wav',
             'Cutulu': 'som_aviso_cutulu.wav', 'Mergulhadores': 'som_aviso_mergulhador.wav', 'Condenados': 'som_aviso_condenado.wav',
             'Condenado inchado': 'som_aviso_inchado.wav', 'Caveira gigante': 'som_aviso_caveira.wav',
             'Olho demoníaco': 'som_aviso_olho.wav', 'Mina demoníaca': 'som_aviso_mina.wav'}
    for nome, arq in AVISO.items():
        g = grupo_de(ini, nome)
        for e in walk(g['events']):
            for a in e.get('actions') or []:
                if a['type']['value'] == 'PlaySound' and a['parameters'][1] in ('test.wav',) + tuple(AVISO.values()):
                    a['parameters'][1:5] = [arq, '', '65', 'RandomFloatInRange(0.95, 1.05)']
    for nome, obj, arq in (('Atirador', 'atirador', 'som_tiro_inimigo.wav'), ('Sapo', 'sapo', 'som_cuspe.wav'),
                           ('Olho demoníaco', 'olho_demoniaco', 'som_tiro_olho.wav')):
        g = grupo_de(ini, nome)
        g['events'].append(E([C(FB, obj, 'FireBullet', '')], [som(arq, 55, 'RandomFloatInRange(0.93, 1.07)')]))
    sapo = grupo_de(ini, 'Sapo')
    cura = next(e for e in walk(sapo['events']) if tem_a(e, 'SetStringObjectVariable', 'sapo', 'estado', '=', '"curar"'))
    cura['actions'].append(som('som_cura.wav', 50))
    cav = grupo_de(ini, 'Caveira gigante')
    fogo = next(e for e in walk(cav['events']) if tem_a(e, 'SetStringObjectVariable', 'caveira_gigante', 'estado', '=', '"atacar"'))
    fogo['actions'].append(som('som_fogo_caveira.wav', 75))
    for nome, obj in (('Condenado inchado', 'condenado_inchado'), ('Mina demoníaca', 'mina_demoniaca')):
        g = grupo_de(ini, nome)
        boom = next(e for e in walk(g['events']) if tem_a(e, 'SetNumberObjectVariable', obj, 'vida', '=', '0'))
        boom['actions'] = [a for a in boom['actions'] if not (a['type']['value'] == 'PlaySound' and a['parameters'][1] == 'som_explosao.wav')]   # (rodar de novo)
        boom['actions'].append(som('som_explosao.wav', 70, 'RandomFloatInRange(0.75, 0.85)'))

    # ------------------------------------------------------------------ pré-carregar (como os sons das armas): sem isso o primeiro
    # toque de cada som espera o arquivo carregar e decodificar
    pre = next(e for e in walk(jog) if tem_a(e, 'PreloadSound', '', 'som_pistola.wav'))
    pre['actions'] = [a for a in pre['actions'] if not (a['type']['value'] == 'PreloadSound' and a['parameters'][1] in nossos)]
    pre['actions'] += [A('PreloadSound', '', n) for n in nossos]

    # ------------------------------------------------------------------ troca de arma
    troca = grupo_de(jog, 'Troca de Arma')
    for e in troca['events']:
        if tem_c(e, 'KeyFromTextJustPressed'):
            e['actions'].append(som('som_troca_arma.wav', 50, 'RandomFloatInRange(0.95, 1.05)'))

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


def receitas_nomes():
    import inspect, re, t31_sons_jogo
    return set(re.findall(r"R\['(som_[a-z_]+\.wav)'\]", inspect.getsource(t31_sons_jogo.receitas)))


if __name__ == '__main__':
    main()
