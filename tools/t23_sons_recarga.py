"""Tarefa 23: som de recarga para cada arma (som_recarga_<arma>.wav, de tools/t19_sons_cc0.py).

Quando a recarga de uma arma começa (tecla R ou automática), toca o som dela no canal 6, uma vez. O tom acompanha a duração
real da recarga: com upgrade de recarga (mais curta) o som é tocado mais rápido para terminar junto (limitado a 2x).
Sai o som genérico carregar.mp3 da recarga automática.
Rodar:  python3 tools/t23_sons_recarga.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, C, E, comentario, grupo, procura, upsert, PATH

ARMAS = ('pistola', 'doze', 'minigun', 'lanca')
CANAL = '6'
FB = 'FireBullet::FireBullet'


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    rec = d['resources']['resources']
    for n in ARMAS:
        som = f'som_recarga_{n}.wav'
        if not any(r['name'] == som for r in rec):
            rec.append({'file': 'assets/' + som, 'kind': 'audio', 'metadata': '', 'name': som,
                        'preloadAsMusic': False, 'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True})
    for o in d['objects']:
        if o['name'] in ARMAS:
            upsert(o['variables'], 'som_recarga', False)
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']

    def anda(evs):
        for e in evs:
            yield e
            yield from anda(e.get('events') or [])
    for e in anda(jog):
        acts = e.get('actions') or []
        acts[:] = [a for a in acts if not (a['type']['value'] == 'PlaySound' and a['parameters'][1] == 'carregar.mp3')]
        if any(a['type']['value'] == 'PreloadSound' and a['parameters'][1] == 'som_pistola.wav' for a in acts):
            for n in ARMAS:
                if not any(a['type']['value'] == 'PreloadSound' and a['parameters'][1] == f'som_recarga_{n}.wav' for a in acts):
                    acts.append(A('PreloadSound', '', f'som_recarga_{n}.wav'))

    armas = procura(jog, 'Controle das Armas')
    armas['events'] = [e for e in armas['events'] if e.get('name') != 'Som de recarga']
    subs = [comentario('Toca uma vez quando a recarga começa; o tom segue a duração da recarga (upgrades encurtam).')]
    for n in ARMAS:
        subs.append(E([C(f'{FB}::IsReloadInProgress', n, 'FireBullet', ''), C('BooleanObjectVariable', n, 'som_recarga', 'False', '')],
                      [A('SetBooleanObjectVariable', n, 'som_recarga', 'True', ''),
                       A('PlaySoundOnChannel', '', f'som_recarga_{n}.wav', CANAL, '', '80', '1'),
                       A('SetSoundChannelPitch', '', CANAL, '=', f'clamp({n}.recarga_base / max(0.01, {n}.FireBullet::ReloadDuration()), 1, 2)')]))
        subs.append(E([C(f'{FB}::IsReloadInProgress', n, 'FireBullet', '', inv=True)],
                      [A('SetBooleanObjectVariable', n, 'som_recarga', 'False', '')]))
    armas['events'].append(grupo('Som de recarga', subs))
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
