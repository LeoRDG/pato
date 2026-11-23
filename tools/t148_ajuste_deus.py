"""Tarefa 148: ajustes do chefe Deus depois de jogar.

- Corpo menor: todas as partes (e a pupila) ficam deus.corpo_escala do tamanho da arte, e as distâncias que dependiam
  do tamanho acompanham (distancia_baixo, canal_orbita_raio, orbita_raio, pupila_alcance; só mudam se ainda estiverem
  no valor inicial).
- Sinal de vulnerável: com a pupila aberta ao dano ela brilha (efeito Glow "Aberta", pulsando por brilho_forca e
  brilho_pulso) na cor cor_aberta e a barra do chefe fica em barra_cor_aberta; fechada, sem brilho, escurecida
  (cor_fechada) e a barra cinza (barra_cor_fechada).
- Os nomes de efeito e de parâmetro das ações de efeito passam a ir entre aspas (sem elas o GDevelop lia vazio e o
  bloom por fase da t144 não mudava nada).
- Fragmentos só no olhar: em vez de cair o tempo todo, deus.fragmento_qtd pedras aparecem espalhadas pela tela
  (longe de Deus: fragmento_baixo) no começo do olhar, surgindo aos poucos (fragmento_fade) e paradas na tela
  (sobem com a câmera, com uma deriva fragmento_deriva). No fim do olhar (ou numa troca de fase) caem
  (fragmento_queda) e somem abaixo da tela. A arte nova (facetas) ganha máscara nova.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t148_ajuste_deus.py
"""
import os
from gd_mig import *
import gd_luz as luz
from t147_visual_deus import casco

ids = Ids('t148')
d_ = 'deus'
PARTES = ('deus_aura', 'deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa', 'deus_olho', 'deus_escudo', 'deus')
NOVOS = {'distancia_baixo': (150, 230), 'canal_orbita_raio': (260, 200), 'orbita_raio': (260, 170),
         'pupila_alcance': (36, 22)}
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def sinal():
    efeito_ = 'EffectCapability::EffectBehavior::EnableEffect'
    return grupo('Sinal de vulnerável', [
        ev([bol(d_, 'invulneravel', False), bol(d_, 'morto', False)],
           [X(efeito_, d_, 'Effect', '"Aberta"', 'yes'),
            luz.acao_param_efeito_obj(d_, 'Aberta', 'outerStrength',
                                      'deus.brilho_forca * (1 + sin(TimeFromStart() * deus.brilho_pulso)) / 2'),
            X('ChangeColor', d_, 'deus.cor_aberta'), X('TiledSpriteObject::SetColor', 'hud_boss_fill', 'deus.barra_cor_aberta')]),
        ev([bol(d_, 'invulneravel', True)],
           [X(efeito_, d_, 'Effect', '"Aberta"', 'no'), X('ChangeColor', d_, 'deus.cor_fechada'),
            X('TiledSpriteObject::SetColor', 'hud_boss_fill', 'deus.barra_cor_fechada')]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('corpo_escala', 0.6), ('cor_aberta', '255;255;255'), ('cor_fechada', '110;110;140'),
        ('barra_cor_aberta', '255;255;255'), ('barra_cor_fechada', '120;120;130'), ('brilho_forca', 6), ('brilho_pulso', 6),
        ('fragmento_qtd', 5), ('fragmento_deriva', 25), ('fragmento_queda', 600), ('fragmento_baixo', 420),
        ('fragmento_fade', 500)])
    for v in o[d_]['variables']:
        if v['name'] in NOVOS and v.get('value') == NOVOS[v['name']][0]:
            v['value'] = NOVOS[v['name']][1]
    if not any(e['name'] == 'Aberta' for e in o[d_]['effects']):
        o[d_]['effects'].append(efeito('Glow', 'Aberta', {'distance': 12, 'innerStrength': 1, 'outerStrength': 4},
                                       {'color': '255;220;120'}))
    for a in o['fragmento']['animations']:
        for sp in a['directions'][0]['sprites']:
            sp['hasCustomCollisionMask'] = True
            sp['customCollisionMask'] = [[{'x': x, 'y': y} for x, y in casco(os.path.join(RAIZ, sp['image']))]]

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    # nomes de efeito/parâmetro sem aspas (o bloom por fase da t144) não faziam nada
    for e in todos(deus['events']):
        for a in e.get('actions', []):
            if a['type']['value'] == luz.ACAO_PARAM_EFEITO_OBJ:
                a['parameters'][2:4] = [luz._texto(x) for x in a['parameters'][2:4]]
    # corpo menor
    cria = acha(deus['events'], 'Criação')['events'][0]
    cria['actions'] += [X('ScalableCapability::ScalableBehavior::SetValue', p, 'Scale', '=', 'deus.corpo_escala')
                        for p in PARTES]
    # sinal de vulnerável logo depois do dano na pupila
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Dano na pupila')
    deus['events'].insert(k + 1, sinal())
    # fragmentos: não nascem mais por tempo
    frag = acha(deus['events'], 'Fragmentos')
    frag['events'] = [e for e in frag['events'] if '"Create"}, "parameters": ["", "fragmento"' not in tx(e.get('actions', []))]
    frag['events'].append(ev([cbol('luta', True)], [X('OpacityCapability::OpacityBehavior::SetValue', 'fragmento', 'Opacity', '=',
                                                      'min(deus.opacidade_max, fragmento.Opacity() + deus.fragmento_fade * TimeDelta())')]))
    # ... nascem no começo do olhar, espalhados e parados na tela
    ouro = acha(deus['events'], 'Anel de ouro: o olhar')
    inicio = next(e for e in todos(ouro['events']) if '"deus", "etapa", "=", "\\"mira\\""' in tx(e.get('actions', [])))
    inicio.setdefault('events', []).append(repete('deus.fragmento_qtd', [
        X('Create', '', 'fragmento',
          f'RandomInRange({CX} - {CW} / 2 + deus.fragmento_folga, {CX} + {CW} / 2 - deus.fragmento_folga)',
          f'RandomInRange({CY} - {CH} / 2 + deus.fragmento_folga, {CY} + {CH} / 2 - deus.fragmento_baixo)', '""'),
        X('AnimatableCapability::AnimatableBehavior::SetName', 'fragmento', 'Animation', '=', '"f" + ToString(RandomInRange(1, 3))'),
        setn('fragmento', 'vy', '=', 'deus.fragmento_deriva * RandomFloatInRange(-1, 1) - subida_vel'),
        X('OpacityCapability::OpacityBehavior::SetValue', 'fragmento', 'Opacity', '=', '0'),
        X('ChangePlan', 'fragmento', '=', 'deus.fragmento_z')]))
    # ... e caem no fim do olhar e na troca de fase
    fim = next(e for e in todos(ouro['events']) if '"deus", "estado", "=", "\\"fim_golpe\\""' in tx(e.get('actions', [])))
    fim['actions'].append(setn('fragmento', 'vy', '=', 'deus.fragmento_queda'))
    troca = next(e for e in todos(acha(deus['events'], 'Fases')['events'])
                 if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
    troca['actions'].append(setn('fragmento', 'vy', '=', 'deus.fragmento_queda'))


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Sinal de vulnerável') is not None, 't148')
