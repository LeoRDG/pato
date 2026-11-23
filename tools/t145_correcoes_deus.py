"""Tarefa 145: correções da revisão final do chefe Deus.

1. Morte: Combate apaga a pupila (deus) 1 s depois de morrer, então a limpeza das partes do corpo passa a contar o
   tempo num relógio do olho (deus_olho, "morte_deus", deus_olho.morte_tempo) e não depende mais da pupila; e o corpo
   só é posicionado enquanto a pupila existe (senão o olho pulava para a origem do mundo).
2. Anel de ouro: RaycastToPosition invertido só é verdadeiro quando ACERTA um fragmento, então a queima estava
   invertida. Agora um raio normal marca pato.na_sombra e o feixe só queima com na_sombra falso.
3. Troca de fase no meio de um golpe: limpa a etapa e as sobras dos golpes (escuro, halos, feixe, luz da pupila,
   pupila escondida, clarão), senão nenhum golpe começava de novo.
4. Pupila fechada: com canalizadores vivos (escudo de pé) ou com o olho fechado no piscar, vulneravel fica falso,
   mesmo durante a janela do anel rosa.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t145_correcoes_deus.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t145')
d_ = 'deus'
PARTES = ('deus_aura', 'deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa', 'deus_olho', 'deus_escudo')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    o = {x['name']: x for x in d['objects']}
    vd = {v['name']: v.get('value') for v in o[d_]['variables']}
    poe_vars(ids, o['deus_olho']['variables'], 'deus_olho', [('morte_tempo', vd.get('morte_tempo', 2.6))])
    poe_vars(ids, o['pato']['variables'], 'pato', [('na_sombra', False)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')

    # 1. morte sem depender da pupila
    morte = acha(deus['events'], 'Morte')
    inicio = next(e for e in morte['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
    inicio['actions'].append(zera('deus_olho', 'morte_deus'))
    morte['events'].append(ev([X('SceneInstancesCount', '', 'deus', '=', '0'),
                               X('SceneInstancesCount', '', 'deus_olho', '>', '0'),
                               timer('deus_olho', 'morte_deus', '>', 'deus_olho.morte_tempo')],
                              [X('Delete', p, '') for p in PARTES]))
    corpo = acha(deus['events'], 'Corpo')
    poe = next(e for e in corpo['events'] if '"SetXY"}, "parameters": ["deus_olho"' in tx(e['actions']))
    poe['conditions'].append(X('SceneInstancesCount', '', 'deus', '>', '0'))

    # 2. o feixe queima quem NÃO está na sombra
    ouro = acha(deus['events'], 'Anel de ouro: o olhar')
    pai = next(e for e in todos(ouro['events'])
               if any('"pato", "vida", "-"' in tx(f.get('actions', [])) for f in e.get('events', [])))
    k, queima = next((i, f) for i, f in enumerate(pai['events']) if '"pato", "vida", "-"' in tx(f.get('actions', [])))
    queima['conditions'] = [c for c in queima['conditions'] if c['type']['value'] != 'RaycastToPosition']
    queima['conditions'].append(bol('pato', 'na_sombra', False))
    pai['events'].insert(k, ev([], [setb('pato', 'na_sombra', False)], [
        ev([X('RaycastToPosition', 'fragmento', 'deus.px', 'deus.py', 'pato.CenterX()', 'pato.CenterY()',
              'olhar_rx', 'olhar_ry', '')], [setb('pato', 'na_sombra', True)])]))

    # 3. troca de fase limpa o golpe interrompido
    fases = acha(deus['events'], 'Fases')
    troca = next(e for e in fases['events'] if '"deus", "estado", "=", "\\"fase\\""' in tx(e['actions']))
    troca['actions'] += [sets(d_, 'etapa', ''), setb(d_, 'janela_amor', False),
                         luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_normal'),
                         luz.acao_raio_luz('luz_pato', 'luz_pato_raio'),
                         luz.acao_raio_luz('luz_olhar', 'deus.olhar_raio_idle'),
                         X('Show', d_, ''), X('Delete', 'luz_halo', ''), X('Delete', 'feixe_olhar', '')]

    # 4. pupila fechada com escudo de pé ou olho fechado
    guarda = grupo('Pupila fechada', [
        ev([cmp('deus.canal_vivos', '>', '0')], [setb(d_, 'vulneravel', False), setb(d_, 'janela_amor', False)]),
        ev([txt(d_, 'etapa', 'fecha')], [setb(d_, 'vulneravel', False)]),
        ev([txt(d_, 'etapa', 'escuro')], [setb(d_, 'vulneravel', False)]),
    ])
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Dano na pupila')
    deus['events'].insert(k, guarda)


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Pupila fechada') is not None, 't145')
