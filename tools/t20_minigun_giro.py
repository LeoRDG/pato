"""Tarefa 20: giro dos canos da minigun + correção do tom do tiro da minigun.

  - O tiro da minigun era tocado com tom -40 (sobra do som antigo). O GDevelop limita o tom a 0,5..4, então o som saía na METADE
    da velocidade: uma oitava abaixo e com o dobro da duração (sem impacto, "lavado"). Agora toca em tom 1.
  - Giro: o laço som_minigun_giro.wav (tools/t19_sons_cc0.py) toca sempre no canal 5, com volume 0. A variável global `giro`
    (0..1) sobe enquanto o botão de tiro está apertado com a minigun (0,5 s até o giro total) e desce sozinha em ~0,6 s ao soltar;
    volume e tom do canal 5 seguem `giro`. A minigun só atira com giro = 1 (as outras armas não esperam).
Rodar:  python3 tools/t20_minigun_giro.py   (pode rodar de novo). Depois de t16_armas.py. Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, C, E, comentario, grupo, procura, upsert, var, PATH

SOM, CANAL, VOLUME = 'som_minigun_giro.wav', '5', 35
SUBIDA, DESCIDA = 0.5, 1.6      # segundos para os canos chegarem ao giro total; queda por segundo ao soltar


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    if not any(r['name'] == SOM for r in d['resources']['resources']):
        d['resources']['resources'].append({'file': 'assets/' + SOM, 'kind': 'audio', 'metadata': '', 'name': SOM,
                                            'preloadAsMusic': False, 'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True})
    upsert(d['variables'], 'giro', 0)
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']

    def anda(evs):
        for e in evs:
            yield e
            yield from anda(e.get('events') or [])

    for e in anda(jog):
        for a in e.get('actions') or []:
            if a['type']['value'] == 'PlaySoundOnChannel' and a['parameters'][1] == 'som_minigun.wav':
                a['parameters'][5] = '1'                                    # era -40: tocava na metade da velocidade
        acts = e.get('actions') or []
        if any(a['type']['value'] == 'PreloadSound' for a in acts):         # início da cena: liga o laço, mudo
            acts[:] = [a for a in acts if SOM not in a['parameters']]
            acts += [A('PreloadSound', '', SOM), A('PlaySoundOnChannel', '', SOM, CANAL, 'yes', '0', '1')]

    # só a minigun espera os canos: espera_giro = 1 nela, 0 nas outras; a condição do tiro vira "giro + 1 - espera_giro >= 1"
    for o in d['objects']:
        if o['name'] in ('pistola', 'doze', 'minigun', 'lanca'):
            upsert(o['variables'], 'espera_giro', 1 if o['name'] == 'minigun' else 0)
    armas = procura(jog, 'Controle das Armas')
    for e in anda(armas['events']):
        if any(a['type']['value'] == 'FireBullet::FireBullet::FireTowardObject' for a in e.get('actions') or []):
            e['conditions'] = [c for c in e['conditions'] if 'giro' not in ' '.join(c['parameters'])]
            e['conditions'].append(C('BuiltinCommonInstructions::CompareNumbers', 'giro + 1 - Arma.espera_giro', '>=', '1'))
    armas['events'] = [e for e in armas['events'] if e.get('name') != 'Giro da minigun']
    armas['events'].append(grupo('Giro da minigun', [
        comentario(f'Segurar o tiro com a minigun acelera os canos (0 a 1 em {SUBIDA} s); ela só atira com giro = 1. Soltar desacelera. '
                   'O laço do canal 5 acompanha (volume e tom).'),
        E([], [A('SetNumberVariable', 'giro', '=', f'max(0, giro - {DESCIDA} * TimeDelta())')]),
        E([C('MouseButtonFromTextPressed', '', '"Left"'), C('StringVariable', 'arma_atual', '=', '"minigun"')],
          [A('SetNumberVariable', 'giro', '=', f'min(1, giro + ({DESCIDA} + 1 / {SUBIDA}) * TimeDelta())')]),
        E([], [A('SetSoundChannelVolume', '', CANAL, '=', f'{VOLUME} * giro'),
               A('SetSoundChannelPitch', '', CANAL, '=', '0.75 + 0.45 * giro')]),
    ]))
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
