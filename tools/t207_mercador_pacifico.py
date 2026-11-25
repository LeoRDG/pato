"""Tarefa 207: o mercador deixa de ser inimigo.
- Sai dos grupos Inimigo (bala, dano de contato, morte, moedas) e Personagem (barra de vida e números de dano): a bala
  passa por ele e ele não tem mais barra de vida.
- Saem os eventos de hostilidade da Loja > Mercador (contar os golpes, ficar hostil depois de trader.paciencia golpes,
  o gancho Ataques do trader e o que acontece quando ele morre), a barra de chefe do mercador no HUD, a multa de moedas
  quando o pato morria para ele (Morte do Pato) e a variável global trader_morto (também do save).
- Saem as variáveis do mercador que só serviam para isso: paciencia, golpes, vida_vista, multa, dano_hostil, nome_barra,
  rastro_vel. Ele continua virando para o lado do pato e abrindo a loja com E.
Rodar uma vez:  python3 tools/t207_mercador_pacifico.py
"""
from gd_mig import *

VARS_SAEM = ('paciencia', 'golpes', 'vida_vista', 'multa', 'dano_hostil', 'nome_barra', 'rastro_vel')


def migra(d):
    for g in d['objectsGroups']:
        if g['name'] in ('Inimigo', 'Personagem'):
            g['objects'] = [o for o in g['objects'] if o['name'] != 'trader']

    merc = acha(folha(d, 'Loja')['events'], 'Mercador')
    fica = []
    for e in merc['events']:
        s = json.dumps(e)
        hostil = (e.get('name') == 'Ataques do trader' or 'vida_vista' in s or 'trader.paciencia' in s or 'trader_morto' in s)
        if not hostil:
            fica.append(e)
    assert len(merc['events']) - len(fica) == 5, len(merc['events']) - len(fica)
    merc['events'] = fica

    barras = acha(folha(d, 'HUD')['events'], 'Barras de chefe')
    barras['events'] = [e for e in barras['events'] if e.get('name') != 'Mercador']

    morte = acha(folha(d, 'Jogador')['events'], 'Morte do Pato')

    def tira_multa(evs):
        out = []
        for e in evs:
            if any(c['parameters'][:4] == ['pato', 'ultimo_agressor', '=', '"trader"'] for c in e.get('conditions') or []):
                continue
            if e.get('events'):
                e['events'] = tira_multa(e['events'])
            out.append(e)
        return out
    morte['events'] = tira_multa(morte['events'])

    d['variables'] = [v for v in d['variables'] if v['name'] != 'trader_morto']
    for x in [folha(d, 'Jogador'), cena(d, 'Menu')]:
        for e in todos(x['events']):
            if e['type'].endswith('JsCode'):
                e['inlineCode'] = [l.replace('"trader_morto", ', '') for l in e['inlineCode']]

    t = objeto(d, 'trader')
    t['variables'] = [v for v in t['variables'] if v['name'] not in VARS_SAEM]
    for x in d['externalEvents'] + d['layouts']:
        s = json.dumps(x['events'])
        assert 'trader_morto' not in s, x['name']
        for v in VARS_SAEM:
            assert f'trader.{v}' not in s and f'"trader", "{v}"' not in s, (x['name'], v)


if __name__ == '__main__':
    roda(migra, lambda d: not any(o['name'] == 'trader' for g in d['objectsGroups'] if g['name'] == 'Inimigo'
                                  for o in g['objects']), 't207')
