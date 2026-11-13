"""Tarefa 39: DPS do boneco = dano recebido nos últimos 5 s dividido por 5 (janela deslizante).

Substitui a lógica de "série de acertos" (tarefas 36-38, nunca confiável) só dentro do grupo 'Boneco de teste'.
- dps_buf (variável de cena do Hub): array de baldes de boneco.dps_passo segundos (0,1 s); round(dps_janela / dps_passo) baldes = a janela.
- Cada acerto soma o dano no balde do instante; ao entrar num balde novo ele é zerado (sai o dano de 5 s atrás).
- Texto: "DPS " + soma de todos os baldes / boneco.dps_janela.
Rodar uma vez:  python3 tools/t39_boneco_dps_janela.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, var, lista, adiciona_var, objeto, cena, C, A, E, comentario

N = 'round(boneco.dps_janela / boneco.dps_passo)'
SOMA = '"DPS " + ToString(round(dps_soma / boneco.dps_janela))'


def main():
    d = carrega()
    hub = cena(d, 'Hub')
    g = next(e for e in hub['events'] if e.get('name') == 'Boneco de teste')
    if 'dps_buf' in json.dumps(g):
        print('já migrado'); return
    inicio = next(e for e in g['events'] if any(c['type']['value'] == 'SceneJustBegins' for c in e.get('conditions') or []))
    regen = next(e for e in g['events'] if any(c['type']['value'] == 'CompareObjectTimer' and 'regen_espera' in json.dumps(c) for c in e.get('conditions') or []))
    hit = next(e for e in g['events'] if any(c['parameters'][:4] == ['boneco', 'vida', '<', 'boneco.vida_vista'] for c in e.get('conditions') or [])
               and not any(c['parameters'][:2] == ['boneco', 'dps_ativo'] for c in e['conditions']))
    regen['actions'] = [a for a in regen['actions'] if 'dps_' not in json.dumps(a)]
    hit['actions'] = [a for a in hit['actions'] if 'dps_' not in json.dumps(a)]
    hit['actions'].insert(1, A('SetNumberVariable', 'dps_buf[dps_idx]', '+', 'boneco.vida_vista - boneco.vida'))

    avanca = E([], [A('SetNumberVariable', 'dps_idx', '=', f'mod(floor(TimeFromStart() / boneco.dps_passo), {N})')], [
        E([C('BuiltinCommonInstructions::CompareNumbers', 'dps_idx', '!=', 'dps_idx_ant')],
          [A('SetNumberVariable', 'dps_buf[dps_idx]', '=', '0'),
           A('SetNumberVariable', 'dps_idx_ant', '=', 'dps_idx')])])
    soma = E([], [A('SetNumberVariable', 'dps_soma', '=', '0'), A('SetNumberVariable', 'dps_i', '=', '0')], [
        E([], [A('SetNumberVariable', 'dps_soma', '+', 'dps_buf[dps_i]'), A('SetNumberVariable', 'dps_i', '+', '1')],
          tipo='BuiltinCommonInstructions::Repeat', repeatExpression=N)])
    mostra = E([], [
        A('TextContainerCapability::TextContainerBehavior::SetValue', 'boneco_dps', 'Text', '=', SOMA),
        A('SetXY', 'boneco_dps', '=', 'boneco.CenterX() - boneco_dps.Width() / 2', '=', 'boneco.Y() - boneco.dps_altura')])
    g['events'] = [
        comentario('Boneco para testar as armas: leva dano de tudo e, depois de boneco.regen_espera s sem dano, volta à vida cheia. '
                   'O DPS é o dano dos últimos boneco.dps_janela s dividido por dps_janela.'),
        inicio, avanca, hit, regen, soma, mostra]

    bv = objeto(d, 'boneco')['variables']
    bv[:] = [x for x in bv if x['name'] not in ('dps_total', 'dps_tempo', 'dps_ativo', 'dps_min_tempo', 'dps_primeiro', 'dps_pausa')]
    adiciona_var(bv, var('dps_janela', 5))
    adiciona_var(bv, var('dps_passo', 0.1))
    adiciona_var(hub['variables'], lista('dps_buf', []))
    for k, val in dict(dps_idx=0, dps_idx_ant=0, dps_soma=0, dps_i=0).items():
        adiciona_var(hub['variables'], var(k, val))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
