"""Tarefa 195: tiro à queima-roupa e bala rápida não atravessam mais inimigo sem acertar.
- A bala nasce na boca do cano; com o inimigo encostado no pato, a boca já fica depois dele e a bala nunca o tocava.
- A bala anda de quadro em quadro (minigun 4000 px/s: ~67 px por quadro) e podia pular inimigos pequenos (moscas).
Agora cada bala guarda onde estava no quadro anterior (projetil.rcx/rcy) e, antes dos eventos de dano, um raio vai de lá até
onde ela está; se passar por um inimigo vivo que essa bala ainda não acertou, a bala é posta no ponto do encontro e o dano
normal acontece. No primeiro quadro o "quadro anterior" é o ombro do pato na linha do cano (pato.tiro_ombro_frac da altura,
o mesmo ponto em que a arma gira), então o comprimento da arma também conta. A bala continua saindo da boca na tela.
Rodar uma vez:  python3 tools/t195_tiro_a_queima_roupa.py
"""
from gd_mig import *

OMBRO_Y = '(pato.Y() + pato.Height() * pato.tiro_ombro_frac)'
D = f'max(0, (bocal_x - pato.CenterX()) * mira_lado * cos(mira_a) + (bocal_y - {OMBRO_Y}) * sin(mira_a))'


def migra(d):
    ids = Ids('t195')
    poe_vars(ids, objeto(d, 'pato')['variables'], 'pato', [('tiro_ombro_frac', 0.68)])
    # o raio grava o ponto do encontro em variáveis da cena (como laser_x/laser_y), então elas ficam em cada cena com o pato
    for l in d['layouts']:
        if any(v['name'] == 'laser_x' for v in l['variables']):
            poe_vars(ids, l['variables'], l['name'], [('tiro_hx', 0), ('tiro_hy', 0)])
    poe_vars(ids, objeto(d, 'projetil')['variables'], 'projetil', [('rcx', 0), ('rcy', 0)])

    com = folha(d, 'Combate')['events']
    proj = acha(com, 'Projéteis')
    balas = acha(proj['events'], 'Balas (alcance, queda e perfuração)')
    ini = balas['events'][0]
    assert '"iniciado", "False"' in json.dumps(ini['conditions'])
    ini['actions'][-1:-1] = [
        setn('projetil', 'rcx', '=', f'bocal_x - mira_lado * cos(mira_a) * {D}'),
        setn('projetil', 'rcy', '=', f'bocal_y - sin(mira_a) * {D}')]
    i = proj['events'].index(balas) + 1
    proj['events'].insert(i, grupo('Varredura da bala (queima-roupa e bala rápida)', [
        cada('projetil', [
            bol('projetil', 'iniciado', True),
            X('RaycastToPosition', 'Inimigo', 'projetil.rcx', 'projetil.rcy', 'projetil.CenterX()', 'projetil.CenterY()',
              'tiro_hx', 'tiro_hy', ''),
            bol('Inimigo', 'morto', False),
            num('Inimigo', 'bala_serie', '!=', 'projetil.serie')],
            [X('SetXY', 'projetil', '=', 'tiro_hx - projetil.Width() / 2', '=', 'tiro_hy - projetil.Height() / 2')])]))
    # fim do quadro: onde a bala está agora vira o "quadro anterior" do próximo
    fim = next(e for e in acha(proj['events'], 'Balas no terreno')['events']
               if [a['parameters'][:2] for a in e['actions']][:1] == [['projetil', 'px']])
    fim['actions'] += [setn('projetil', 'rcx', '=', 'projetil.CenterX()'), setn('projetil', 'rcy', '=', 'projetil.CenterY()')]


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'tiro_ombro_frac' for v in objeto(d, 'pato')['variables']), 't195')
