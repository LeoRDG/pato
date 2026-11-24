"""Tarefa 186: a arma é escolhida no hub.
- Munição infinita: o FireBullet das 4 armas fica com UnlimitedAmmo; o pente (ShotsPerReload) e a recarga continuam.
  O HUD esconde a reserva ("/ 108") e os 4 slots de troca.
- Pedestais nos 3 hubs (pedestal_arma, uma instância por arma, com as variáveis arma/nome/escala/fase): no começo da
  cena cada um cria um expositor_arma flutuando em cima. Perto de um (pato.arma_raio), aparece "E · NOME"; o E pega a
  arma. A arma equipada some do pedestal (o pedestal fica vazio) e a que o pato largou volta para o dela.
  Só aparecem as armas liberadas (armas.doze/minigun/lanca).
- Nas fases a troca por 1-4 fica desligada (os eventos continuam lá, desativados).
- A cena começa com a arma escolhida (antes só mostrava a pistola) e o jogo novo (Menu) volta para a pistola;
  morrer mantém a arma.
Rodar uma vez:  python3 tools/t186_armas_no_hub.py
"""
import copy
from gd_mig import *

ids = Ids('t186')
ARMAS = [('pistola', 'PISTOLA', 2), ('doze', 'DOZE', 3), ('minigun', 'MINIGUN', 1), ('lanca', 'LANÇA-GRANADAS', 1)]
PEDESTAL = 'assets/hub/pedestal_arma.png'
HUBS = ('Hub', 'HubPurgatorio', 'HubParaiso')
CHAO_Y, PED_H, PED_X0, PED_PASSO, PED_Z = 1010, 60, 190, 170, 1000   # chão dos hubs: y 1010


def objetos(d):
    poe_recursos(d, [PEDESTAL])
    poe_objeto(d, sprite(ids, 'pedestal_arma', [('idle', [PEDESTAL], 1, 1, False)], [
        var(ids, 'pedestal_arma', n, v) for n, v in
        (('arma', 'pistola'), ('nome', 'PISTOLA'), ('escala', 2), ('altura', 10), ('fase', 0))]), 'hub')
    poe_objeto(d, sprite(ids, 'expositor_arma', [(a, [f'arma_{a}.png'], 1, 1, False) for a, _, _ in ARMAS], [
        var(ids, 'expositor_arma', n, v) for n, v in
        (('arma', ''), ('nome', ''), ('base_y', 0), ('fase', 0), ('bob_alt', 6), ('bob_vel', 2.5))]), 'hub')
    dica = copy.deepcopy(objeto(d, 'loja_dica'))
    dica['name'], dica['persistentUuid'] = 'arma_dica', ids('obj/arma_dica')
    poe_objeto(d, dica, 'hub')
    poe_vars(ids, objeto(d, 'pato')['variables'], 'pato', [('arma_raio', 75), ('arma_dica_y', 50),
                                                       ('arma_som_volume', 50), ('arma_som_variacao', 0.05)])


def instancias(d):
    for h in HUBS:
        c = cena(d, h)
        if any(i['name'] == 'pedestal_arma' for i in c['instances']):
            continue
        for k, (a, nome, esc) in enumerate(ARMAS):
            iv = [var(ids, f'inst/{h}/{a}', n, v) for n, v in
                  (('arma', a), ('nome', nome), ('escala', esc), ('fase', k * 1.5))]
            c['instances'].append(inst(ids, 'pedestal_arma', f'{h}/{a}', PED_X0 + k * PED_PASSO, CHAO_Y - PED_H,
                                       PED_Z, variaveis=iv))


