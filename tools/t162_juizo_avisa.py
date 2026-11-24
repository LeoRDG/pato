"""Tarefa 162: o Juízo passa a avisar, e os anjinhos nascem colados em Deus.

- deus.juizo_carga vai de 0 a 1 durante o Juízo (tempo do golpe / juizo_tempo) e fica 0 fora dele. Os laços engrossam
  (laco_espessura * (1 + juizo_engrossa * carga)) e brilham mais (Glow outerStrength = laco_brilho * (1 + juizo_brilha
  * carga)) conforme o prazo chega.
- Um som (som_luz, tom juizo_aviso_tom) toca juizo_aviso segundos antes do clarão, se ainda houver anjinho vivo
  (juizo_avisou impede repetir; volta a falso quando o Juízo começa).
- Os anjinhos nasciam já na órbita, que com o vai e vem podia estar longe de Deus, e o laço pegava o pato sem tempo de
  reagir. Agora cada um tem canalizador.surgir, que vai de 0 a 1 em canal_surgir segundos e multiplica o raio: nasce
  no centro de Deus e se afasta aos poucos.
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t162_juizo_avisa.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t162')
d_ = 'deus'
C = 'canalizador'
RAIO = '(deus.canal_orbita_raio + deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('juizo_carga', 0), ('juizo_engrossa', 2), ('juizo_brilha', 2), ('laco_brilho', 5), ('juizo_aviso', 1),
        ('juizo_aviso_tom', 1.4), ('juizo_avisou', False), ('canal_surgir', 1.2)])
    poe_vars(ids, o[C]['variables'], C, [('surgir', 0)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    rosa = acha(deus['events'], 'Anel rosa: amor')

    # anjinhos nascem colados e se afastam
    for e in todos(deus['events']):
        a = e.get('actions', [])
        if '"Create"}, "parameters": ["", "canalizador"' in tx(a):
            k = next(i for i, x in enumerate(a) if x['type']['value'] == 'Create' and x['parameters'][1] == C)
            a.insert(k + 1, setn(C, 'surgir', '=', '0'))
    orbitas = [e for e in rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions'])]
    for e in orbitas:
        for a in e['actions']:
            if a['type']['value'] == 'SetXY':
                a['parameters'][2] = a['parameters'][2].replace(RAIO, f'canalizador.surgir * {RAIO}')
                a['parameters'][4] = a['parameters'][4].replace(RAIO, f'canalizador.surgir * {RAIO}')
    a = orbitas[0]['actions']
    k = next(i for i, x in enumerate(a) if x['type']['value'] == 'SetXY')
    a.insert(k, setn(C, 'surgir', '=', 'min(1, canalizador.surgir + TimeDelta() / deus.canal_surgir)'))

    # carga do Juízo: laços engrossam e brilham
    juizo = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'juizo'), txt(d_, 'etapa', 'juizo')]
    k = next(i for i, e in enumerate(rosa['events']) if '"PrimitiveDrawing::LineV2"' in tx(e['actions']))
    linha = rosa['events'][k]
    for x in linha['actions']:
        if x['type']['value'] == 'PrimitiveDrawing::LineV2':
            x['parameters'][5] = 'deus.laco_espessura * (1 + deus.juizo_engrossa * deus.juizo_carga)'
    rosa['events'][k:k] = [
        ev([], [setn(d_, 'juizo_carga', '=', '0')]),
        ev(juizo, [setn(d_, 'juizo_carga', '=', 'min(1, deus.ObjectTimerElapsedTime("golpe") / deus.juizo_tempo)')]),
        ev([], [luz.acao_param_efeito_obj('laco_amor', 'Effect', 'outerStrength',
                                          'deus.laco_brilho * (1 + deus.juizo_brilha * deus.juizo_carga)')]),
        ev(juizo + [bol(d_, 'juizo_avisou', False), timer(d_, 'golpe', '>', 'deus.juizo_tempo - deus.juizo_aviso'),
                    cmp('deus.canal_vivos', '>', '0')],
           [setb(d_, 'juizo_avisou', True), som('som_luz.wav', 'deus.som_volume', 'deus.juizo_aviso_tom')]),
    ]
    comeca = next(e for e in todos(rosa['events']) if '"deus", "etapa", "=", "\\"juizo\\""' in tx(e.get('actions', [])))
    comeca['actions'].append(setb(d_, 'juizo_avisou', False))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'juizo_carga' for v in objeto(d, 'deus')['variables']), 't162')
