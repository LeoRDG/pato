"""Tarefa 22: a bombeada da doze usa som_doze_pump.wav (tools/t19_sons_cc0.py) no lugar de carrega_doze.mp3.
Só troca o arquivo da ação existente (o atraso e o canal ficam como estão) e o pré-carrega no início da cena.
Rodar:  python3 tools/t22_som_pump.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, PATH

SOM, ANTIGO = 'som_doze_pump.wav', 'carrega_doze.mp3'


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    if not any(r['name'] == SOM for r in d['resources']['resources']):
        d['resources']['resources'].append({'file': 'assets/' + SOM, 'kind': 'audio', 'metadata': '', 'name': SOM,
                                            'preloadAsMusic': False, 'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True})

    def anda(evs):
        for e in evs:
            yield e
            yield from anda(e.get('events') or [])
    trocas = 0
    for x in d['externalEvents'] + d['layouts']:
        for e in anda(x['events']):
            acts = e.get('actions') or []
            for a in acts:
                if a['type']['value'] == 'PlaySoundOnChannel' and a['parameters'][1] == ANTIGO:
                    a['parameters'][1] = SOM
                    trocas += 1
            if any(a['type']['value'] == 'PreloadSound' and a['parameters'][1] == 'som_doze.wav' for a in acts) \
                    and not any(a['type']['value'] == 'PreloadSound' and a['parameters'][1] == SOM for a in acts):
                acts.append(A('PreloadSound', '', SOM))
    print('ações trocadas:', trocas)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