def eventos_hub(d):
    E, P, D = 'expositor_arma', 'pedestal_arma', 'arma_dica'
    equipa = [ev([txt(E, 'arma', a)], [setb(a, 'equipada', True), X('Show', a, ''),
                                       X('SetStringVariable', 'arma_atual', '=', f'"{a}"')]) for a, _, _ in ARMAS]
    trava = [ev([txt(E, 'arma', a), cbol(f'armas.{a}', False)], [X('Delete', E, '')]) for a, _, _ in ARMAS[1:]]
    g = grupo('Armas no hub', [
        ev([X('DepartScene', '')], [X('Create', '', D, '0', '0', ''), X('Hide', D)]),
        cada(P, [X('DepartScene', '')], [
            X('Create', '', E, f'{P}.CenterX()', f'{P}.Y()', ''),
            X('SetStringObjectVariable', E, 'arma', '=', f'{P}.arma'),
            X('SetStringObjectVariable', E, 'nome', '=', f'{P}.nome'),
            X('AnimatableCapability::AnimatableBehavior::SetName', E, 'Animation', '=', f'{P}.arma'),
            X('ScalableCapability::ScalableBehavior::SetValue', E, 'Scale', '=', f'{P}.escala'),
            X('SetX', E, '=', f'{P}.CenterX() - {E}.Width() / 2'),
            X('SetY', E, '=', f'{P}.Y() - {P}.altura - {E}.Height()'),
            setn(E, 'base_y', '=', f'{E}.Y()'),
            setn(E, 'fase', '=', f'{P}.fase'),
            X('ChangePlan', E, '=', f'{P}.ZOrder() + 1'),
        ]),
        ev([], [], trava),
        # flutua; a arma que o pato está usando some (o pedestal fica vazio)
        ev([], [X('SetY', E, '=', f'{E}.base_y + sin(TimeFromStart() * {E}.bob_vel + {E}.fase) * {E}.bob_alt'),
                X('Show', E, '')], [
            ev([X('StringObjectVariable', E, 'arma', '=', 'GlobalVariableString(arma_atual)')], [X('Hide', E)]),
        ]),
        ev([], [X('Hide', D)]),
        ev([bol('pato', 'na_loja', False), X('Visible', E), X('Distance', E, 'pato', 'pato.arma_raio', ''),
            X('PickNearest', E, 'pato.CenterX()', 'pato.CenterY()', '')], [
            X('Show', D, ''),
            X('TextContainerCapability::TextContainerBehavior::SetValue', D, 'Text', '=', f'"E · " + {E}.nome'),
            X('SetX', D, '=', f'{E}.CenterX() - {D}.Width() / 2'),
            X('SetY', D, '=', f'{E}.base_y - pato.arma_dica_y'),
            X('ChangePlan', D, '=', f'{E}.ZOrder() + 1'),
        ], [
            ev([X('KeyFromTextJustPressed', '', '"e"')], [
                setb('Arma', 'equipada', False), X('Hide', 'Arma'),
                som('som_troca_arma.wav', 'pato.arma_som_volume',
                    'RandomFloatInRange(1 - pato.arma_som_variacao, 1 + pato.arma_som_variacao)'),
            ], equipa),
        ]),
    ])
    folha(d, 'Hubs')['events'].append(g)


def jogador(d):
    J = folha(d, 'Jogador')['events']
    cria = acha(J, 'Criacao das Armas')
    base = cria['events'][0]
    tem = json.dumps(base, ensure_ascii=False)
    for a, _, _ in ARMAS[1:]:
        if f'"arma_atual", "=", "\\"{a}\\""' not in tem:
            base.setdefault('events', []).append(
                ev([X('StringVariable', 'arma_atual', '=', f'"{a}"')], [setb(a, 'equipada', True), X('Show', a, '')]))
    for e in todos(acha(J, 'Troca de Arma')['events']):
        if 'KeyFromTextJustPressed' in json.dumps(e.get('conditions', [])):
            e['disabled'] = True


def municao_e_hud(d):
    for a, _, _ in ARMAS:
        next(b for b in objeto(d, a)['behaviors'] if b['type'] == 'FireBullet::FireBullet')['UnlimitedAmmo'] = True
    hud = acha(folha(d, 'HUD')['events'], 'HUD')
    hud['events'].append(ev([], [X('Hide', o) for o in
                                 ('max_municao', 'hud_slot1', 'hud_slot2', 'hud_slot3', 'hud_slot4')]))


def menu(d):
    g = acha(cena(d, 'Menu')['events'], 'Ir para o Hub')
    g['events'].insert(0, ev([X('DepartScene', '')], [X('SetStringVariable', 'arma_atual', '=', '"pistola"')]))


def migra(d):
    objetos(d)
    instancias(d)
    eventos_hub(d)
    jogador(d)
    municao_e_hud(d)
    menu(d)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'expositor_arma') is not None, 't186')
