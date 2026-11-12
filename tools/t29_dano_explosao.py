"""Tarefa 29: dano da explosão confiável, preso ao emissor, com queda pela distância.

Antes: o evento da explosão comparava a distância com CompareNumbers usando Inimigo.CenterX(): sem nada escolhendo os inimigos,
o GDevelop usa só a primeira instância, então quase sempre um só inimigo (qualquer um) era testado. E a distância ia até o
CENTRO do inimigo: inimigos grandes (boss, caveira gigante) com a borda dentro do raio ficavam de fora.

Agora:
  - a granada (projetil) dá dano 1 em quem ela acerta direto (lanca.dano = 1);
  - o dano da explosão (lanca.dano_explosao) vai para o emissor explosao_fogo, junto com raio e repulsão;
  - o grupo "Dano da explosão" passa por cada emissor novo e cada inimigo vivo (ForEach), mede a distância do centro da
    explosão até a borda da caixa do inimigo e tira dano_explosao * (1 - distância / raio): 100% no centro, 0 na borda
    (mínimo 1 dentro do raio). Cada emissor aplica o dano uma vez só (aplicado).
Rodar:  python3 tools/t29_dano_explosao.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, C, E, PATH, comentario, grupo, upsert

DANO_EXPLOSAO = 90
EXPLOSAO = ('explosao_fumaca', 'explosao_fogo', 'explosao_faiscas')
EF = 'explosao_fogo'
# distância do centro da explosão até o ponto mais perto da caixa do inimigo (0 se a explosão está dentro dele)
DIST = (f'sqrt(pow(max(0, abs({EF}.X() - Inimigo.CenterX()) - Inimigo.Width() / 2), 2) + '
        f'pow(max(0, abs({EF}.Y() - Inimigo.CenterY()) - Inimigo.Height() / 2), 2))')
QUEDA = f'(1 - exp_d / {EF}.raio)'
FE = 'BuiltinCommonInstructions::ForEach'
vivo = lambda: C('BooleanObjectVariable', 'Inimigo', 'morto', 'False', '')


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def grupo_explosao():
    boom = lambda cond, extra=(): E(cond, [A('SetBooleanObjectVariable', 'projetil', 'boom', 'True', ''), *extra], tipo=FE, object='projetil')
    return grupo('Explosão da granada', [
        comentario('Granada (projetil.raio > 0) explode ao tocar no chão ou num inimigo; quem ela acerta direto leva o dano da granada (1). '
                   'A explosão cria as partículas e o som, e o emissor explosao_fogo leva o dano, o raio e a repulsão (ver Dano da explosão). '
                   'Depois a granada some.'),
        boom([C('NumberObjectVariable', 'projetil', 'raio', '>', '0'), C('CollisionNP', 'projetil', 'Terreno', '', '', '')]),
        boom([C('NumberObjectVariable', 'projetil', 'raio', '>', '0'), C('CollisionNP', 'projetil', 'Inimigo', '', '', ''), vivo()],
             [A('SetNumberObjectVariable', 'Inimigo', 'vida', '-', 'max(1, round(projetil.dano * GlobalVariable(mult_dano)))'),
              A('SetBooleanObjectVariable', 'Inimigo', 'acertado', 'True', '')]),
        E([C('BooleanObjectVariable', 'projetil', 'boom', 'True', '')],
          [A('Create', '', n, 'projetil.CenterX()', 'projetil.CenterY()', '') for n in EXPLOSAO] + [
              A('SetNumberObjectVariable', EF, 'dano', '=', 'projetil.dano_explosao'),
              A('SetNumberObjectVariable', EF, 'raio', '=', 'projetil.raio'),
              A('SetNumberObjectVariable', EF, 'repulsao', '=', 'projetil.repulsao'),
              A('PlaySoundOnChannel', '', 'som_explosao.wav', '3', '90', '90', '1'),
              A('SetSoundChannelPitch', '', '3', '=', 'RandomFloatInRange(.95, 1.05)'),
              A('Delete', 'projetil', ''),
          ], tipo=FE, object='projetil'),
    ])


def grupo_dano():
    return grupo('Dano da explosão', [
        comentario('Cada explosão nova (emissor explosao_fogo) dá dano uma vez em todo inimigo vivo cuja caixa esteja a menos de raio px do centro: '
                   'dano * (1 - distância / raio), 100% no centro e 0 na borda (mínimo 1). A repulsão cai do mesmo jeito.'),
        E([C('BooleanObjectVariable', EF, 'aplicado', 'False', '')], [], [
            E([vivo()], [A('SetNumberVariable', 'exp_d', '=', DIST)], [
                E([C('NumberVariable', 'exp_d', '<', f'{EF}.raio')], [
                    A('SetNumberObjectVariable', 'Inimigo', 'vida', '-',
                      f'max(1, round({EF}.dano * {QUEDA} * RandomFloatInRange(0.9, 1.1) * GlobalVariable(mult_dano)))'),
                    A('SetBooleanObjectVariable', 'Inimigo', 'acertado', 'True', ''),
                    A('SetNumberObjectVariable', 'Inimigo', 'kb_dir', '=', f'sign(Inimigo.CenterX() - {EF}.X() + 0.001) * {EF}.repulsao * {QUEDA}'),
                ]),
            ], tipo=FE, object='Inimigo'),
            E([], [A('SetBooleanObjectVariable', EF, 'aplicado', 'True', '')]),
        ], tipo=FE, object=EF),
    ])


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    obj = {o['name']: o for o in d['objects']}
    for n in ('pistola', 'doze', 'minigun', 'lanca'):
        upsert(obj[n]['variables'], 'dano_explosao', DANO_EXPLOSAO if n == 'lanca' else 0)
    upsert(obj['lanca']['variables'], 'dano', 1)
    upsert(obj['projetil']['variables'], 'dano_explosao', 0)
    for k in ('dano', 'raio', 'repulsao'):
        upsert(obj[EF]['variables'], k, 0)
    upsert(obj[EF]['variables'], 'aplicado', False)
    for lay in d['layouts']:
        if lay['name'] in ('Hub', 'Inferno'):
            upsert(lay['variables'], 'exp_d', 0)

    comb = next(x for x in d['externalEvents'] if x['name'] == 'Combate')
    proj = next(e for e in walk(comb['events']) if e.get('name') == 'Projéteis')
    nasc = next(e for e in walk(proj['events']) if any(a['parameters'][:2] == ['projetil', 'raio'] for a in e.get('actions', [])))
    nasc['actions'] = [a for a in nasc['actions'] if a['parameters'][:2] != ['projetil', 'dano_explosao']]
    i = next(k for k, a in enumerate(nasc['actions']) if a['parameters'][:2] == ['projetil', 'raio'])
    nasc['actions'].insert(i + 1, A('SetNumberObjectVariable', 'projetil', 'dano_explosao', '=', 'Arma.dano_explosao'))

    evs = proj['events']
    evs[:] = [e for e in evs if e.get('name') != 'Dano da explosão']
    i = next(k for k, e in enumerate(evs) if e.get('name') == 'Explosão da granada')
    evs[i] = grupo_explosao()
    evs.insert(i + 1, grupo_dano())

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
