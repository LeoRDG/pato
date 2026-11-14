"""Tarefa 45: upgrade "Eletricidade": raios ligam as balas do jogador que estão no ar e dão dano em quem encostar.

- Cada bala (projetil) se liga à bala mais próxima disparada antes dela (projetil.serie menor), se estiver a até
  pato.eletro_alcance px. O raio é desenhado em zigue-zague no objeto eletro_raio (pintor, cópia do laser, azul):
  pato.eletro_segmentos pedaços, tremor de pato.eletro_tremor px, espessura pato.eletro_espessura.
- A cada pato.eletro_intervalo s, cada raio tira max(1, round(pato.eletro_dano * nível * mult_dano)) de todo inimigo vivo
  cuja caixa esteja a menos de pato.eletro_largura px do raio (sem repulsão).
- Novo item no catálogo: id "eletricidade" (upgrades.eletricidade); nível 0 = sem raios.
Rodar uma vez:  python3 tools/t45_eletricidade.py
"""
import copy
from migra import carrega, salva, var, estrutura, adiciona_var, objeto, externo, copia_objeto, C, A, E, comentario, grupo

N = 'pato.eletro_segmentos'
DANO = 'max(1, round(pato.eletro_dano * GlobalVariable(upgrades.eletricidade) * GlobalVariable(mult_dano)))'
T = 'clamp(((Inimigo.CenterX() - eletro_ax) * (eletro_bx - eletro_ax) + (Inimigo.CenterY() - eletro_ay) * (eletro_by - eletro_ay)) / max(1, eletro_len2), 0, 1)'
D = ('sqrt(pow(max(0, abs(eletro_ax + eletro_t * (eletro_bx - eletro_ax) - Inimigo.CenterX()) - Inimigo.Width() / 2), 2)'
     ' + pow(max(0, abs(eletro_ay + eletro_t * (eletro_by - eletro_ay) - Inimigo.CenterY()) - Inimigo.Height() / 2), 2))')


def S(nome, op, valor):
    return A('SetNumberVariable', nome, op, valor)


def cmp(a, op, b):
    return C('BuiltinCommonInstructions::CompareNumbers', a, op, b)


