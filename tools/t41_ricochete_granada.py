"""Tarefa 41: a granada (lanca, projetil.raio > 0) também ricocheteia e explode a cada ricochete.

- Granada com ricochetes sobrando que bate no Terreno: marca projetil.quica e explode como sempre (efeitos, som, explosao_fogo),
  mas não some; depois o evento de ricochete (o mesmo das balas) a rebate como num espelho.
  Sem ricochetes, explode e some como antes. Bater num inimigo continua explodindo e sumindo.
- O ricochete também espelha a gravidade da granada (projetil.gy) e tira pato.ricochete_perda do dano da explosão.
- Total de explosões = ricochetes + 1.
Rodar uma vez:  python3 tools/t41_ricochete_granada.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, var, adiciona_var, objeto, externo, C, A, E, comentario


def P(nome, op, valor):
    return A('SetNumberObjectVariable', 'projetil', nome, op, valor)


def B(nome, valor):
    return A('SetBooleanObjectVariable', 'projetil', nome, valor, '')


def main():
    d = carrega()
    proj = next(e for e in externo(d, 'Combate')['events'] if e.get('name') == 'Projéteis')['events']
    if '"quica"' in json.dumps(proj):
        print('já migrado'); return
    adiciona_var(objeto(d, 'projetil')['variables'], var('quica', False))

    # --- explosão: granada com ricochetes que bate no terreno explode sem sumir
    exp = next(e for e in proj if e.get('name') == 'Explosão da granada')['events']
    boom = next(e for e in exp if any(c['parameters'][:3] == ['projetil', 'boom', 'True'] for c in e.get('conditions') or []))
    if boom['actions'][-1]['type']['value'] != 'Delete':
        raise SystemExit('O evento da explosão da granada foi editado no GDevelop; nada alterado')
    apaga = boom['actions'].pop()
    boom.setdefault('events', [])
    boom['events'] += [
        E([C('BooleanObjectVariable', 'projetil', 'quica', 'False', '')], [apaga]),
        E([C('BooleanObjectVariable', 'projetil', 'quica', 'True', '')], [B('boom', 'False'), B('quica', 'False')]),
    ]
    marca = E([C('NumberObjectVariable', 'projetil', 'raio', '>', '0'), C('NumberObjectVariable', 'projetil', 'ricochetes', '>', '0'),
               C('CollisionNP', 'projetil', 'Terreno', '', '', '')],
              [B('quica', 'True'), B('boom', 'True')], tipo='BuiltinCommonInstructions::ForEach', object='projetil')
    i = exp.index(boom)
    exp[i:i] = [comentario('Granada com ricochetes sobrando explode no terreno sem sumir (projetil.quica); '
                           'o evento de Ricochete, mais abaixo, a rebate.'), marca]

    # --- ricochete: vale também para a granada, espelha a gravidade e enfraquece a explosão
    ric = next(e for e in proj if any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or [])
               and e['type'] == 'BuiltinCommonInstructions::ForEach')
    ric['conditions'] = [c for c in ric['conditions'] if c['parameters'][:2] != ['projetil', 'raio']]
    final = ric['events'][-1]['actions']
    j = next(n for n, a in enumerate(final) if a['type']['value'] == 'AddForceXY')
    final.insert(j + 1, P('gy', '*', '1 - 2 * projetil.ric_y'))
    final.insert(next(n for n, a in enumerate(final) if a['parameters'][:2] == ['projetil', 'dano']) + 1,
                 P('dano_explosao', '*', '1 - pato.ricochete_perda'))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
