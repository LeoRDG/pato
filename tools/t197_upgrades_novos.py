"""Tarefa 197: quatro upgrades novos na loja, feitos em cima de sistemas que já existem.
- Vampirismo: cada inimigo morto cura pato.vamp_cura de vida por nível (até a vida máxima).
- Ímã: as moedas vêm de mais longe: o alcance do ímã (moeda.iman_dist) cresce pato.upg_ima por nível (+100%).
- Incendiária: a bala põe fogo no inimigo por pato.queima_tempo s; a cada pato.queima_intervalo s ele perde
  pato.queima_dano * nível (com o bônus de dano) e solta brasas (sangue_brasa). Variáveis queima/queima_tick em cada inimigo.
- Cadáver explosivo: o inimigo que morre explode como a granada (explosao_fogo, que já fere os inimigos em volta), com
  dano pato.cadaver_dano * nível, raio pato.cadaver_raio e empurrão pato.cadaver_repulsao: dá para fazer reação em cadeia.
O painel do mercador cresce uma linha por item novo (ui_rod_y e ui_m_h somam ui_m_lin_loja por item, a partir do valor atual).
Os preços seguem os dos outros itens; a tarefa de preços (t198) ajusta tudo junto.
Rodar uma vez:  python3 tools/t197_upgrades_novos.py
"""
import copy
from gd_mig import *

NOVOS = [
    ('vampirismo', 'Vampirismo', 'Cada inimigo morto cura 4 de vida por nivel'),
    ('ima', 'Ima', 'As moedas vem de mais longe: +100% de alcance do ima por nivel'),
    ('incendiaria', 'Incendiaria', 'A bala poe fogo no inimigo: dano a cada meio segundo por 2 s; +dano por nivel'),
    ('cadaver', 'Cadaver Explosivo', 'Inimigo morto explode e fere quem estiver perto; +dano por nivel'),
]
NIVEL = lambda u: f'GlobalVariable(upgrades.{u})'


def migra(d):
    ids = Ids('t197')
    poe_vars(ids, objeto(d, 'pato')['variables'], 'pato', [
        ('vamp_cura', 4), ('upg_ima', 1), ('queima_tempo', 2), ('queima_intervalo', 0.5), ('queima_dano', 4),
        ('cadaver_dano', 30), ('cadaver_raio', 160), ('cadaver_repulsao', 500), ('cadaver_som_volume', 45)])
    upg = next(v for v in d['variables'] if v['name'] == 'upgrades')
    poe_vars(ids, upg['children'], 'upgrades', [(u, 0) for u, _, _ in NOVOS])
    upg['children'].sort(key=lambda c: c['name'])
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    tem = {next(c['value'] for c in it['children'] if c['name'] == 'id') for it in cat['children']}
    modelo = next(it for it in cat['children'] if any(c['name'] == 'id' and c['value'] == 'eletricidade' for c in it['children']))
    novos = 0
    for u, nome, desc in NOVOS:
        if u in tem:
            continue
        it = copy.deepcopy(modelo)
        it['persistentUuid'] = ids(f'cat/{u}')
        for c in it['children']:
            c['persistentUuid'] = ids(f'cat/{u}/{c["name"]}')
            c['value'] = {'id': u, 'nome': nome, 'descricao': desc, 'requer': ''}.get(c['name'], c['value'])
        cat['children'].append(it)
        novos += 1
    for nome in ('ui_rod_y', 'ui_m_h'):
        v = next(x for x in d['variables'] if x['name'] == nome)
        v['value'] += novos * next(x for x in d['variables'] if x['name'] == 'ui_m_lin_loja')['value']

    g = next(g for g in d['objectsGroups'] if g['name'] == 'Inimigo')
    for o in g['objects']:
        poe_vars(ids, objeto(d, o['name'])['variables'], o['name'], [('queima', 0), ('queima_tick', 0)])

    com = folha(d, 'Combate')['events']
    # vampirismo e cadáver explosivo: quando o inimigo morre
    morte = acha(com, 'Morte do Inimigo')['events'][0]
    assert '"morto", "True"' in json.dumps(morte['actions'])
    # um por inimigo que morreu neste quadro (vários podem morrer juntos, ex.: na explosão)
    morte['events'] = (morte.get('events') or []) + [cada('Inimigo', [], [], [
        ev([cmp(NIVEL('vampirismo'), '>', '0'), bol('pato', 'morto', False)], [
            setn('pato', 'vida', '=', f'min(pato.max_vida, pato.vida + pato.vamp_cura * {NIVEL("vampirismo")})')]),
        ev([cmp(NIVEL('cadaver'), '>', '0')], [
            som('som_explosao.wav', 'pato.cadaver_som_volume', 'RandomFloatInRange(1.1, 1.3)'),
            X('Create', '', 'explosao_fumaca', 'Inimigo.CenterX()', 'Inimigo.CenterY()', ''),
            X('Create', '', 'explosao_fogo', 'Inimigo.CenterX()', 'Inimigo.CenterY()', ''),
            X('Create', '', 'explosao_faiscas', 'Inimigo.CenterX()', 'Inimigo.CenterY()', ''),
            setn('explosao_fogo', 'dano', '=', f'pato.cadaver_dano * {NIVEL("cadaver")}'),
            setn('explosao_fogo', 'raio', '=', 'pato.cadaver_raio'),
            setn('explosao_fogo', 'repulsao', '=', 'pato.cadaver_repulsao')]),
    ])]
    # ímã
    ima = acha(com, 'Ímã e sumiço')['events'][0]
    c = next(c for c in ima['conditions'] if c['type']['value'] == 'Distance')
    c['parameters'][2] = f'moeda.iman_dist * (1 + pato.upg_ima * {NIVEL("ima")})'
    # incendiária: a bala acende, o fogo queima com o tempo
    dano = acha(com, 'Dano da bala')['events'][0]
    assert any(a['parameters'][:2] == ['Inimigo', 'bala_serie'] for a in dano['actions'])
    dano['events'].insert(0, ev([cmp(NIVEL('incendiaria'), '>', '0')], [setn('Inimigo', 'queima', '=', 'pato.queima_tempo')]))
    proj = acha(com, 'Projéteis')
    proj['events'].append(grupo('Fogo da bala incendiária', [
        cada('Inimigo', [num('Inimigo', 'queima', '>', '0'), bol('Inimigo', 'morto', False), bol('Inimigo', 'invulneravel', False)], [
            setn('Inimigo', 'queima', '-', 'TimeDelta()'), setn('Inimigo', 'queima_tick', '+', 'TimeDelta()')], [
            ev([num('Inimigo', 'queima_tick', '>=', 'pato.queima_intervalo')], [
                setn('Inimigo', 'queima_tick', '-', 'pato.queima_intervalo'),
                setn('Inimigo', 'vida', '-', f'max(1, round(pato.queima_dano * {NIVEL("incendiaria")} * GlobalVariable(mult_dano)))'),
                X('Create', '', 'sangue_brasa', 'Inimigo.CenterX() + RandomFloatInRange(-0.3, 0.3) * Inimigo.Width()',
                  'Inimigo.CenterY() + RandomFloatInRange(-0.3, 0.3) * Inimigo.Height()', ''),
                X('SetAngle', 'sangue_brasa', '=', '-90')])]),
        cada('Inimigo', [num('Inimigo', 'queima', '<=', '0'), num('Inimigo', 'queima_tick', '>', '0')], [
            setn('Inimigo', 'queima_tick', '=', '0')]),
    ]))


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'vampirismo' for v in d['variables'] if v['name'] == 'upgrades' for c in v['children']), 't197')
