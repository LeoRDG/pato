import copy
import json
from gd import ext, find_group


def caminhos(evs, pais=()):
    """(evento, condições de todos os pais + as dele) para cada evento."""
    for e in evs:
        conds = pais + tuple(e.get('conditions', []))
        yield e, conds
        yield from caminhos(e.get('events', []), conds)


def armas(jogo):
    return find_group(ext(jogo, 'Jogador')['events'], 'Controle das Armas')


def tem(conds, tipo, params):
    return any(c['type']['value'] == tipo and c['parameters'][:len(params)] == params for c in conds)


def test_recarga_ativa_janela(jogo):
    janela = [conds for e, conds in caminhos(armas(jogo)['events'])
              if any('ReloadTimeLeft' in json.dumps(c) and '0.35' in c['parameters'] for c in e.get('conditions', []))]
    assert janela
    conds = janela[0]
    assert tem(conds, 'BooleanVariable', ['perks.pistola', 'True'])
    assert any('ReloadTimeLeft' in json.dumps(c) and '0.55' in c['parameters'] for c in conds)
    proj = json.dumps(find_group(ext(jogo, 'Combate')['events'], 'Projéteis'), ensure_ascii=False)
    assert '* GlobalVariable(mult_dano) * GlobalVariable(bonus_pente)' in proj
    assert {v['name']: v['value'] for v in jogo['variables'] if v['type'] == 'number'}['bonus_pente'] == 1


def test_doze_recuo_so_com_perk(jogo):
    pulos = [conds for e, conds in caminhos(armas(jogo)['events'])
             if any(a['type']['value'] == 'PlatformBehavior::SetCurrentFallSpeed' for a in e.get('actions', []))]
    assert len(pulos) == 1
    conds = pulos[0]
    assert tem(conds, 'BooleanVariable', ['perks.doze', 'True'])
    assert tem(conds, 'BooleanObjectVariable', ['doze', 'equipada', 'True'])
    assert tem(conds, 'FireBullet::FireBullet::HasJustFired', ['doze'])


def test_minigun_giro(jogo):
    s = json.dumps(armas(jogo), ensure_ascii=False)
    assert '3 - 2 * min(1, TimerElapsedTime(\\"giro\\"))' in s
    assert 'FireBullet::FireBullet::SetHeatPerShot' in s


def test_sem_perk_igual_main(jogo, jogo_main):
    """Tirando os eventos de perk (cada um sob um pai perks.<x> True) e as travas da run, o grupo é o mesmo da main."""
    def limpa(evs):
        saida = []
        for e in evs:
            if any(c['type']['value'] == 'BooleanVariable' and c['parameters'][0].startswith('perks.') for c in e.get('conditions', [])):
                continue
            e = copy.deepcopy(e)
            if 'conditions' in e:
                e['conditions'] = [c for c in e['conditions'] if not c['parameters'][:1] in (['run.oferta_aberta'], ['run.caronte_aberto'])]
            if 'events' in e:
                e['events'] = limpa(e['events'])
            saida.append(e)
        return saida
    agora = armas(jogo)
    assert limpa(agora['events']) == armas(jogo_main)['events']
    assert len(json.dumps(agora)) > len(json.dumps(armas(jogo_main))) + 2000
