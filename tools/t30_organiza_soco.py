"""Migração única: organiza os eventos de dentro do grupo "Soco" em subgrupos.

  Início                  -> SceneJustBegins (timer do soco e y_antes)
  Teto                    -> subindo sem sair do lugar (Y = y_antes): bateu no teto, zera a queda
  Golpe                   -> o soco no botão direito + rmb_antes (borda do clique)
  Luva e rastro           -> posição da luva e do rastro, e quando somem
  Empurrão nos terrestres -> inimigo socado anda no sentido do soco
  Coice na parede         -> coice_guarda (coyote) e coice_vx
  Guarda a altura         -> y_antes = Y no fim do quadro (o Teto compara no próximo)

A ordem dos eventos não muda. O Teto tem que vir antes do Golpe: o soco na parede põe a
velocidade de queda em soco_vy (para cima) no mesmo quadro, e o Teto, se viesse depois,
veria "subindo sem ter saído do lugar" e cancelaria o coice. Não rode de novo.
Uso: python3 tools/t30_organiza_soco.py [arquivo]  (padrão jogo.json)
"""
import json
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'jogo.json'
ORDEM = ['Início', 'Teto', 'Golpe', 'Luva e rastro', 'Empurrão nos terrestres', 'Coice na parede', 'Guarda a altura']


def carrega():
    s = open(PATH, encoding='utf-8').read()
    return json.loads(s, parse_float=lambda t: '\x00F' + t + '\x00')


def salva(d):
    o = json.dumps(d, indent=2, ensure_ascii=False)
    o = re.sub(r'"\\u0000F(.*?)\\u0000"', r'\1', o)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(o + '\n')


def acha_grupo(evs, nome):
    for e in evs:
        if e.get('type') == 'BuiltinCommonInstructions::Group' and e.get('name') == nome:
            return e
        r = acha_grupo(e.get('events', []), nome)
        if r:
            return r


def tipo(e):
    if e['type'] == 'BuiltinCommonInstructions::Comment':
        c = e.get('comment', '')
        if 'teto' in c:
            return 'Teto'
        if c.startswith('Soco no botão'):
            return 'Golpe'
        if c.startswith('Luva'):
            return 'Luva e rastro'
        raise SystemExit('comentário não reconhecido: ' + c[:80])
    cond = json.dumps(e.get('conditions', []), ensure_ascii=False)
    acts = json.dumps(e.get('actions', []), ensure_ascii=False)
    if 'SceneJustBegins' in cond:
        return 'Início'
    if not e.get('conditions') and 'y_antes' in acts:
        return 'Guarda a altura'
    if 'y_antes' in cond:
        return 'Teto'
    if 'rmb_antes' in cond + acts:
        return 'Golpe'
    if '"soco"' in cond + acts or '"soco_rastro"' in cond + acts:
        return 'Luva e rastro'
    if '"Terrestre"' in cond:
        return 'Empurrão nos terrestres'
    if 'coice_guarda' in cond or 'coice_vx' in cond + acts:
        return 'Coice na parede'
    raise SystemExit('evento não reconhecido: ' + (cond + acts)[:200])


def main():
    d = carrega()
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    g = acha_grupo(jog['events'], 'Soco')
    assert g, 'grupo Soco não encontrado'
    if any(e['type'].endswith('Group') for e in g['events']):
        raise SystemExit('o grupo já tem subgrupos; nada a fazer')

    grupos = {t: [] for t in ORDEM}
    for e in g['events']:
        grupos[tipo(e)].append(e)

    # A ordem tem que ser exatamente a mesma de antes.
    assert [id(e) for e in g['events']] == [id(e) for t in ORDEM for e in grupos[t]], 'juntar mudaria a ordem'

    g['events'] = [{
        'colorB': g.get('colorB', 228), 'colorG': g.get('colorG', 176), 'colorR': g.get('colorR', 74),
        'creationTime': 0, 'name': t, 'source': '',
        'type': 'BuiltinCommonInstructions::Group',
        'events': grupos[t], 'parameters': [],
    } for t in ORDEM if grupos[t]]
    salva(d)
    print('ok:', {t: len(v) for t, v in grupos.items()})


if __name__ == '__main__':
    main()
