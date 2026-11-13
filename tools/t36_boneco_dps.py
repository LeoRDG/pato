"""Tarefa 36: leitura de DPS sobre o boneco de teste (só mexe no grupo 'Boneco de teste' criado na tarefa 35).

- Uma série de acertos começa no primeiro dano e termina quando o boneco volta à vida cheia (regen_espera sem dano).
- DPS = dano total da série / max(tempo do primeiro ao último acerto, boneco.dps_min_tempo).
- Texto boneco_dps acima do boneco: "DPS N   total N". O último resultado fica na tela até a próxima série.
Rodar uma vez:  python3 tools/t36_boneco_dps.py   (feche o projeto no GDevelop antes)
"""
from migra import carrega, salva, var, adiciona_var, objeto, cena, copia_objeto, C, A, E


def unico(lista, desc):
    if len(lista) != 1:
        raise SystemExit(f'{desc}: esperado 1, achei {len(lista)}; nada alterado')
    return lista[0]


def main():
    d = carrega()
    if objeto(d, 'boneco_dps'):
        print('já existe; nada feito'); return
    b = objeto(d, 'boneco')
    for k, val in dict(dps_total=0, dps_tempo=0, dps_ativo=False, dps_min_tempo=1, dps_altura=36).items():
        adiciona_var(b['variables'], var(k, val))
    t = copia_objeto(d, 'resumo_txt', 'boneco_dps', characterSize=24, string='DPS 0')
    t['content'] = dict(t['content'], characterSize=24, text='DPS 0')

    hub = cena(d, 'Hub')
    g = unico([e for e in hub['events'] if e.get('name') == 'Boneco de teste'], 'grupo Boneco de teste')['events']
    inicio = unico([e for e in g if any(c['type']['value'] == 'SceneJustBegins' for c in e.get('conditions') or [])], 'início')
    hit = unico([e for e in g if any(c['parameters'][:4] == ['boneco', 'vida', '<', 'boneco.vida_vista'] for c in e.get('conditions') or [])], 'acerto')
    regen = unico([e for e in g if any(c['type']['value'] == 'CompareObjectTimer' for c in e.get('conditions') or [])], 'regen')

    inicio['actions'] += [A('Create', '', 'boneco_dps', 'boneco.CenterX()', 'boneco.Y()', ''),
                          A('ChangePlan', 'boneco_dps', '=', '1100')]
    nova_serie = E([C('NumberObjectVariable', 'boneco', 'vida', '<', 'boneco.vida_vista'),
                    C('BooleanObjectVariable', 'boneco', 'dps_ativo', 'False', '')],
                   [A('ResetObjectTimer', 'boneco', '"dps"'),
                    A('SetNumberObjectVariable', 'boneco', 'dps_total', '=', '0'),
                    A('SetBooleanObjectVariable', 'boneco', 'dps_ativo', 'True', '')])
    g.insert(g.index(hit), nova_serie)
    i = next(n for n, a in enumerate(hit['actions']) if a['parameters'][:2] == ['boneco', 'vida_vista'])
    hit['actions'][i:i] = [A('SetNumberObjectVariable', 'boneco', 'dps_total', '+', 'boneco.vida_vista - boneco.vida'),
                           A('SetNumberObjectVariable', 'boneco', 'dps_tempo', '=', 'boneco.ObjectTimerElapsedTime("dps")')]
    regen['actions'].append(A('SetBooleanObjectVariable', 'boneco', 'dps_ativo', 'False', ''))
    g.append(E([], [
        A('TextContainerCapability::TextContainerBehavior::SetValue', 'boneco_dps', 'Text', '=',
          '"DPS " + ToString(round(boneco.dps_total / max(boneco.dps_tempo, boneco.dps_min_tempo)))'
          ' + "   total " + ToString(round(boneco.dps_total))'),
        A('SetXY', 'boneco_dps', '=', 'boneco.CenterX() - boneco_dps.Width() / 2', '=', 'boneco.Y() - boneco.dps_altura'),
    ]))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
