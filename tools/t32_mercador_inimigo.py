"""Tarefa 32: o mercador é um inimigo secreto.

- Calmo: não machuca ao encostar. Cada golpe (bala, explosão, soco: qualquer perda de vida) gasta paciência;
  ao esgotar (golpes >= paciencia) ele fica hostil, passa a causar trader.dano_hostil e fecha a loja.
- Hostil: barra de vida (hud_boss_*) com trader.nome_barra. Ataques: grupo 'Ataques do trader' (a fazer).
- Se o mercador mata o pato, o pato perde round(moedas_total * trader.multa) moedas (nunca fica negativo) e o resumo avisa.
- Se o pato mata o mercador: global trader_morto = verdadeiro e grupo 'Quando o trader morre' (a decidir).
Rodar uma vez:  python3 tools/t32_mercador_inimigo.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, externo, anda, C, A, E, comentario, grupo


def unico(lista, desc):
    if len(lista) != 1:
        raise SystemExit(f'{desc}: esperado 1, achei {len(lista)}; nada alterado')
    return lista[0]


def mercador():
    calmo = C('StringObjectVariable', 'trader', 'estado', '=', '"calmo"')
    return [
        comentario('Calmo: cada vez que a vida do mercador cai (bala, explosão ou soco) conta um golpe. '
                   'Quando os golpes chegam à paciência, ele fica hostil e fecha a loja.'),
        E([C('SceneJustBegins', '')], [A('SetNumberObjectVariable', 'trader', 'vida_vista', '=', 'trader.vida')]),
        E([calmo, C('NumberObjectVariable', 'trader', 'vida', '<', 'trader.vida_vista')],
          [A('SetNumberObjectVariable', 'trader', 'golpes', '+', '1'),
           A('SetNumberObjectVariable', 'trader', 'vida_vista', '=', 'trader.vida')]),
        E([calmo, C('NumberObjectVariable', 'trader', 'golpes', '>=', 'trader.paciencia')],
          [A('SetStringObjectVariable', 'trader', 'estado', '=', '"hostil"'),
           A('SetNumberObjectVariable', 'trader', 'dano', '=', 'trader.dano_hostil'),
           A('AnimatableCapability::AnimatableBehavior::SetName', 'trader', 'Animation', '=', '"idle"')],
          [E([C('BooleanVariable', 'loja_aberta', 'True', '')], [A('SetStringVariable', 'loja_acao', '=', '"fechar"')])]),
        grupo('Ataques do trader', [comentario('A fazer: ataques do mercador hostil (trader.estado = "hostil"). '
                                               'Projéteis dele devem ter projetil_inimigo.origem = "trader" para a multa valer.')]),
        E([C('BooleanObjectVariable', 'trader', 'morto', 'True', ''), C('BuiltinCommonInstructions::Once')],
          [A('SetBooleanVariable', 'trader_morto', 'True', '')],
          [grupo('Quando o trader morre', [comentario('A decidir: o que muda quando o pato mata o mercador (global trader_morto).')])]),
    ]


def barra():
    nome = ['hud_boss_trilho', 'hud_boss_rastro', 'hud_boss_fill', 'hud_boss_nome']
    return [
        comentario('Barra de vida do mercador hostil, usando a barra do boss do HUD.'),
        E([C('StringObjectVariable', 'trader', 'estado', '=', '"hostil"'), C('BooleanObjectVariable', 'trader', 'morto', 'False', '')],
          [A('Show', n, '') for n in nome] + [
              A('ResizableCapability::ResizableBehavior::SetWidth', 'hud_boss_fill', 'Resizable', '=',
                'hud_boss_trilho.Width() * clamp(trader.vida / trader.max_vida, 0, 1)'),
              A('SetXY', 'hud_boss_fill', '=', 'hud_boss_trilho.X()', '=', 'hud_boss_trilho.Y()'),
              A('SetXY', 'hud_boss_rastro', '=', 'hud_boss_trilho.X()', '=', 'hud_boss_trilho.Y()'),
              A('TextContainerCapability::TextContainerBehavior::SetValue', 'hud_boss_nome', 'Text', '=', 'trader.nome_barra'),
              A('SetXY', 'hud_boss_nome', '=', 'hud_boss_trilho.X() + hud_boss_trilho.Width() / 2 - hud_boss_nome.Width() / 2',
                '=', 'hud_boss_trilho.Y() - 30')]),
    ]


def main():
    d = carrega()
    loja = externo(d, 'Loja')['events']
    g_merc = unico([e for e in loja if e.get('name') == 'Mercador'], 'grupo Mercador')
    if 'hostil' in json.dumps(g_merc):
        print('já migrado'); return
    g_barra = unico([e for e in loja if e.get('name') == 'Barra do mercador'], 'grupo Barra do mercador')

    dano = unico([e for e in anda(externo(d, 'Combate')['events']) if e.get('name') == 'Dano e invencibilidade'], 'Dano e invencibilidade')
    contato = unico([e for e in dano['events'] if any(c['type']['value'] == 'CollisionNP' and c['parameters'][:2] == ['pato', 'Inimigo']
                                                      for c in e.get('conditions') or [])], 'evento de contato')
    bala = unico([e for e in dano['events'] if any(c['parameters'][:2] == ['projetil_inimigo', 'pato'] for c in e.get('conditions') or [])
                  and any(c['parameters'][:3] == ['pato', 'invencivel', 'False'] for c in e['conditions'])], 'evento de bala')

    morte = unico([e for e in anda(externo(d, 'Jogador')['events']) if e.get('name') == 'Morte do Pato'], 'Morte do Pato')
    ao_morrer = unico([e for e in morte['events'] if any(a['parameters'][:3] == ['pato', 'morto', 'True'] for a in e.get('actions') or [])
                       and any(c['parameters'][:3] == ['pato', 'vida', '<='] for c in e.get('conditions') or [])], 'evento da morte')
    resumo = unico([e for e in morte['events'] if any(a['type']['value'] == 'Create' and a['parameters'][1] == 'resumo_txt'
                                                      for a in e.get('actions') or [])], 'evento do resumo')
    centra = resumo['events'][-1]
    assert any(a['type']['value'] == 'SetXY' and a['parameters'][0] == 'resumo_txt' for a in centra['actions']), 'SetXY do resumo não é o último'

    g_merc['events'] += mercador()
    g_barra['events'] += barra()
    contato['conditions'].append(C('StringObjectVariable', 'Inimigo', 'estado', '!=', '"calmo"'))
    contato['actions'].append(A('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', 'Inimigo.ObjectName()'))
    bala['actions'].insert(0, A('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', 'projetil_inimigo.origem'))
    ao_morrer['events'].append(E(
        [C('StringObjectVariable', 'pato', 'ultimo_agressor', '=', '"trader"')],
        [A('SetNumberObjectVariable', 'pato', 'moedas_perdidas', '=', 'round(GlobalVariable(moedas_total) * trader.multa)'),
         A('SetNumberVariable', 'moedas_total', '=', 'max(0, GlobalVariable(moedas_total) - pato.moedas_perdidas)')]))
    resumo['events'].insert(len(resumo['events']) - 1, E(
        [C('NumberObjectVariable', 'pato', 'moedas_perdidas', '>', '0')],
        [A('TextContainerCapability::TextContainerBehavior::SetValue', 'resumo_txt', 'Text', '+',
           'NewLine() + NewLine() + "O mercador levou " + ToString(pato.moedas_perdidas) + " moedas"')]))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
