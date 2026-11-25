"""Tarefa 196: o jogo fica menos punitivo (jogadores morriam demais).
- dificuldade_dano (global, 0,7): todo dano que o pato leva é multiplicado por ela (arredondado, no mínimo 1). Em vez de mexer
  no dano de cada inimigo, um evento compara a vida com pato.vida_ref (a última vida já contada): o que caiu abaixo dela é
  escalado e vida_ref acompanha; se a vida subiu (upgrade, começo da cena), vida_ref sobe junto. O evento roda no começo da
  Morte do Pato (Jogador, antes da conferência de morte) e no começo dos Sons de dano (Combate, antes do número de dano),
  então pega dano de qualquer folha. As mortes de propósito (feixe do Juízo, tecla X) põem vida_ref = vida e não são escaladas.
- Depois de levar dano o pato fica invencível 1 s (pato.iframes_tempo, era 0,75 s; só muda se ainda estiver em 0,75).
- Encostar num inimigo empurra o pato para longe dele (pato.dano_empurrao_x, pelo coice_vx que já existe), em vez de deixá-lo
  dentro do inimigo levando um golpe atrás do outro.
Rodar uma vez:  python3 tools/t196_dificuldade.py
"""
from gd_mig import *


def escala():
    return ev([], [], [
        ev([X('BuiltinCommonInstructions::CompareNumbers', 'pato.vida', '<', 'pato.vida_ref'), num('pato', 'vida_ref', '>', '0')], [
            setn('pato', 'vida', '=', 'pato.vida_ref - max(1, round((pato.vida_ref - pato.vida) * dificuldade_dano))'),
            setn('pato', 'vida_ref', '=', 'pato.vida')]),
        ev([X('BuiltinCommonInstructions::CompareNumbers', 'pato.vida', '>', 'pato.vida_ref')], [setn('pato', 'vida_ref', '=', 'pato.vida')]),
    ])


def migra(d):
    ids = Ids('t196')
    pato = objeto(d, 'pato')
    poe_vars(ids, pato['variables'], 'pato', [('vida_ref', 0), ('dano_empurrao_x', 900)])
    poe_vars(ids, d['variables'], 'global', [('dificuldade_dano', 0.7)])
    it = next(v for v in pato['variables'] if v['name'] == 'iframes_tempo')
    if it['value'] == 0.75:
        it['value'] = 1

    jog = folha(d, 'Jogador')['events']
    acha(jog, 'Morte do Pato')['events'].insert(0, escala())
    com = folha(d, 'Combate')['events']
    acha(com, 'Sons de dano')['events'].insert(0, escala())

    # mortes de propósito não são escaladas
    for x in d['externalEvents']:
        for e in todos(x['events']):
            acs = e.get('actions', [])
            for k in range(len(acs) - 1, -1, -1):
                a = acs[k]
                if a['type']['value'] == 'SetNumberObjectVariable' and a['parameters'][:3] == ['pato', 'vida', '='] \
                        and a['parameters'][3] in ('0', '-10'):
                    acs.insert(k + 1, setn('pato', 'vida_ref', '=', 'pato.vida'))

    toque = next(e for e in acha(com, 'Dano e invencibilidade')['events']
                 if any(c['type']['value'] == 'CollisionNP' and c['parameters'][:2] == ['pato', 'Inimigo'] for c in e['conditions']))
    toque['actions'].append(setn('pato', 'coice_vx', '=', 'sign(pato.CenterX() - Inimigo.CenterX() + 0.001) * pato.dano_empurrao_x'))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'dificuldade_dano' for v in d['variables']), 't196')
