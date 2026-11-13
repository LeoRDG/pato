"""Tarefa 40: ricochete das balas do jogador e upgrade "Ricochete" (1 nível = 1 ricochete).

- Bala do jogador (projetil.raio <= 0) que bate no Terreno com ricochetes sobrando quica como num espelho:
  testa a posição do quadro anterior em cada eixo para saber se bateu em parede (inverte X) ou chão/teto (inverte Y),
  volta para a posição anterior, perde pato.ricochete_perda do dano e gasta um ricochete. Sem ricochetes, some como antes.
  A granada (lanca, raio > 0) continua explodindo; balas de inimigo não quicam.
- projetil.ricochetes = GlobalVariable(upgrades.ricochete) ao nascer. Novo item no catálogo da loja: id "ricochete".
- Alcance: doze e minigun deixam de sumir no alcance (alcance = 99999, como a pistola). A queda de dano continua igual:
  nova variável queda_fim nas armas (= o alcance de antes) e a distância agora é o caminho percorrido (com os ricochetes).
Rodar uma vez:  python3 tools/t40_ricochete.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, var, estrutura, adiciona_var, acha_var, objeto, externo, C, A, E, comentario

DIST = 'DistanceBetweenPositions(projetil.CenterX(), projetil.CenterY(), projetil.ox, projetil.oy)'
FATOR_FIM_VELHO = 'max(1, projetil.alcance - projetil.queda_ini)'
FATOR_FIM_NOVO = 'max(1, projetil.queda_fim - projetil.queda_ini)'
ARMAS = ('pistola', 'doze', 'minigun', 'lanca')
SEM_ALCANCE = 99999


def P(nome, op, valor):
    return A('SetNumberObjectVariable', 'projetil', nome, op, valor)


def main():
    d = carrega()
    proj = next(e for e in externo(d, 'Combate')['events'] if e.get('name') == 'Projéteis')['events']
    if 'ricochetes' in json.dumps(proj):
        print('já migrado'); return

    # --- dados
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    if not any(c['value'] == 'ricochete' for i in cat['children'] for c in i['children'] if c['name'] == 'id'):
        cat['children'].append(estrutura(None, {'id': 'ricochete', 'nome': 'Ricochete',
                                                'descricao': '+1 ricochete por nível; a bala perde dano a cada ricochete',
                                                'tipo': 'upgrade', 'nivel_max': 3, 'preco_base': 50, 'preco_mult': 1.6,
                                                'requer': ''}))
    adiciona_var(next(v for v in d['variables'] if v['name'] == 'upgrades')['children'], var('ricochete', 0))
    adiciona_var(objeto(d, 'pato')['variables'], var('ricochete_perda', 0.2))
    for k in ('ricochetes', 'px', 'py', 'cx', 'cy', 'fx', 'fy', 'ric_x', 'ric_y', 'percorrido', 'queda_fim'):
        adiciona_var(objeto(d, 'projetil')['variables'], var(k, 0))
    for arma in ARMAS:
        av = objeto(d, arma)['variables']
        alc = acha_var(av, 'alcance')
        adiciona_var(av, var('queda_fim', alc['value']))   # a queda de dano termina onde o alcance terminava
        alc['value'] = max(alc['value'], SEM_ALCANCE)

    # --- nascimento da bala e queda pelo caminho percorrido
    balas = next(e for e in proj if e.get('name') == 'Balas (alcance, queda e perfuração)')
    nasce, voa = balas['events'][1], balas['events'][2]
    assert any(a['parameters'][:2] == ['projetil', 'furos'] for a in nasce['actions']), 'evento de nascimento mudou'
    nasce['actions'][-1:-1] = [P('queda_fim', '=', 'Arma.queda_fim'), P('ricochetes', '=', 'GlobalVariable(upgrades.ricochete)'),
                               P('px', '=', 'projetil.X()'), P('py', '=', 'projetil.Y()'), P('percorrido', '=', '0')]
    fator = voa['actions'][0]['parameters']
    corte = voa['events'][0]['conditions'][0]['parameters']
    if DIST not in fator[-1] or FATOR_FIM_VELHO not in fator[-1] or corte[0] != DIST:
        raise SystemExit('A queda de dano/alcance foi editada no GDevelop; nada alterado: ' + fator[-1])
    fator[-1] = fator[-1].replace(DIST, 'projetil.percorrido').replace(FATOR_FIM_VELHO, FATOR_FIM_NOVO)
    corte[0] = 'projetil.percorrido'
    voa['actions'].insert(0, P('percorrido', '+', 'DistanceBetweenPositions(projetil.X(), projetil.Y(), projetil.px, projetil.py)'))

    # --- ricochete (antes do evento que apaga a bala no terreno)
    apaga = next(e for e in proj if e['type'] == 'BuiltinCommonInstructions::Standard'
                 and any(c['parameters'][:2] == ['projetil', 'Terreno'] for c in e.get('conditions') or [])
                 and any(a['type']['value'] == 'Delete' for a in e['actions']))
    bate = lambda: C('CollisionNP', 'projetil', 'Terreno', '', '', '')
    ricochete = E(
        [C('NumberObjectVariable', 'projetil', 'raio', '<=', '0'), C('NumberObjectVariable', 'projetil', 'ricochetes', '>', '0'), bate()],
        [P('ric_x', '=', '0'), P('ric_y', '=', '0'), P('cx', '=', 'projetil.X()'), P('cy', '=', 'projetil.Y()'),
         A('SetXY', 'projetil', '=', 'projetil.px', '=', 'projetil.cy')],
        [
            comentario('Só o movimento em Y ainda bate: chão/teto (inverte Y). Só o movimento em X bate: parede (inverte X). '
                       'Nenhum dos dois ou os dois: quina (inverte os dois).'),
            E([bate()], [P('ric_y', '=', '1')]),
            E([], [A('SetXY', 'projetil', '=', 'projetil.cx', '=', 'projetil.py')]),
            E([bate()], [P('ric_x', '=', '1')]),
            E([C('NumberObjectVariable', 'projetil', 'ric_x', '=', '0'), C('NumberObjectVariable', 'projetil', 'ric_y', '=', '0')],
              [P('ric_x', '=', '1'), P('ric_y', '=', '1')]),
            E([], [
                A('SetXY', 'projetil', '=', 'projetil.px', '=', 'projetil.py'),
                P('fx', '=', 'projetil.ForceX() * (1 - 2 * projetil.ric_x)'),
                P('fy', '=', 'projetil.ForceY() * (1 - 2 * projetil.ric_y)'),
                A('Arreter', 'projetil'),
                A('AddForceXY', 'projetil', 'projetil.fx', 'projetil.fy', '1'),
                A('SetAngle', 'projetil', '=', 'ToDeg(atan2(projetil.fy, projetil.fx))'),
                P('dano', '*', '1 - pato.ricochete_perda'),
                P('ricochetes', '-', '1'),
            ]),
        ],
        tipo='BuiltinCommonInstructions::ForEach', object='projetil')
    i = proj.index(apaga)
    proj[i:i] = [comentario('Ricochete: bala do jogador com ricochetes sobrando quica no terreno como num espelho '
                            '(upgrades.ricochete, pato.ricochete_perda).'), ricochete]
    # posição do fim do quadro (o próximo quadro mede o caminho e testa o ricochete a partir dela)
    proj.insert(proj.index(apaga) + 1, E([], [P('px', '=', 'projetil.X()'), P('py', '=', 'projetil.Y()')]))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