def main():
    d = carrega()
    comb = externo(d, 'Combate')['events']
    if any(e.get('name') == 'Eletricidade' for e in comb):
        print('já migrado'); return

    # --- dados
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    if not any(c['value'] == 'eletricidade' for i in cat['children'] for c in i['children'] if c['name'] == 'id'):
        cat['children'].append(estrutura(None, {'id': 'eletricidade', 'nome': 'Eletricidade',
                                                'descricao': 'Raios ligam as balas no ar e dão dano em quem encostar; +dano por nível',
                                                'tipo': 'upgrade', 'nivel_max': 3, 'preco_base': 50, 'preco_mult': 1.6,
                                                'requer': ''}))
    adiciona_var(next(v for v in d['variables'] if v['name'] == 'upgrades')['children'], var('eletricidade', 0))
    for k, v in dict(eletro_alcance=260, eletro_dano=6, eletro_intervalo=0.2, eletro_largura=16,
                     eletro_espessura=3, eletro_tremor=10, eletro_segmentos=5).items():
        adiciona_var(objeto(d, 'pato')['variables'], var(k, v))
    for k in ('eletro_relogio', 'eletro_tick', 'eletro_ax', 'eletro_ay', 'eletro_bx', 'eletro_by', 'eletro_serie',
              'eletro_len', 'eletro_len2', 'eletro_i', 'eletro_off', 'eletro_x0', 'eletro_y0', 'eletro_x1', 'eletro_y1',
              'eletro_t', 'eletro_d'):
        adiciona_var(d['variables'], var(k, 0))
    if not objeto(d, 'eletro_raio'):
        o = copia_objeto(d, 'laser', 'eletro_raio')
        o['outlineColor'] = {'r': 140, 'g': 215, 'b': 255}
        o['outlineOpacity'] = 230
        o['effects'] = copy.deepcopy(o['effects'])
        for ef in o['effects']:
            if 'color' in ef.get('stringParameters', {}):
                ef['stringParameters']['color'] = '90;180;255'

    # --- eventos
    zigue = E([], [S('eletro_off', '=', 'RandomFloatInRange(-pato.eletro_tremor, pato.eletro_tremor)')], [
        E([cmp('eletro_i + 1', '>=', N)], [S('eletro_off', '=', '0')]),
        E([], [
            S('eletro_x1', '=', f'eletro_ax + (eletro_bx - eletro_ax) * (eletro_i + 1) / {N} - (eletro_by - eletro_ay) / max(1, eletro_len) * eletro_off'),
            S('eletro_y1', '=', f'eletro_ay + (eletro_by - eletro_ay) * (eletro_i + 1) / {N} + (eletro_bx - eletro_ax) / max(1, eletro_len) * eletro_off'),
            A('PrimitiveDrawing::LineV2', 'eletro_raio', 'eletro_x0', 'eletro_y0', 'eletro_x1', 'eletro_y1', 'pato.eletro_espessura'),
            S('eletro_x0', '=', 'eletro_x1'), S('eletro_y0', '=', 'eletro_y1'), S('eletro_i', '+', '1'),
        ]),
    ], tipo='BuiltinCommonInstructions::Repeat', repeatExpression=N)
    dano = E([cmp('eletro_tick', '=', '1')], [], [
        E([C('BooleanObjectVariable', 'Inimigo', 'morto', 'False', '')], [S('eletro_t', '=', T), S('eletro_d', '=', D)], [
            E([cmp('eletro_d', '<', 'pato.eletro_largura')], [A('SetNumberObjectVariable', 'Inimigo', 'vida', '-', DANO)]),
        ], tipo='BuiltinCommonInstructions::ForEach', object='Inimigo'),
    ])
    liga = E([C('AjoutObjConcern', '', 'projetil'),
              C('BooleanObjectVariable', 'projetil', 'iniciado', 'True', ''),
              C('NumberObjectVariable', 'projetil', 'serie', '<', 'eletro_serie'),
              C('PickNearest', 'projetil', 'eletro_ax', 'eletro_ay', '')],
             [S('eletro_bx', '=', 'projetil.CenterX()'), S('eletro_by', '=', 'projetil.CenterY()'),
              S('eletro_len2', '=', 'pow(eletro_bx - eletro_ax, 2) + pow(eletro_by - eletro_ay, 2)'),
              S('eletro_len', '=', 'sqrt(eletro_len2)')], [
        E([cmp('eletro_len', '<=', 'pato.eletro_alcance')],
          [S('eletro_x0', '=', 'eletro_ax'), S('eletro_y0', '=', 'eletro_ay'), S('eletro_i', '=', '0')], [zigue, dano]),
    ])
    eventos = [
        comentario('Eletricidade (upgrades.eletricidade): cada bala do jogador se liga por um raio à bala mais próxima disparada antes dela, '
                   'até pato.eletro_alcance px. A cada pato.eletro_intervalo s o raio dá dano em todo inimigo a menos de pato.eletro_largura px dele.'),
        E([C('SceneInstancesCount', '', 'eletro_raio', '=', '0')],
          [A('Create', '', 'eletro_raio', '0', '0', ''), A('ChangePlan', 'eletro_raio', '=', '900')]),
        E([cmp('GlobalVariable(upgrades.eletricidade)', '>', '0'), C('SceneInstancesCount', '', 'pato', '>', '0')], [], [
            E([], [S('eletro_tick', '=', '0'), S('eletro_relogio', '+', 'TimeDelta()')], [
                E([cmp('eletro_relogio', '>=', 'pato.eletro_intervalo')], [S('eletro_tick', '=', '1'), S('eletro_relogio', '=', '0')]),
            ]),
            E([C('BooleanObjectVariable', 'projetil', 'iniciado', 'True', '')],
              [S('eletro_ax', '=', 'projetil.CenterX()'), S('eletro_ay', '=', 'projetil.CenterY()'),
               S('eletro_serie', '=', 'projetil.serie')], [liga],
              tipo='BuiltinCommonInstructions::ForEach', object='projetil'),
        ]),
    ]
    comb.append(grupo('Eletricidade', eventos))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
