"""Tarefa 42: o ricochete às vezes não quicava a granada (correção da tarefa 41).

Causa: depois de quicar, a bala gira para a nova direção, e a máscara de colisão fica na metade da frente do sprite.
O ângulo vinha só da força (sem a gravidade projetil.gy): a granada lançada para cima cai descendo, e o ricochete
a apontava para baixo, girando a máscara para dentro do chão; o evento seguinte apagava a granada logo depois da explosão.
Correção: o ângulo segue a velocidade real (força + gravidade) e, se a máscara girada ainda tocar o terreno,
volta o ângulo de antes (que estava livre no quadro anterior).
Rodar uma vez:  python3 tools/t42_ricochete_angulo.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, var, adiciona_var, objeto, externo, C, A, E

VELHO = 'ToDeg(atan2(projetil.fy, projetil.fx))'
NOVO = 'ToDeg(atan2(projetil.fy + projetil.gy, projetil.fx))'


def main():
    d = carrega()
    proj = next(e for e in externo(d, 'Combate')['events'] if e.get('name') == 'Projéteis')['events']
    ric = next(e for e in proj if e['type'] == 'BuiltinCommonInstructions::ForEach'
               and any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or []))
    if '"ang"' in json.dumps(ric):
        print('já migrado'); return
    final = ric['events'][-1]
    gira = next((a for a in final['actions'] if a['type']['value'] == 'SetAngle' and a['parameters'][2] == VELHO), None)
    if gira is None:
        raise SystemExit('O ângulo do ricochete foi editado no GDevelop; nada alterado')
    adiciona_var(objeto(d, 'projetil')['variables'], var('ang', 0))
    gira['parameters'][2] = NOVO
    i = final['actions'].index(gira)
    final['actions'].insert(i, A('SetNumberObjectVariable', 'projetil', 'ang', '=', 'projetil.Angle()'))
    final.setdefault('events', []).append(
        E([C('CollisionNP', 'projetil', 'Terreno', '', '', '')], [A('SetAngle', 'projetil', '=', 'projetil.ang')]))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
