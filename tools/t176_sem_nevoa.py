"""Tarefa 176: tira a névoa do Purgatório (purg_nevoa, t171/t175).

As partículas do GDevelop só sabem sumir, não aparecer aos poucos: cada tufo grande de névoa nascia já opaco e parecia
um holofote acendendo. Sai o objeto, os eventos que o criavam e o moviam (fase e hub) e a variável purg_nevoa_z.
As cinzas (purg_cinza) ficam.
Rodar uma vez:  python3 tools/t176_sem_nevoa.py
"""
from gd_mig import *

N = 'purg_nevoa'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def limpa(evs):
    fica = []
    for e in evs:
        if e.get('events'):
            e['events'] = limpa(e['events'])
        if f'"{N}"' in tx(e.get('conditions', [])) + tx(e.get('actions', [])):
            continue
        fica.append(e)
    return fica


def migra(d):
    d['objects'] = [o for o in d['objects'] if o['name'] != N]
    for sc in d['layouts']:
        if N not in tx(sc):
            continue
        sc['events'] = limpa(sc['events'])
        sc['variables'] = [v for v in sc['variables'] if v['name'] != f'{N}_z']
        sc['instances'] = [i for i in sc['instances'] if i['name'] != N]
        sc['objects'] = [o for o in sc.get('objects', []) if o['name'] != N]
    def tira_pasta(no):
        if isinstance(no, dict):
            if 'children' in no:
                no['children'] = [c for c in no['children'] if c.get('objectName') != N]
            for v in no.values():
                tira_pasta(v)
        elif isinstance(no, list):
            for v in no:
                tira_pasta(v)
    tira_pasta(d.get('objectsFolderStructure', {}))
    for gr in d.get('objectsGroups', []):
        gr['objects'] = [o for o in gr['objects'] if o['name'] != N]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, N) is None, 't176')
