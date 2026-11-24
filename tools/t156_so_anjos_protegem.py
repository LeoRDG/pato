"""Tarefa 156: Deus só fica invulnerável enquanto os anjinhos (canalizadores) canalizam.

- Pupila fechada: sem canalizadores vivos (e fora da troca de fase) a pupila fica aberta ao dano; antes ela só abria na
  janela depois de cada golpe. Saem os fechamentos do piscar (etapas fecha/escuro), que não existe mais.
- Os canalizadores, além de girar, vão e voltam em direção a Deus: o raio da órbita oscila entre canal_orbita_raio e
  canal_orbita_raio - canal_vaivem, a canal_vaivem_vel, cada um numa fase (vaivem_fase, o ângulo em que nasceu).
- O laço de cada canalizador até Deus fere o pato que encostar nele (laco_dano, a menos de laco_raio do segmento).
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t156_so_anjos_protegem.py
"""
from gd_mig import *

ids = Ids('t156')
d_ = 'deus'
C = 'canalizador'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [('canal_vaivem', 90), ('canal_vaivem_vel', 1.6), ('laco_dano', 15),
                                           ('laco_raio', 18)])
    poe_vars(ids, o[C]['variables'], C, [('vaivem_fase', 0), ('laco_t', 0)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')

    guarda = acha(deus['events'], 'Pupila fechada')
    guarda['events'] = [e for e in guarda['events']
                        if not any(c['type']['value'] == 'StringObjectVariable' and c['parameters'][1] == 'etapa'
                                   for c in e['conditions'])]
    fora_fase = txt(d_, 'estado', 'fase')
    fora_fase['type']['inverted'] = True
    guarda['events'].insert(0, ev([cmp('deus.canal_vivos', '=', '0'), bol(d_, 'morto', False), fora_fase],
                                  [setb(d_, 'vulneravel', True)]))

    rosa = acha(deus['events'], 'Anel rosa: amor')
    raio = '(deus.canal_orbita_raio - deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'
    orbita = next(e for e in rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']))
    for a in orbita['actions']:
        if a['type']['value'] == 'SetXY':
            a['parameters'][2] = f'deus.cx + cos(canalizador.ang) * {raio} - canalizador.Width() / 2'
            a['parameters'][4] = f'deus.cy + sin(canalizador.ang) * {raio} - canalizador.Height() / 2'
    for e in todos(deus['events']):
        a = e.get('actions', [])
        if '"Create"}, "parameters": ["", "canalizador"' in tx(a):
            k = next(i for i, x in enumerate(a) if x['parameters'][:2] == [C, 'ang'])
            a.insert(k + 1, setn(C, 'vaivem_fase', '=', 'canalizador.ang'))

    # o laço fere: distância do pato ao segmento canalizador -> centro de Deus
    ax, ay = 'canalizador.CenterX()', 'canalizador.CenterY()'
    t = (f'clamp(((pato.CenterX() - {ax}) * (deus.cx - {ax}) + (pato.CenterY() - {ay}) * (deus.cy - {ay}))'
         f' / max(1, pow(deus.cx - {ax}, 2) + pow(deus.cy - {ay}, 2)), 0, 1)')
    dist = (f'sqrt(pow({ax} + canalizador.laco_t * (deus.cx - {ax}) - pato.CenterX(), 2)'
            f' + pow({ay} + canalizador.laco_t * (deus.cy - {ay}) - pato.CenterY(), 2))')
    k = next(i for i, e in enumerate(rosa['events']) if '"PrimitiveDrawing::LineV2"' in tx(e['actions']))
    rosa['events'].insert(k + 1, cada(C, [bol(C, 'morto', False), bol(d_, 'morto', False)],
                                      [setn(C, 'laco_t', '=', t)], [
        ev([bol(C, 'morto', False), bol('pato', 'invencivel', False), bol('pato', 'morto', False),
            cmp(dist, '<', 'deus.laco_raio')],
           [setn('pato', 'vida', '-', 'deus.laco_dano'), setb('pato', 'invencivel', True), zera('pato', 'iframes'),
            sets('pato', 'ultimo_agressor', 'deus')])]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'laco_dano' for v in objeto(d, 'deus')['variables']), 't156')
