"""Tarefa 78: cada inimigo comum ganha uma mecânica própria (inspirada em The Binding of Isaac e Enter the Gungeon), em vez
de todos que andam fazerem "anda até o pato e dá um bote" e todos que voam fazerem "fica em cima e mergulha".

INFERNO
  condenado          se levanta: abaixo de cair_abaixo de vida cai no chão (inofensivo) e, se não for acabado em caido_tempo s,
                     levanta com levanta_vida, mais rápido (levanta_vel_fator) e avermelhado. Só levanta levanta_max vezes.
  condenada          joga ossos: fica entre dist_min e dist_max e joga osso_qtd ossos em arco (osso_tempo s de voo) em leque
                     de osso_espalha px em volta do pato: acertam atrás de parede baixa, então não dá para ficar parado.
  condenado_torto    pulador: só anda pulando, pulinhos tortos (pulo_alt_min..max, pulo_vx) que às vezes vão para longe do pato,
                     e de vez em quando (salto_chance, ou se o pato está acima) um salto grande em cima dele.
  condenado_azul     investida: alinhado com o pato (|dy| < carga_alt, |dx| < carga_alcance) ruge por carga_aviso s e corre em
                     linha reta a carga_vel até bater numa parede; encostar no caminho tira carga_dano e joga longe. Bateu na
                     parede: fica tonto (inofensivo) por atordoa_tempo s. Pule por cima e deixe ele bater.
  condenado_inchado  bolsa de bile: acelera quanto mais perto (acelera), pisca e explode como antes; morrer de qualquer jeito
                     (inclusive a tiro) estoura bile_qtd bolhas de bile em anel: mate de longe.
  arvore_condenada   espinheiro: parada, treme por aviso_tempo s e atira um leque de espinho_qtd espinhos (espinho_leque graus)
                     no pato; a cada anel_cada ataques solta um anel de anel_qtd espinhos lentos.
  caveira_gigante    além da explosão de fogo, de espiral_espera em espiral_espera s para e gira uma espiral de bolas de fogo
                     (espiral_bracos braços, espiral_giro graus por rajada) por espiral_duracao s.
  caveira_azul       caveira da morte: quica pelo cenário em diagonal sem parar e ganha velocidade a cada quique; bala não
                     machuca (ricocheteia), só o soco (e explosão não). Fica a area_raio px de onde nasceu.
  cabeca_voadora     investida mirada: paira a distancia px do pato, treme e mira por investida_aviso s e dispara em linha reta
                     na direção travada a investida_vel; batendo no terreno fica tonta.
  diabinho           ladrão: rói o osso até ver o pato; aí orbita em volta dele e dá botes. Encostar rouba até roubo_max moedas
                     e ele foge rindo: se não for morto em fuga_tempo s, some com elas. Morto, devolve tudo.
  moscas             enxame com inércia: aceleram até o pato (acel) e passam direto, fazendo curva; acertar uma acorda as outras
                     a menos de alerta_raio.
  olho_demoniaco     raio: mira com uma linha fina que segue o pato devagar (mira_giro graus/s) por mira_tempo s, trava por
                     trava_tempo s (a linha pisca) e dispara um raio de raio_largura px por raio_tempo s, que para na parede.
  mina_demoniaca     morrer de qualquer jeito explode: dano no pato a menos de explosao_raio, estilhaco_qtd estilhaços de fogo e
                     dano_inimigos nos inimigos perto, inclusive outras minas (reação em cadeia).
PURGATÓRIO
  zumbi              sem cabeça: abaixo de frenesi_abaixo da vida perde a cabeça e corre a frenesi_vel trocando de direção
                     (a frenesi_troca_min..max s), pulando à toa e sem tomar tranco.
  pigman             pancada: a menos de salto_alcance avisa e salta no pato (salto_tempo s de voo); ao cair solta duas ondas de
                     choque rente ao chão (onda_vel, onda_ttl s) para os dois lados: pule as ondas.
  atirador           alterna rajada mirada e leque de espingarda (espalha_qtd balas em espalha_leque graus); com o pato muito
                     perto pula para trás; morrendo solta morte_tiros balas em anel.
  sapo               cura como antes; o cuspe vira bolha de bile em arco; língua: alinhado com o pato a menos de lingua_alcance
                     avisa (lingua_aviso s) e dá a língua, que machuca e puxa o pato para perto (lingua_puxao).
  cutulu             elite: o salto agora cai com um anel de anel_qtd bolhas; abaixo de furia_abaixo da vida ataca mais rápido.
  voador             bombardeiro: passa de um lado para o outro por cima do pato e solta bomba_qtd bombas que caem e explodem
                     (bomba_raio, bomba_dano) no chão ou no pato.
CÉU (os anjos ganham IA e entram nos grupos Inimigo e Personagem)
  querubim           arqueiro: fica a dist_min..dist_max e atira flechas rápidas mirando onde o pato VAI estar (flecha_lead);
                     ferido, atira voleio_qtd flechas e fica mais longe. Trocar de direção é o que desvia.
  serafim            padrões de luz: alterna espiral (espiral_bracos braços girando) e anéis de anel_qtd orbes com um buraco
                     (anel_buraco_meio) perto do pato: ache o buraco.
  ofanim             roda de olhos: fechada por fechado_tempo s, bala ricocheteia DE VOLTA no pato; aberta por aberto_tempo s
                     solta anéis de luz e leva dano. O soco sempre machuca.
  roda_anjo          roda: rola de um lado para o outro; alinhada com o pato gira no lugar (aviso_tempo s) e dispara a
                     investida_vel até a parede, onde quica para trás.

Projéteis novos: o mesmo objeto projetil_inimigo (então o Combate continua cuidando do dano e de sumir na parede) ganha
animações osso, espinho, bile, fogo, flecha, luz, olho, bomba e onda (imagens em assets/inimigos/projeteis) e as variáveis
tipo, gravidade, vy, gira e ttl. Inimigos com invulneravel = True não levam dano de bala, granada, explosão nem eletricidade
(a bala ricocheteia com som de ping); com reflete = True a bala volta como projétil inimigo no pato.

Migração de uso único. Variáveis: só ADICIONA as que faltam (valores atuais ficam). Os eventos externos "Inimigos" são
refeitos (é a tarefa), mas os blocos comuns (preparar, estados dos terrestres, paredes, separação, sorteio da árvore) são
copiados do jogo.json atual, com as edições que tiverem. Não roda duas vezes (procura a marca no comentário do topo).
"""
import copy, json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCA = 'Mecânicas dos inimigos (t78)'
PROJ_DIR = 'assets/inimigos/projeteis'
CENAS_INIMIGOS = ['Inferno', 'Purgatorio']
ANJOS = ['querubim', 'serafim', 'ofanim', 'roda_anjo']
VOADORES = ['voador', 'caveira_azul', 'cabeca_voadora', 'diabinho', 'moscas', 'olho_demoniaco', 'mina_demoniaca',
            'querubim', 'serafim', 'ofanim']
SONS = ['som_arremesso.wav', 'som_carga.wav', 'som_bate_parede.wav', 'som_bile.wav', 'som_espinhos.wav', 'som_espiral.wav',
        'som_ping.wav', 'som_investida.wav', 'som_roubo.wav', 'som_laser_carga.wav', 'som_laser.wav', 'som_bomba.wav',
        'som_arranca.wav', 'som_impacto.wav', 'som_lingua.wav', 'som_flecha.wav', 'som_luz.wav', 'som_olhos.wav',
        'som_roda.wav', 'som_levanta.wav']


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t78/' + '/'.join(p)))


# ---------------------------------------------------------------- variáveis novas (só entram se ainda não existem)
TODOS = {'invulneravel': False, 'reflete': False, 'reflete_vel': 650, 'reflete_dano': 12, 'firme': False,
         'morte_feita': False, 'preparado': False, 'golpe': '', 'vx': 0, 'vy': 0, 'dx': 0, 'dy': 0, 'ang': 0, 'rnd': 0, 'i': 0}
VOADOR_BASE = {'empurrao_x': 40, 'dano_duracao': 0.2, 'aggro_dist': 800, 'desiste_dist': 1100}
VARS = {
    'condenado': dict(cair_abaixo=30, caido_tempo=3, levanta_vida=60, levanta_max=1, levantadas=0, levanta_vel_fator=1.35,
                      levanta_cor='255;150;150'),
    'condenada': dict(dist_min=260, dist_max=480, arremesso_alcance=700, osso_qtd=3, osso_espalha=110, osso_tempo=0.85,
                      osso_gravidade=1500, osso_dano=10, osso_giro=720, atacar_tempo=0.4),
    'condenado_torto': dict(pulo_espera_min=0.2, pulo_espera_max=0.6, pulo_alt_min=380, pulo_alt_max=650, pulo_vx=280,
                            salto_chance=0.3, salto_dist=650, salto_dy=150, salto_alt=950, salto_vx=600, pulo_espera=0.4,
                            pulo_vel_atual=0, pulo_dir=1, pulando=False, salta=False),
    'condenado_azul': dict(carga_alcance=750, carga_alt=110, carga_aviso=0.45, carga_vel=950, carga_tempo_max=1.8,
                           carga_dano=25, carga_empurrao=1300, atordoa_tempo=1.6, parede_tempo=0.12, atordoa_balanco=6),
    'condenado_inchado': dict(acelera=1.5, bile_qtd=8, bile_vel=380, bile_dano=10, tremor=3),
    'arvore_condenada': dict(aggro_dist=750, ataque_espera=2.8, aviso_tempo=0.6, espinho_qtd=5, espinho_leque=50,
                             espinho_vel=520, espinho_dano=10, anel_cada=3, anel_qtd=12, anel_vel=300, ataques=0, tremor=4),
    'caveira_gigante': dict(espiral_espera=7, espiral_alcance=700, espiral_duracao=2.2, espiral_cadencia=0.09,
                            espiral_giro=17, espiral_bracos=3, espiral_vel=280, espiral_dano=12),
    'caveira_azul': dict(invulneravel=True, firme=True, quique_ganho=12, quique_max=420, area_raio=650),
    'cabeca_voadora': dict(distancia=320, altura=110, segue=2.5, investida_espera=2.4, investida_aviso=0.55,
                           investida_vel=1150, investida_tempo=0.5, tonto_tempo=0.9, tremor=4, investida_alcance=750),
    'diabinho': dict(orbita_raio=230, orbita_vel=2.2, segue=4, bote_espera=2.6, bote_aviso=0.35, bote_vel=700,
                     bote_tempo=0.6, roubo_max=6, roubadas=0, fuga_vel=430, fuga_tempo=5),
    'moscas': dict(acel=900, alerta_raio=600, v=0),
    'olho_demoniaco': dict(mira_tempo=1.1, trava_tempo=0.3, raio_tempo=0.4, raio_alcance=1500, raio_largura=22,
                           raio_dano=20, mira_giro=140, fim_x=0, fim_y=0, t=0, d=0, len2=0),
    'mina_demoniaca': dict(estilhaco_qtd=8, estilhaco_vel=420, estilhaco_dano=10, dano_inimigos=60),
    'zumbi': dict(frenesi_abaixo=0.5, frenesi_vel=260, frenesi_troca_min=0.35, frenesi_troca_max=0.9,
                  frenesi_pulo_chance=0.3, frenesi=False, frenesi_dir=1, frenesi_espera=0.5, frenesi_cor='255;110;110'),
    'pigman': dict(salto_alcance=600, salto_tempo=0.75, salto_altura=900, salto_vx=0, onda_vel=520, onda_dano=15,
                   onda_ttl=1.4, pulo_padrao=0, salto_tempo_max=2.5),
    'atirador': dict(espalha_qtd=5, espalha_leque=40, espalha_vel=650, espalha_dano=10, padrao=1, recua_pulo=700,
                     recua_espera=1.5, morte_tiros=6, morte_vel=420, morte_dano=10),
    'sapo': dict(lingua_alcance=420, lingua_alt=90, lingua_espera=3.2, lingua_aviso=0.35, lingua_duracao=0.35,
                 lingua_puxao=1100, lingua_dano=6, cuspe_tempo=0.8, cuspe_gravidade=1300, cuspe_dano=12),
    'cutulu': dict(anel_qtd=10, anel_vel=360, anel_dano=12, furia_abaixo=0.5, furia_fator=0.6, furia=False,
                   furia_cor='170;255;255'),
    'voador': dict(passada_dist=380, bomba_espera=2.2, bomba_qtd=3, bomba_intervalo=0.22, bomba_gravidade=1300,
                   bomba_raio=120, bomba_dano=15, bomba_alcance_x=200, bombas=0),
    'querubim': dict(dist_min=380, dist_max=600, flecha_vel=1050, flecha_dano=14, flecha_lead=1, ferido=False,
                     voleio_qtd=3, voleio_leque=14, flecha_alcance=950, ferido_dist=200, ferido_ritmo=0.7, segue=2),
    'serafim': dict(altura_sobre_pato=330, segue=1.2, padrao=1, espiral_bracos=4, espiral_giro=11, espiral_cadencia=0.1,
                    espiral_duracao=2.4, espiral_vel=240, anel_qtd=18, anel_vel=220, anel_buraco_meio=1, anel_desvio=70,
                    anel_intervalo=0.5, aneis=3, aneis_feitos=0, descanso=1.6, luz_dano=12, buraco_ang=0, luz_alcance=900),
    'ofanim': dict(invulneravel=True, reflete=True, fechado_tempo=3, aberto_tempo=2.2, aberto=False, anel_qtd=10,
                   anel_vel=300, anel_intervalo=0.7, anel_giro=18, luz_dano=12, segue=0.8, altura=200, giro_fechado=90,
                   giro_aberto=25, aviso_abrir=0.6),
    'roda_anjo': dict(rolagem_vel=260, perseguir_fator=1.3, investida_alcance=650, investida_alt=100, investida_vel=1100,
                      investida_tempo_max=2, quique_pulo=500, atordoa_tempo=0.8, patrulha_raio=300, travado_tempo=0.15,
                      giro_aviso=900),
}
for n in VOADORES:
    VARS.setdefault(n, {})


# ---------------------------------------------------------------- imagens dos projéteis
def desenha(nome):
    P = lambda *c: tuple(c) + (255,)
    if nome == 'osso':
        im = Image.new('RGBA', (12, 6)); px = im.load()
        for x in range(2, 10):
            px[x, 2] = P(232, 222, 196); px[x, 3] = P(196, 182, 150)
        for x, y in ((0, 1), (1, 1), (0, 4), (1, 4), (1, 2), (1, 3), (10, 1), (11, 1), (10, 4), (11, 4), (10, 2), (10, 3),
                     (0, 2), (0, 3), (11, 2), (11, 3)):
            px[x, y] = P(240, 232, 210) if y < 3 else P(200, 188, 158)
    elif nome == 'espinho':
        im = Image.new('RGBA', (12, 5)); px = im.load()
        for x in range(12):
            h = max(0, 2 - x // 5)
            for y in range(2 - h, 3 + h):
                px[x, y] = P(98, 64, 44) if y != 2 - h else P(150, 108, 76)
        px[11, 2] = P(220, 205, 170); px[10, 2] = P(190, 170, 130)
    elif nome in ('bile', 'luz', 'olho', 'bomba'):
        im = Image.new('RGBA', (9, 9)); px = im.load()
        cor = {'bile': (P(70, 140, 40), P(140, 210, 70), P(210, 255, 150)),
               'luz': (P(220, 160, 40), P(255, 220, 110), P(255, 255, 230)),
               'olho': (P(110, 60, 190), P(170, 130, 255), P(240, 230, 255)),
               'bomba': (P(30, 26, 34), P(62, 56, 70), P(130, 124, 140))}[nome]
        for y in range(9):
            for x in range(9):
                d = ((x - 4) ** 2 + (y - 4) ** 2) ** .5
                if d <= 4.2:
                    px[x, y] = cor[0] if d > 3.2 else cor[1]
        px[3, 3] = px[3, 2] = px[2, 3] = cor[2]
        if nome == 'olho':
            px[4, 4] = px[5, 4] = P(30, 10, 50)
        if nome == 'bomba':
            px[6, 1] = P(150, 110, 60); px[7, 0] = P(255, 200, 60); px[8, 0] = P(255, 120, 30)
        if nome == 'bile':
            px[6, 6] = P(50, 100, 30)
    elif nome == 'flecha':
        im = Image.new('RGBA', (16, 5)); px = im.load()
        for x in range(3, 13):
            px[x, 2] = P(236, 226, 200)
        for x, y in ((13, 1), (13, 2), (13, 3), (14, 2), (15, 2), (14, 1), (14, 3)):
            px[x, y] = P(255, 214, 90) if x < 15 else P(255, 245, 190)
        for x, y in ((0, 0), (1, 1), (2, 1), (0, 4), (1, 3), (2, 3), (1, 0), (1, 4), (3, 1), (3, 3)):
            px[x, y] = P(250, 250, 255)
    elif nome == 'onda':
        im = Image.new('RGBA', (14, 9)); px = im.load()
        for x in range(14):
            h = int(1 + 7 * (x / 13) ** 1.6)
            for y in range(9 - h, 9):
                px[x, y] = P(180, 150, 120) if y > 9 - h else P(230, 210, 170)
        for x, y in ((12, 0), (10, 1), (13, 2), (8, 3)):
            px[x, y] = P(150, 120, 90)
    return im.resize((im.width * 3, im.height * 3), Image.NEAREST)


TIPOS_DESENHADOS = ['osso', 'espinho', 'bile', 'flecha', 'luz', 'olho', 'bomba', 'onda']
FOGO = ['assets/demonio_chefe/bola_fogo_00.png', 'assets/demonio_chefe/bola_fogo_01.png',
        'assets/demonio_chefe/bola_fogo_02.png', 'assets/demonio_chefe/bola_fogo_03.png']


# ---------------------------------------------------------------- montagem de eventos
def I(t, *p, inv=False):
    d = {'type': {'value': t}, 'parameters': [str(x) for x in p]}
    if inv:
        d['type']['inverted'] = True
    return d


def E(c=(), a=(), s=()):
    return {'type': 'BuiltinCommonInstructions::Standard', 'conditions': list(c), 'actions': list(a), 'events': list(s)}


def FE(obj, c=(), a=(), s=()):
    return {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': list(c), 'actions': list(a),
            'events': list(s)}


def REP(expr, a=(), s=()):
    return {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': expr, 'conditions': [], 'actions': list(a),
            'events': list(s)}


def G(nome, evs, cor=(74, 176, 228)):
    return {'colorB': cor[2], 'colorG': cor[1], 'colorR': cor[0], 'creationTime': 0, 'name': nome, 'source': '',
            'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': list(evs)}


def COM(txt):
    return {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0,
                                                                     'textR': 0}, 'comment': txt}


def OR(*conds):
    d = I('BuiltinCommonInstructions::Or')
    d['subInstructions'] = list(conds)
    return d


# condições
def vivo(o): return I('BooleanObjectVariable', o, 'morto', 'False', '')
def morto(o): return I('BooleanObjectVariable', o, 'morto', 'True', '')
def b(o, v, val=True): return I('BooleanObjectVariable', o, v, 'True' if val else 'False', '')
def n(o, v, op, x): return I('NumberObjectVariable', o, v, op, x)
def est(o, s, op='='): return I('StringObjectVariable', o, 'estado', op, f'"{s}"')
def tm(o, t, op, x): return I('CompareObjectTimer', o, f'"{t}"', op, x)
def cmp(a, op, x): return I('BuiltinCommonInstructions::CompareNumbers', a, op, x)
def perto(o, alvo, d, inv=False): return I('Distance', o, alvo, d, '', inv=inv)
def col(a, c): return I('CollisionNP', a, c, '', '', '')
def no_chao(o, inv=False): return I('PlatformBehavior::IsOnFloor', o, 'PlatformerObject', inv=inv)
def anda_algo(o, inv=False): return I('PlatformBehavior::IsMoving', o, 'PlatformerObject', inv=inv)
def pato_livre(): return [b('pato', 'invencivel', False), b('pato', 'morto', False)]


# ações
def setn(o, v, op, x): return I('SetNumberObjectVariable', o, v, op, x)
def setb(o, v, val=True): return I('SetBooleanObjectVariable', o, v, 'True' if val else 'False', '')
def sets(o, v, s): return I('SetStringObjectVariable', o, v, '=', f'"{s}"')
def rst(o, t): return I('ResetObjectTimer', o, f'"{t}"')
def anim(o, a): return I('AnimatableCapability::AnimatableBehavior::SetName', o, 'Animation', '=', f'"{a}"')
def som(arq, vol=60, tom='RandomFloatInRange(0.95, 1.05)'): return I('PlaySound', '', arq, '', vol, tom)
def brilho(o, x): return I('EffectCapability::EffectBehavior::SetEffectDoubleParameter', o, 'Effect', '"Brilho"', '"brightness"', x)
def esq(o): return I('PlatformBehavior::SimulateLeftKey', o, 'PlatformerObject')
def dir_(o): return I('PlatformBehavior::SimulateRightKey', o, 'PlatformerObject')
def pula(o): return I('PlatformBehavior::SimulateJumpKey', o, 'PlatformerObject')
def maxv(o, x): return I('PlatformBehavior::MaxSpeed', o, 'PlatformerObject', '=', x)
def pulo_vel(o, x): return I('PlatformBehavior::JumpSpeed', o, 'PlatformerObject', '=', x)
def cor(o, c): return I('ChangeColor', o, f'"{c}"')
def cor_expr(o, x): return I('ChangeColor', o, x)


def estado(o, s):
    return [sets(o, 'estado', s), rst(o, 'estado')]


DT = 'TimeDelta()'
PULSO = '1.6 + 0.9 * sin(TimeFromStart() * 40)'


def ang_pato(o):
    return f'ToDeg(atan2(pato.CenterY() - {o}.CenterY(), pato.CenterX() - {o}.CenterX()))'


def dano_pato(o, dano, empurrao):
    """Ações: tira `dano` do pato, dá a invencibilidade e joga o pato para longe de o a `empurrao` px/s (negativo puxa)."""
    return [setn('pato', 'vida', '-', dano), setb('pato', 'invencivel'), rst('pato', 'iframes'),
            I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'"{o}"'),
            setn('pato', 'coice_vx', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001) * ({empurrao})')]


def tiro(o, tipo, ang, vel, dano, x=None, y=None, extra=()):
    """Ações que criam um projetil_inimigo do tipo (animação) no centro de o, na direção ang (graus) a vel px/s."""
    x = x or f'{o}.CenterX()'
    y = y or f'{o}.CenterY()'
    return [I('Create', '', 'projetil_inimigo', x, y, ''),
            anim('projetil_inimigo', tipo),
            I('SetXY', 'projetil_inimigo', '=', f'{x} - projetil_inimigo.Width() / 2', '=', f'{y} - projetil_inimigo.Height() / 2'),
            I('AddForceAL', 'projetil_inimigo', ang, vel, '1'),
            I('SetAngle', 'projetil_inimigo', '=', ang),
            setn('projetil_inimigo', 'dano', '=', dano),
            I('SetStringObjectVariable', 'projetil_inimigo', 'origem', '=', f'"{o}"'),
            sets('projetil_inimigo', 'tipo', tipo),
            rst('projetil_inimigo', 'vida')] + list(extra)


def anel(o, qtd, tipo, vel, dano, ang0='0', extra=()):
    """Repeat que solta qtd projéteis em anel (o.i conta)."""
    return [E(a=[setn(o, 'i', '=', '0')]),
            REP(qtd, tiro(o, tipo, f'{ang0} + {o}.i * 360 / max(1, {qtd})', vel, dano, extra=extra) + [setn(o, 'i', '+', '1')])]


def leque(o, qtd, abertura, tipo, vel, dano, centro=None, extra=()):
    centro = centro or ang_pato(o)
    a = f'{centro} + ({o}.i - ({qtd} - 1) / 2) * {abertura} / max(1, {qtd} - 1)'
    return [E(a=[setn(o, 'i', '=', '0')]), REP(qtd, tiro(o, tipo, a, vel, dano, extra=extra) + [setn(o, 'i', '+', '1')])]


def anda_ate(o, parar):
    return [E([cmp(f'abs(pato.CenterX() - {o}.CenterX())', '>', parar)], [], [
        E([cmp(f'pato.CenterX() - {o}.CenterX()', '<', '0')], [esq(o), setb(o, 'quer_andar')]),
        E([cmp(f'pato.CenterX() - {o}.CenterX()', '>', '0')], [dir_(o), setb(o, 'quer_andar')])])]


def mantem_dist(o, dmin, dmax):
    return anda_ate(o, dmax) + [E([cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', dmin)], [], [
        E([cmp(f'pato.CenterX() - {o}.CenterX()', '>', '0')], [esq(o), setb(o, 'quer_andar')]),
        E([cmp(f'pato.CenterX() - {o}.CenterX()', '<', '0')], [dir_(o), setb(o, 'quer_andar')])])]


def lado(o, campo='direcao'):
    return [E([n(o, campo, '<', '0')], [esq(o), setb(o, 'quer_andar')]), E([n(o, campo, '>', '0')], [dir_(o), setb(o, 'quer_andar')])]


def segue_ponto(o, x, y, k):
    """Voador vai suave até (x, y): a cada quadro anda min(1, k * dt) do caminho."""
    return [I('SetX', o, '+', f'(({x}) - {o}.CenterX()) * min(1, {k} * {DT})'),
            I('SetY', o, '+', f'(({y}) - {o}.CenterY()) * min(1, {k} * {DT})')]


# ---------------------------------------------------------------- grupos de eventos por inimigo
def g_projeteis():
    p = 'projetil_inimigo'
    return G('Projéteis dos inimigos', [
        COM('Tipos de projétil (animação): osso, espinho, bile, fogo, flecha, luz, olho, bomba, onda. gravidade (px/s²) faz '
            'cair em arco, gira (graus/s) roda o desenho, sem gira ele aponta para onde vai; ttl > 0 some depois de ttl s. A '
            'bomba explode no chão ou no pato (raio, dano_bomba). O dano normal e sumir na parede ficam no Combate.'),
        E([n(p, 'gravidade', '!=', '0')], [setn(p, 'vy', '+', f'{p}.gravidade * {DT}'), I('SetY', p, '+', f'{p}.vy * {DT}')]),
        E([n(p, 'gira', '!=', '0')], [I('SetAngle', p, '+', f'{p}.gira * {DT}')]),
        E([n(p, 'gira', '=', '0'), n(p, 'gravidade', '!=', '0')],
          [I('SetAngle', p, '=', f'ToDeg(atan2({p}.vy + {p}.ForceY(), {p}.ForceX()))')]),
        E([n(p, 'ttl', '>', '0'), tm(p, 'vida', '>', f'{p}.ttl')], [I('Delete', p, '')]),
        E([I('StringObjectVariable', p, 'tipo', '=', '"bomba"'), col(p, 'Terreno')], [setb(p, 'boom')]),
        E([I('StringObjectVariable', p, 'tipo', '=', '"bomba"'), col(p, 'pato')], [setb(p, 'boom')]),
        FE(p, [b(p, 'boom')], [
            I('Create', '', 'explosao_fumaca', f'{p}.CenterX()', f'{p}.CenterY()', ''),
            I('Create', '', 'explosao_fogo', f'{p}.CenterX()', f'{p}.CenterY()', ''),
            I('Create', '', 'explosao_faiscas', f'{p}.CenterX()', f'{p}.CenterY()', ''),
            som('som_explosao.wav', 60, 'RandomFloatInRange(1.1, 1.25)')], [
            E([perto(p, 'pato', f'{p}.raio')] + pato_livre(), dano_pato(p, f'{p}.dano_bomba', '700')),
            E(a=[I('Delete', p, '')])]),
    ])


def g_condenado():
    o = 'condenado'
    return G('Condenado (se levanta)', [
        COM('Anda até o pato e dá um bote curto. Abaixo de cair_abaixo de vida cai (estado "calmo": inofensivo e sem '
            'tranco) e, se ninguém acabar com ele em caido_tempo s, levanta com levanta_vida, mais rápido e avermelhado.'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [anim(o, 'andando')], anda_ate(o, f'{o}.parar_dist')),
            E([est(o, 'patrulha')], [anim(o, 'andando')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.ataque_alcance')],
              estado(o, 'preparar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX())'), anim(o, 'idle'),
                                       som('som_aviso_condenado.wav', 65)]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
              estado(o, 'atacar') + [maxv(o, f'{o}.velocidade * {o}.investida_fator'), anim(o, 'ataque')]),
            E([est(o, 'atacar')], [], lado(o)),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.investida_tempo')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([n(o, 'vida', '<=', f'{o}.cair_abaixo'), n(o, 'levantadas', '<', f'{o}.levanta_max'), est(o, 'calmo', '!=')],
              estado(o, 'calmo') + [setb(o, 'firme'), setn(o, 'levantadas', '+', '1'), anim(o, 'morte'),
                                    som('som_inimigo_morte.wav', 50, 'RandomFloatInRange(0.75, 0.85)')]),
            E([est(o, 'calmo'), tm(o, 'estado', '>', f'{o}.caido_tempo')],
              estado(o, 'perseguir') + [setb(o, 'firme', False), setn(o, 'vida', '=', f'max({o}.vida, {o}.levanta_vida)'),
                                        setn(o, 'vida_controle', '=', f'{o}.vida'),
                                        setn(o, 'velocidade', '*', f'{o}.levanta_vel_fator'), anim(o, 'idle'),
                                        cor_expr(o, f'{o}.levanta_cor'), rst(o, 'ataque'), som('som_levanta.wav', 70)]),
            E([est(o, 'calmo'), tm(o, 'estado', '>', f'{o}.caido_tempo - 0.5')],
              [I('SetX', o, '+', f'sin(TimeFromStart() * 70) * 60 * {DT}')]),
        ]),
    ])


def g_condenada():
    o = 'condenada'
    vx = f'(pato.CenterX() - {o}.CenterX() + ({o}.i - ({o}.osso_qtd - 1) / 2) * {o}.osso_espalha) / {o}.osso_tempo'
    vy = f'(pato.CenterY() - {o}.CenterY()) / {o}.osso_tempo - {o}.osso_gravidade * {o}.osso_tempo / 2'
    p = 'projetil_inimigo'
    return G('Condenada (joga ossos)', [
        COM('Fica entre dist_min e dist_max do pato e joga osso_qtd ossos em arco (osso_tempo s de voo) espalhados '
            'osso_espalha px em volta de onde o pato está.'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [anim(o, 'andando')], mantem_dist(o, f'{o}.dist_min', f'{o}.dist_max')),
            E([est(o, 'perseguir'), cmp(f'abs(pato.CenterX() - {o}.CenterX())', '>=', f'{o}.dist_min'),
               cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<=', f'{o}.dist_max')], [anim(o, 'idle')]),
            E([est(o, 'patrulha')], [anim(o, 'andando')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.arremesso_alcance')],
              estado(o, 'preparar') + [anim(o, 'idle'), som('som_aviso_condenado.wav', 60, '1.3')]),
        ]),
        FE(o, [vivo(o), est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
           estado(o, 'atacar') + [anim(o, 'ataque'), som('som_arremesso.wav', 65)], [
               E(a=[setn(o, 'i', '=', '0')]),
               REP(f'{o}.osso_qtd', tiro(o, 'osso', '0', '0', f'{o}.osso_dano', extra=[
                   I('AddForceXY', p, vx, '0', '1'), setn(p, 'vy', '=', vy), setn(p, 'gravidade', '=', f'{o}.osso_gravidade'),
                   setn(p, 'gira', '=', f'{o}.osso_giro'), setn(p, 'ttl', '=', '4')]) + [setn(o, 'i', '+', '1')])]),
        E([vivo(o), est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.atacar_tempo')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
    ])


def g_torto():
    o = 'condenado_torto'
    return G('Condenado torto (pulador)', [
        COM('Só anda pulando: pulinhos tortos (às vezes para longe do pato) e, com salto_chance ou o pato acima '
            'salto_dy px, um salto grande em cima dele.'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir'), no_chao(o), tm(o, 'pulo', '>', f'{o}.pulo_espera')], [
                setn(o, 'rnd', '=', 'RandomFloat(1)'), setb(o, 'salta', False)], [
                E([n(o, 'rnd', '<', f'{o}.salto_chance'), perto(o, 'pato', f'{o}.salto_dist')], [setb(o, 'salta')]),
                E([cmp('pato.CenterY()', '<', f'{o}.CenterY() - {o}.salto_dy'), perto(o, 'pato', f'{o}.salto_dist')],
                  [setb(o, 'salta')]),
                E([b(o, 'salta')], [pulo_vel(o, f'{o}.salto_alt'), setn(o, 'pulo_vel_atual', '=', f'{o}.salto_vx'),
                                    setn(o, 'pulo_dir', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)'),
                                    anim(o, 'ataque'), som('som_aviso_condenado.wav', 55, '1.5')]),
                E([b(o, 'salta', False)], [
                    pulo_vel(o, f'RandomFloatInRange({o}.pulo_alt_min, {o}.pulo_alt_max)'),
                    setn(o, 'pulo_vel_atual', '=', f'{o}.pulo_vx * RandomFloatInRange(0.5, 1.2)'),
                    setn(o, 'pulo_dir', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001) * sign(0.7 - RandomFloat(1))'),
                    anim(o, 'andando')]),
                E(a=[pula(o), setb(o, 'pulando'), rst(o, 'pulo'),
                     setn(o, 'pulo_espera', '=', f'RandomFloatInRange({o}.pulo_espera_min, {o}.pulo_espera_max)')]),
            ]),
            E([est(o, 'perseguir'), no_chao(o, inv=True)], [maxv(o, f'{o}.pulo_vel_atual')], lado(o, 'pulo_dir')),
            E([b(o, 'pulando'), no_chao(o), tm(o, 'pulo', '>', '0.1')], [setb(o, 'pulando', False), rst(o, 'pulo'), anim(o, 'idle')]),
            E([est(o, 'patrulha')], [anim(o, 'andando')]),
        ]),
    ])


def g_azul():
    o = 'condenado_azul'
    return G('Condenado azul (investida)', [
        COM('Alinhado com o pato ruge e corre em linha reta até bater numa parede (fica tonto e inofensivo por '
            'atordoa_tempo s). Encostar durante a corrida tira carga_dano e joga longe.'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [anim(o, 'andando')], anda_ate(o, f'{o}.parar_dist')),
            E([est(o, 'patrulha')], [anim(o, 'andando')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'),
               cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.carga_alcance'),
               cmp(f'abs(pato.CenterY() - {o}.CenterY())', '<', f'{o}.carga_alt')],
              estado(o, 'preparar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX())'), anim(o, 'idle'),
                                       som('som_carga.wav', 70)]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.carga_aviso')],
              estado(o, 'atacar') + [maxv(o, f'{o}.carga_vel'), anim(o, 'ataque'), rst(o, 'parede')]),
            E([est(o, 'atacar')], [], lado(o)),
            E([est(o, 'atacar'), col('pato', o)] + pato_livre(), dano_pato(o, f'{o}.carga_dano', f'{o}.carga_empurrao')),
            E([est(o, 'atacar'), anda_algo(o)], [rst(o, 'parede')]),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.carga_tempo_max')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([est(o, 'atacar'), tm(o, 'parede', '>', f'{o}.parede_tempo')],
              estado(o, 'calmo') + [setb(o, 'firme'), anim(o, 'idle'), som('som_bate_parede.wav', 75), cor(o, '170;170;255')]),
            E([est(o, 'calmo')], [I('SetAngle', o, '=', f'sin(TimeFromStart() * 25) * {o}.atordoa_balanco')]),
            E([est(o, 'calmo'), tm(o, 'estado', '>', f'{o}.atordoa_tempo')],
              estado(o, 'perseguir') + [setb(o, 'firme', False), I('SetAngle', o, '=', '0'), cor(o, '255;255;255'),
                                        rst(o, 'ataque')]),
        ]),
    ])


def g_inchado():
    o = 'condenado_inchado'
    return G('Condenado inchado (bolsa de bile)', [
        COM('Acelera quanto mais perto do pato (acelera); perto, pisca e explode (dano em explosao_raio). Morrer de '
            'qualquer jeito, inclusive a tiro, estoura bile_qtd bolhas em anel.'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [anim(o, 'andando'), maxv(o, f'{o}.velocidade * (1 + {o}.acelera * clamp(1 - '
                                      f'DistanceBetweenPositions(pato.CenterX(), pato.CenterY(), {o}.CenterX(), {o}.CenterY())'
                                      f' / {o}.aggro_dist, 0, 1))')], anda_ate(o, f'{o}.parar_dist')),
            E([est(o, 'patrulha')], [anim(o, 'andando')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.ataque_alcance')],
              estado(o, 'preparar') + [anim(o, 'idle'), som('som_aviso_inchado.wav', 65)]),
            E([est(o, 'preparar')], [I('SetX', o, '+', f'sin(TimeFromStart() * 80) * {o}.tremor')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
              estado(o, 'atacar') + [setn(o, 'vida', '=', '0'), som('som_explosao.wav', 70, 'RandomFloatInRange(0.75, 0.85)')], [
                  E([perto(o, 'pato', f'{o}.explosao_raio')] + pato_livre(),
                    dano_pato(o, f'{o}.dano', f'{o}.explosao_empurrao'))]),
        ]),
        FE(o, [morto(o), b(o, 'morte_feita', False)], [setb(o, 'morte_feita'), som('som_bile.wav', 70)],
           anel(o, f'{o}.bile_qtd', 'bile', f'{o}.bile_vel', f'{o}.bile_dano', ang0='RandomFloat(45)',
                extra=[setn('projetil_inimigo', 'ttl', '=', '3')])),
    ])


def g_arvore(eventos_sorteio):
    o = 'arvore_condenada'
    return G('Árvore condenada (espinheiro)', [
        COM('Parada; machuca no contato. Com o pato a menos de aggro_dist: treme por aviso_tempo s e atira um leque de '
            'espinho_qtd espinhos; a cada anel_cada ataques, um anel de anel_qtd espinhos lentos.'),
    ] + eventos_sorteio + [
        E([vivo(o), est(o, 'patrulha'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.aggro_dist')],
          estado(o, 'preparar') + [som('som_aviso_caveira.wav', 55, '1.4')]),
        E([vivo(o), est(o, 'preparar')], [I('SetX', o, '=', f'{o}.base_x + sin(TimeFromStart() * 60) * {o}.tremor'),
                                         brilho(o, PULSO)]),
        FE(o, [vivo(o), est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
           estado(o, 'patrulha') + [I('SetX', o, '=', f'{o}.base_x'), brilho(o, '1'), rst(o, 'ataque'),
                                   setn(o, 'ataques', '+', '1'), som('som_espinhos.wav', 65)], [
               E([cmp(f'mod({o}.ataques, max(1, {o}.anel_cada))', '=', '0')], [],
                 anel(o, f'{o}.anel_qtd', 'espinho', f'{o}.anel_vel', f'{o}.espinho_dano', ang0='RandomFloat(30)',
                      extra=[setn('projetil_inimigo', 'ttl', '=', '4')])),
               E([cmp(f'mod({o}.ataques, max(1, {o}.anel_cada))', '!=', '0')], [],
                 leque(o, f'{o}.espinho_qtd', f'{o}.espinho_leque', 'espinho', f'{o}.espinho_vel', f'{o}.espinho_dano',
                       extra=[setn('projetil_inimigo', 'ttl', '=', '3')]))]),
    ])


def g_caveira_gigante(antigos):
    o = 'caveira_gigante'
    return G('Caveira gigante', antigos + [
        COM('Espiral: de espiral_espera em espiral_espera s, com o pato a menos de espiral_alcance, para e gira uma espiral '
            'de bolas de fogo (espiral_bracos braços, espiral_giro graus por rajada) por espiral_duracao s.'),
        E([vivo(o), est(o, 'perseguir'), tm(o, 'espiral', '>', f'{o}.espiral_espera'), perto(o, 'pato', f'{o}.espiral_alcance')],
          estado(o, 'espiral') + [setb(o, 'firme'), anim(o, 'idle'), som('som_espiral.wav', 70), setn(o, 'ang', '=', 'RandomFloat(360)')]),
        E([vivo(o), est(o, 'espiral')], [brilho(o, '1.3 + 0.3 * sin(TimeFromStart() * 20)')]),
        FE(o, [vivo(o), est(o, 'espiral'), tm(o, 'tiro', '>', f'{o}.espiral_cadencia')],
           [rst(o, 'tiro'), setn(o, 'ang', '+', f'{o}.espiral_giro')],
           anel(o, f'{o}.espiral_bracos', 'fogo', f'{o}.espiral_vel', f'{o}.espiral_dano', ang0=f'{o}.ang',
                extra=[setn('projetil_inimigo', 'ttl', '=', '4')])),
        E([vivo(o), est(o, 'espiral'), tm(o, 'estado', '>', f'{o}.espiral_duracao')],
          estado(o, 'perseguir') + [setb(o, 'firme', False), brilho(o, '1'), rst(o, 'espiral'), rst(o, 'ataque')]),
    ])


def g_voadores():
    o = 'Voador'
    return G('Voadores (comum)', [
        COM('Todos os que voam: levar tiro fora de um ataque (e sem firme) dá dano por dano_duracao s e empurra; perseguem '
            'a menos de aggro_dist e desistem a mais de desiste_dist; piscam avisando (preparar) e olham para o pato.'),
        E([vivo(o)], [], [
            E([b(o, 'acertado')], [setb(o, 'acertado', False), I('SetX', o, '+', f'{o}.kb_dir * {o}.empurrao_x')], [
                E([est(o, 'preparar', '!='), est(o, 'atacar', '!='), b(o, 'firme', False)], estado(o, 'dano'))]),
            E([est(o, 'dano'), tm(o, 'estado', '>', f'{o}.dano_duracao')], estado(o, 'perseguir')),
            E([est(o, 'patrulha'), perto(o, 'pato', f'{o}.aggro_dist')], estado(o, 'perseguir')),
            E([est(o, 'perseguir'), perto(o, 'pato', f'{o}.desiste_dist', inv=True)],
              estado(o, 'patrulha') + [setn(o, 'base_x', '=', f'{o}.X()'), setn(o, 'base_y', '=', f'{o}.Y()')]),
            E([est(o, 'preparar')], [brilho(o, PULSO)]),
            E([est(o, 'preparar', '!=')], [brilho(o, '1')]),
            E([b(o, 'sprite_esquerda'), I('PosX', 'pato', '>', f'{o}.X()')], [I('FlippableCapability::FlippableBehavior::FlipX', o, 'Flippable', 'yes')]),
            E([b(o, 'sprite_esquerda'), I('PosX', 'pato', '<', f'{o}.X()')], [I('FlippableCapability::FlippableBehavior::FlipX', o, 'Flippable', 'no')]),
            E([b(o, 'sprite_esquerda', False), I('PosX', 'pato', '<', f'{o}.X()')], [I('FlippableCapability::FlippableBehavior::FlipX', o, 'Flippable', 'yes')]),
            E([b(o, 'sprite_esquerda', False), I('PosX', 'pato', '>', f'{o}.X()')], [I('FlippableCapability::FlippableBehavior::FlipX', o, 'Flippable', 'no')]),
        ]),
    ])


def onda(o, amp='onda_amp', vel='3'):
    return I('SetY', o, '+', f'({o}.base_y + sin(TimeFromStart() * {vel}) * {o}.{amp} - {o}.Y()) * min(1, {o}.onda_suave * {DT})')


def g_voador():
    o = 'voador'
    p = 'projetil_inimigo'
    return G('Voador (bombardeiro)', [
        COM('Passa de um lado para o outro altura_sobre_pato px acima do pato (vira passada_dist px depois dele) e, quando '
            'está a menos de bomba_alcance_x dele, solta bomba_qtd bombas a cada bomba_intervalo s.'),
        E([vivo(o)], [anim(o, 'voando'), onda(o)], [
            E([est(o, 'patrulha')], [I('SetX', o, '+', f'cos(TimeFromStart() * 1.2) * {o}.patrulha_vel * {DT}')]),
            E([OR(est(o, 'perseguir'), est(o, 'atacar'))], [setn(o, 'base_y', '=', f'pato.Y() - {o}.altura_sobre_pato'),
                                                           I('SetX', o, '+', f'{o}.direcao * {o}.velocidade * {DT}')]),
            E([I('PosX', o, '>', f'pato.CenterX() + {o}.passada_dist')], [setn(o, 'direcao', '=', '-1')]),
            E([I('PosX', o, '<', f'pato.CenterX() - {o}.passada_dist')], [setn(o, 'direcao', '=', '1')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.bomba_espera'),
               cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.bomba_alcance_x')],
              estado(o, 'atacar') + [setn(o, 'bombas', '=', '0'), rst(o, 'tiro')]),
        ]),
        FE(o, [vivo(o), est(o, 'atacar'), tm(o, 'tiro', '>', f'{o}.bomba_intervalo')],
           tiro(o, 'bomba', '90', '0', '0', y=f'{o}.Y() + {o}.Height()', extra=[
               setn(p, 'gravidade', '=', f'{o}.bomba_gravidade'), setn(p, 'vy', '=', '0'), setn(p, 'raio', '=', f'{o}.bomba_raio'),
               setn(p, 'dano_bomba', '=', f'{o}.bomba_dano'), setn(p, 'gira', '=', '200'), setn(p, 'ttl', '=', '6'),
               I('AddForceXY', p, f'{o}.direcao * {o}.velocidade * 0.5', '0', '1')]) +
           [rst(o, 'tiro'), setn(o, 'bombas', '+', '1'), som('som_bomba.wav', 45)]),
        E([vivo(o), est(o, 'atacar'), n(o, 'bombas', '>=', f'{o}.bomba_qtd')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
    ])


def g_caveira_azul():
    o = 'caveira_azul'
    return G('Caveira azul (quica e só morre no soco)', [
        COM('Quica pelo cenário em diagonal sem parar, ganha quique_ganho px/s a cada quique (até quique_max) e não sai de '
            'area_raio px de onde nasceu. invulneravel: bala ricocheteia, só o soco machuca.'),
        E([vivo(o)], [anim(o, 'voando')], [
            E([est(o, 'patrulha')], [onda(o)]),
            E([est(o, 'patrulha', '!='), n(o, 'vx', '=', '0')],
              [setn(o, 'vx', '=', f'{o}.velocidade * sign(pato.CenterX() - {o}.CenterX() + 0.001)'),
               setn(o, 'vy', '=', f'-{o}.velocidade * 0.8')]),
        ]),
        FE(o, [vivo(o), est(o, 'patrulha', '!=')], [I('SetX', o, '+', f'{o}.vx * {DT}')], [
            E([col(o, 'Terreno')], [I('SetX', o, '-', f'{o}.vx * {DT}'), setn(o, 'vx', '=', f'-{o}.vx'),
                                    setn(o, 'vx', '=', f'sign({o}.vx) * min({o}.quique_max, abs({o}.vx) + {o}.quique_ganho)'),
                                    som('som_bate_parede.wav', 25, 'RandomFloatInRange(1.6, 1.8)')]),
            E(a=[I('SetY', o, '+', f'{o}.vy * {DT}')]),
            E([col(o, 'Terreno')], [I('SetY', o, '-', f'{o}.vy * {DT}'), setn(o, 'vy', '=', f'-{o}.vy'),
                                    setn(o, 'vy', '=', f'sign({o}.vy) * min({o}.quique_max, abs({o}.vy) + {o}.quique_ganho)'),
                                    som('som_bate_parede.wav', 25, 'RandomFloatInRange(1.6, 1.8)')]),
            E([I('PosX', o, '>', f'{o}.base_x + {o}.area_raio')], [setn(o, 'vx', '=', f'-abs({o}.vx)')]),
            E([I('PosX', o, '<', f'{o}.base_x - {o}.area_raio')], [setn(o, 'vx', '=', f'abs({o}.vx)')]),
            E([I('PosY', o, '>', f'{o}.base_y + {o}.area_raio')], [setn(o, 'vy', '=', f'-abs({o}.vy)')]),
            E([I('PosY', o, '<', f'{o}.base_y - {o}.area_raio')], [setn(o, 'vy', '=', f'abs({o}.vy)')]),
        ]),
    ])


def g_cabeca():
    o = 'cabeca_voadora'
    return G('Cabeça voadora (investida mirada)', [
        COM('Paira a distancia px do pato, altura px acima; treme e mira por investida_aviso s e dispara em linha reta a '
            'investida_vel na direção travada por investida_tempo s. Batendo no terreno fica tonta por tonto_tempo s.'),
        E([vivo(o)], [anim(o, 'voando')], [
            E([est(o, 'patrulha')], [onda(o)]),
            E([est(o, 'perseguir')], segue_ponto(o, f'pato.CenterX() - sign(pato.CenterX() - {o}.CenterX() + 0.001) * {o}.distancia',
                                                f'pato.CenterY() - {o}.altura + sin(TimeFromStart() * 3) * 30', f'{o}.segue')),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.investida_espera'), perto(o, 'pato', f'{o}.investida_alcance')],
              estado(o, 'preparar') + [som('som_aviso_mergulhador.wav', 60)]),
            E([est(o, 'preparar')], [I('SetX', o, '+', f'RandomFloatInRange(-{o}.tremor, {o}.tremor)')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.investida_aviso')],
              estado(o, 'atacar') + [setn(o, 'ang', '=', ang_pato(o)), som('som_investida.wav', 65)]),
            E([est(o, 'atacar')], [I('SetX', o, '+', f'cos(ToRad({o}.ang)) * {o}.investida_vel * {DT}'),
                                   I('SetY', o, '+', f'sin(ToRad({o}.ang)) * {o}.investida_vel * {DT}')]),
            E([est(o, 'atacar'), col(o, 'Terreno')],
              [I('SetX', o, '-', f'cos(ToRad({o}.ang)) * {o}.investida_vel * {DT}'),
               I('SetY', o, '-', f'sin(ToRad({o}.ang)) * {o}.investida_vel * {DT}')] +
              estado(o, 'tonto') + [setb(o, 'firme'), som('som_bate_parede.wav', 60, '1.3')]),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.investida_tempo')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([est(o, 'tonto')], [I('SetAngle', o, '=', 'sin(TimeFromStart() * 30) * 20')]),
            E([est(o, 'tonto'), tm(o, 'estado', '>', f'{o}.tonto_tempo')],
              estado(o, 'perseguir') + [setb(o, 'firme', False), I('SetAngle', o, '=', '0'), rst(o, 'ataque'),
                                        setn(o, 'base_y', '=', f'{o}.Y()')]),
        ]),
    ])


def g_diabinho():
    o = 'diabinho'
    return G('Diabinho (ladrão)', [
        COM('Rói o osso até ver o pato; aí orbita em volta dele (orbita_raio) e dá botes. Encostar rouba até roubo_max '
            'moedas e ele foge rindo; se não for morto em fuga_tempo s, some com elas. Morto, solta as moedas roubadas.'),
        E([vivo(o)], [], [
            E([est(o, 'patrulha')], [anim(o, 'roendo_osso')]),
            E([est(o, 'perseguir')], [anim(o, 'voando'), setn(o, 'ang', '+', f'{o}.orbita_vel * {DT}')] +
              segue_ponto(o, f'pato.CenterX() + cos({o}.ang) * {o}.orbita_raio',
                          f'pato.CenterY() - 60 + sin({o}.ang) * {o}.orbita_raio * 0.6', f'{o}.segue')),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.bote_espera')],
              estado(o, 'preparar') + [anim(o, 'loop'), som('som_aviso_mergulhador.wav', 55, '1.5')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.bote_aviso')],
              estado(o, 'atacar') + [anim(o, 'voando'), setn(o, 'dx', '=', ang_pato(o))]),
            E([est(o, 'atacar')], [I('SetX', o, '+', f'cos(ToRad({o}.dx)) * {o}.bote_vel * {DT}'),
                                   I('SetY', o, '+', f'sin(ToRad({o}.dx)) * {o}.bote_vel * {DT}')]),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.bote_tempo')],
              estado(o, 'perseguir') + [rst(o, 'ataque'), setn(o, 'ang', '=', f'atan2({o}.CenterY() - pato.CenterY(), {o}.CenterX() - pato.CenterX())')]),
            E([est(o, 'fugir')], [anim(o, 'voando'),
                                  I('SetX', o, '+', f'sign({o}.CenterX() - pato.CenterX() + 0.001) * {o}.fuga_vel * {DT}'),
                                  I('SetY', o, '+', f'(pato.CenterY() - 300 - {o}.CenterY()) * min(1, 2 * {DT})')]),
            E([est(o, 'fugir'), tm(o, 'estado', '>', f'{o}.fuga_tempo - 1')],
              [I('OpacityCapability::OpacityBehavior::SetValue', o, 'Opacity', '=', f'255 * clamp({o}.fuga_tempo - {o}.ObjectTimerElapsedTime("estado"), 0, 1)')]),
            E([est(o, 'fugir'), tm(o, 'estado', '>', f'{o}.fuga_tempo')],
              [I('Create', '', 'explosao_fumaca', f'{o}.CenterX()', f'{o}.CenterY()', ''), I('Delete', o, '')]),
        ]),
        FE(o, [vivo(o), est(o, 'fugir', '!='), n(o, 'roubadas', '=', '0'), col(o, 'pato'), n('pato', 'moedas', '>', '0')], [
            setn(o, 'roubadas', '=', f'min(pato.moedas, {o}.roubo_max)'), setn('pato', 'moedas', '-', f'{o}.roubadas'),
            setn(o, 'qtd_moedas', '+', f'{o}.roubadas'), setb(o, 'firme'), som('som_roubo.wav', 75),
            I('Create', '', 'moeda_feedback', f'{o}.X()', f'{o}.Y()', ''),
            I('TextContainerCapability::TextContainerBehavior::SetValue', 'moeda_feedback', 'Text', '=', f'"-" + ToString({o}.roubadas)'),
            rst('moeda_feedback', 'ttl')] + estado(o, 'fugir')),
    ])


def g_moscas():
    """O alerta guarda o ponto da mosca acertada em variáveis de cena e acorda as outras perto dele."""
    o = 'moscas'
    return G('Moscas (enxame com inércia)', [
        COM('Aceleram até o pato (acel px/s²) até a velocidade, passam direto e fazem a curva, tremendo (tremor). Acertar '
            'uma acorda as outras a menos de alerta_raio.'),
        E([vivo(o)], [anim(o, 'voando')], [
            E([est(o, 'patrulha')], [I('SetY', o, '+', f'({o}.base_y + sin(TimeFromStart() * 6) * {o}.onda_amp - {o}.Y()) * min(1, {o}.onda_suave * {DT})')]),
            E([est(o, 'patrulha', '!=')], [
                setn(o, 'v', '=', f'max(1, DistanceBetweenPositions(pato.CenterX(), pato.CenterY(), {o}.CenterX(), {o}.CenterY()))'),
                setn(o, 'vx', '+', f'(pato.CenterX() - {o}.CenterX()) / {o}.v * {o}.acel * {DT}'),
                setn(o, 'vy', '+', f'(pato.CenterY() - {o}.CenterY()) / {o}.v * {o}.acel * {DT}'),
                setn(o, 'v', '=', f'sqrt({o}.vx * {o}.vx + {o}.vy * {o}.vy)'),
                setn(o, 'vx', '*', f'min(1, {o}.velocidade / max(1, {o}.v))'),
                setn(o, 'vy', '*', f'min(1, {o}.velocidade / max(1, {o}.v))'),
                I('SetX', o, '+', f'{o}.vx * {DT} + sin(TimeFromStart() * 13 + {o}.base_x) * {o}.tremor'),
                I('SetY', o, '+', f'{o}.vy * {DT} + cos(TimeFromStart() * 11 + {o}.base_x) * {o}.tremor')]),
        ]),
        E(a=[I('SetNumberVariable', 'moscas_alerta', '=', '0')]),
        FE(o, [vivo(o), est(o, 'dano'), tm(o, 'estado', '<', '0.05')],
           [I('SetNumberVariable', 'moscas_alerta', '=', '1'), I('SetNumberVariable', 'moscas_alerta_x', '=', f'{o}.CenterX()'),
            I('SetNumberVariable', 'moscas_alerta_y', '=', f'{o}.CenterY()')]),
        E([I('NumberVariable', 'moscas_alerta', '=', '1'), vivo(o), est(o, 'patrulha'),
           cmp(f'{o}.DistanceToPosition(moscas_alerta_x, moscas_alerta_y)', '<', f'{o}.alerta_raio')], estado(o, 'perseguir')),
    ])


def g_olho():
    o = 'olho_demoniaco'
    d = 'olho_raio'
    x1, y1 = f'{o}.CenterX()', f'{o}.CenterY()'
    return G('Olho demoníaco (raio)', [
        COM('Fica altura_sobre_pato acima do pato, a dist_min..dist_max dele. Mira com uma linha fina que segue o pato '
            'devagar (mira_giro graus/s) por mira_tempo s, trava por trava_tempo s (a linha pisca) e dispara um raio de '
            'raio_largura px por raio_tempo s, que para na primeira parede.'),
        E([I('SceneInstancesCount', '', d, '=', '0')], [I('Create', '', d, '0', '0', ''), I('ChangePlan', d, '=', '900')]),
        E([vivo(o)], [anim(o, 'idle')], [
            E([est(o, 'atacar', '!='), est(o, 'preparar', '!=')], [onda(o, vel='2')]),
            E([est(o, 'perseguir')], [setn(o, 'base_y', '=', f'pato.Y() - {o}.altura_sobre_pato')], [
                E([cmp(f'abs(pato.CenterX() - {o}.CenterX())', '>', f'{o}.dist_max')],
                  [I('SetX', o, '+', f'sign(pato.CenterX() - {o}.CenterX()) * {o}.velocidade * {DT}')]),
                E([cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.dist_min')],
                  [I('SetX', o, '-', f'sign(pato.CenterX() - {o}.CenterX()) * {o}.velocidade * {DT}')])]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.ataque_alcance')],
              estado(o, 'preparar') + [setn(o, 'ang', '=', ang_pato(o)), som('som_laser_carga.wav', 55)]),
            E([est(o, 'preparar'), tm(o, 'estado', '<', f'{o}.mira_tempo')],
              [setn(o, 'ang', '+', f'clamp(AngleDifference({ang_pato(o)}, {o}.ang), -{o}.mira_giro * {DT}, {o}.mira_giro * {DT})')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.mira_tempo + {o}.trava_tempo')],
              estado(o, 'atacar') + [som('som_laser.wav', 70)]),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.raio_tempo')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
        ]),
        FE(o, [vivo(o), OR(est(o, 'preparar'), est(o, 'atacar'))], [
            setn(o, 'fim_x', '=', f'{x1} + cos(ToRad({o}.ang)) * {o}.raio_alcance'),
            setn(o, 'fim_y', '=', f'{y1} + sin(ToRad({o}.ang)) * {o}.raio_alcance')], [
            E([I('RaycastToPosition', 'Terreno', x1, y1, f'{o}.fim_x', f'{o}.fim_y', 'olho_rx', 'olho_ry', '')],
              [setn(o, 'fim_x', '=', 'olho_rx'), setn(o, 'fim_y', '=', 'olho_ry')]),
            E([est(o, 'preparar'), tm(o, 'estado', '<', f'{o}.mira_tempo')],
              [I('PrimitiveDrawing::OutlineColor', d, '"255;60;40"'),
               I('PrimitiveDrawing::OutlineOpacity', d, '=', '140 + 80 * sin(TimeFromStart() * 30)'),
               I('PrimitiveDrawing::LineV2', d, x1, y1, f'{o}.fim_x', f'{o}.fim_y', '2')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>=', f'{o}.mira_tempo')],
              [I('PrimitiveDrawing::OutlineColor', d, '"255;255;255"'),
               I('PrimitiveDrawing::OutlineOpacity', d, '=', '255 * (0.6 + 0.4 * sign(sin(TimeFromStart() * 60)))'),
               I('PrimitiveDrawing::LineV2', d, x1, y1, f'{o}.fim_x', f'{o}.fim_y', '3')]),
            E([est(o, 'atacar')], [
                I('PrimitiveDrawing::OutlineColor', d, '"255;120;60"'), I('PrimitiveDrawing::OutlineOpacity', d, '=', '255'),
                I('PrimitiveDrawing::LineV2', d, x1, y1, f'{o}.fim_x', f'{o}.fim_y', f'{o}.raio_largura'),
                I('PrimitiveDrawing::OutlineColor', d, '"255;240;200"'),
                I('PrimitiveDrawing::LineV2', d, x1, y1, f'{o}.fim_x', f'{o}.fim_y', f'{o}.raio_largura * 0.4'),
                setn(o, 'len2', '=', f'pow({o}.fim_x - {x1}, 2) + pow({o}.fim_y - {y1}, 2)'),
                setn(o, 't', '=', f'clamp(((pato.CenterX() - {x1}) * ({o}.fim_x - {x1}) + (pato.CenterY() - {y1}) * ({o}.fim_y - {y1})) / max(1, {o}.len2), 0, 1)'),
                setn(o, 'd', '=', f'DistanceBetweenPositions(pato.CenterX(), pato.CenterY(), {x1} + {o}.t * ({o}.fim_x - {x1}), {y1} + {o}.t * ({o}.fim_y - {y1}))')], [
                E([n(o, 'd', '<', f'{o}.raio_largura / 2 + pato.Width() / 3')] + pato_livre(),
                  dano_pato(o, f'{o}.raio_dano', '500'))]),
        ]),
    ])


def g_mina(antigos_movimento):
    o = 'mina_demoniaca'
    return G('Mina demoníaca (explode ao morrer)', [
        COM('Flutua parada; com o pato a menos de perseguir_dist vai devagar até ele e, a menos de explodir_dist, pisca e '
            'explode. Morrer de qualquer jeito (tiro, explosão de outra mina) também explode: dano no pato a menos de '
            'explosao_raio, estilhaco_qtd estilhaços e dano_inimigos nos inimigos perto, então minas explodem em cadeia.'),
    ] + antigos_movimento + [
        E([vivo(o), est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')], estado(o, 'atacar') + [setn(o, 'vida', '=', '0')]),
        FE(o, [morto(o), b(o, 'morte_feita', False)], [
            setb(o, 'morte_feita'), som('som_explosao.wav', 75, 'RandomFloatInRange(0.75, 0.85)'),
            I('Create', '', 'explosao_fumaca', f'{o}.CenterX()', f'{o}.CenterY()', ''),
            I('Create', '', 'explosao_faiscas', f'{o}.CenterX()', f'{o}.CenterY()', ''),
            I('Create', '', 'explosao_fogo', f'{o}.CenterX()', f'{o}.CenterY()', ''),
            setn('explosao_fogo', 'dano', '=', f'{o}.dano_inimigos'), setn('explosao_fogo', 'raio', '=', f'{o}.explosao_raio'),
            setn('explosao_fogo', 'repulsao', '=', '400')], [
            E([perto(o, 'pato', f'{o}.explosao_raio')] + pato_livre(), dano_pato(o, f'{o}.dano', f'{o}.explosao_empurrao')),
        ] + anel(o, f'{o}.estilhaco_qtd', 'fogo', f'{o}.estilhaco_vel', f'{o}.estilhaco_dano', ang0='RandomFloat(45)',
                 extra=[setn('projetil_inimigo', 'ttl', '=', '1.2')])),
    ])


def g_zumbi():
    o = 'zumbi'
    return G('Zumbi (sem cabeça)', [
        COM('Tanque lento que anda até o pato. Abaixo de frenesi_abaixo da vida perde a cabeça: firme (sem tranco), corre '
            'a frenesi_vel trocando de direção a cada frenesi_troca_min..max s (mais vezes para o pato) e pula à toa.'),
        E([vivo(o), est(o, 'perseguir'), b(o, 'frenesi', False)], [], anda_ate(o, f'{o}.parar_dist')),
        E([vivo(o), b(o, 'frenesi', False), cmp(f'{o}.vida', '<', f'{o}.max_vida * {o}.frenesi_abaixo')],
          [setb(o, 'frenesi'), setb(o, 'firme'), cor_expr(o, f'{o}.frenesi_cor'), som('som_arranca.wav', 75)] +
          estado(o, 'perseguir') + [I('Create', '', 'sangue_verde', f'{o}.CenterX()', f'{o}.Y()', ''),
                                    I('SetAngle', 'sangue_verde', '=', '-90')]),
        E([vivo(o), b(o, 'frenesi')], [maxv(o, f'{o}.frenesi_vel'), sets(o, 'estado', 'perseguir')], lado(o, 'frenesi_dir') + [
            E([tm(o, 'frenesi', '>', f'{o}.frenesi_espera')], [
                rst(o, 'frenesi'), setn(o, 'frenesi_espera', '=', f'RandomFloatInRange({o}.frenesi_troca_min, {o}.frenesi_troca_max)'),
                setn(o, 'frenesi_dir', '=', 'sign(RandomFloatInRange(-1, 1) + 0.001)')], [
                E([cmp('RandomFloat(1)', '<', '0.65')], [setn(o, 'frenesi_dir', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)')]),
                E([no_chao(o), cmp('RandomFloat(1)', '<', f'{o}.frenesi_pulo_chance')], [pula(o)])]),
        ]),
    ])


def g_pigman():
    o = 'pigman'
    return G('Pigman (pancada)', [
        COM('Anda até o pato; a menos de salto_alcance avisa e salta em cima dele (salto_tempo s de voo, impulso '
            'salto_altura). Ao cair solta duas ondas de choque rente ao chão, uma para cada lado (onda_vel, onda_ttl s).'),
        E([I('DepartScene', '')], [setn(o, 'pulo_padrao', '=', f'{o}.PlatformerObject::JumpSpeed()')]),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [anim(o, 'caminhando')], anda_ate(o, f'{o}.parar_dist')),
            E([est(o, 'patrulha')], [anim(o, 'caminhando')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.salto_alcance')],
              estado(o, 'preparar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)'),
                                       anim(o, 'ataque_1'), som('som_aviso_pigman.wav', 65)]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
              estado(o, 'atacar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)'),
                                     setn(o, 'salto_vx', '=', f'clamp(abs(pato.CenterX() - {o}.CenterX()) / {o}.salto_tempo, 60, 900)'),
                                     pulo_vel(o, f'{o}.salto_altura'), pula(o), anim(o, 'ataque_2')]),
            E([est(o, 'atacar')], [maxv(o, f'{o}.salto_vx')], lado(o)),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.salto_tempo_max')],
              estado(o, 'perseguir') + [rst(o, 'ataque'), pulo_vel(o, f'{o}.pulo_padrao')]),
        ]),
        FE(o, [vivo(o), est(o, 'atacar'), tm(o, 'estado', '>', '0.15'), no_chao(o)],
           estado(o, 'perseguir') + [rst(o, 'ataque'), pulo_vel(o, f'{o}.pulo_padrao'), som('som_impacto.wav', 80),
                                     I('Create', '', 'poeira', f'{o}.CenterX()', f'{o}.Y() + {o}.Height()', '')],
           [E(a=tiro(o, 'onda', '0', f'{o}.onda_vel', f'{o}.onda_dano', x=f'{o}.CenterX() + 20',
                     y=f'{o}.Y() + {o}.Height() - 16', extra=[setn('projetil_inimigo', 'ttl', '=', f'{o}.onda_ttl')])),
            E(a=tiro(o, 'onda', '180', f'{o}.onda_vel', f'{o}.onda_dano', x=f'{o}.CenterX() - 20',
                     y=f'{o}.Y() + {o}.Height() - 16', extra=[setn('projetil_inimigo', 'ttl', '=', f'{o}.onda_ttl'),
                                                             I('SetAngle', 'projetil_inimigo', '=', '0'),
                                                             I('FlippableCapability::FlippableBehavior::FlipX', 'projetil_inimigo', 'Flippable', 'yes')]))]),
    ])


def g_atirador():
    o = 'atirador'
    return G('Atirador', [
        COM('Fica a dist_min..dist_max do pato e alterna: rajada de `rajada` tiros mirados e leque de espingarda '
            '(espalha_qtd balas em espalha_leque graus). Com o pato a menos da metade de dist_min pula para trás. Morrendo '
            'solta morte_tiros balas em anel.'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [], mantem_dist(o, f'{o}.dist_min', f'{o}.dist_max')),
            E([est(o, 'perseguir'), cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.dist_min / 2'), no_chao(o),
               tm(o, 'recuo', '>', f'{o}.recua_espera')], [rst(o, 'recuo'), pulo_vel(o, f'{o}.recua_pulo'), pula(o)]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.ataque_alcance')],
              estado(o, 'preparar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX())'),
                                       setn(o, 'padrao', '=', f'3 - {o}.padrao'),
                                       som('som_aviso_atirador.wav', 65)]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo'), n(o, 'padrao', '=', '1')],
              estado(o, 'atacar') + [setn(o, 'tiros', '=', '0')]),
            E([est(o, 'atacar')], [I('FireBullet::FireBullet::FireTowardObject', o, 'FireBullet', f'{o}.CenterX()', f'{o}.CenterY()',
                                     'projetil_inimigo', 'pato', f'{o}.tiro_vel', '')]),
            E([est(o, 'atacar'), I('FireBullet::FireBullet::HasJustFired', o, 'FireBullet', '')], [setn(o, 'tiros', '+', '1')]),
            E([est(o, 'atacar'), n(o, 'tiros', '>=', f'{o}.rajada')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
        ]),
        FE(o, [vivo(o), est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo'), n(o, 'padrao', '=', '2')],
           estado(o, 'perseguir') + [rst(o, 'ataque'), som('som_tiro_inimigo.wav', 70, '0.7')],
           leque(o, f'{o}.espalha_qtd', f'{o}.espalha_leque', '', f'{o}.espalha_vel', f'{o}.espalha_dano',
                 extra=[setn('projetil_inimigo', 'ttl', '=', '3')])),
        E([I('FireBullet::FireBullet::HasJustFired', o, 'FireBullet', '')], [som('som_tiro_inimigo.wav', 55, 'RandomFloatInRange(0.93, 1.07)')]),
        FE(o, [morto(o), b(o, 'morte_feita', False)], [setb(o, 'morte_feita'), som('som_tiro_inimigo.wav', 70, '0.6')],
           anel(o, f'{o}.morte_tiros', '', f'{o}.morte_vel', f'{o}.morte_dano', ang0='RandomFloat(60)',
                extra=[setn('projetil_inimigo', 'ttl', '=', '3')])),
    ])


def g_sapo(cura_eventos):
    o = 'sapo'
    p = 'projetil_inimigo'
    vx = f'(pato.CenterX() - {o}.CenterX()) / {o}.cuspe_tempo'
    vy = f'(pato.CenterY() - {o}.CenterY()) / {o}.cuspe_tempo - {o}.cuspe_gravidade * {o}.cuspe_tempo / 2'
    return G('Sapo (cura, cuspe em arco e língua)', [
        COM('Fica a dist_min..dist_max e cospe uma bolha de bile em arco (cuspe_tempo s de voo). A cada cura_intervalo s cura '
            'os inimigos perto. Alinhado com o pato a menos de lingua_alcance (|dy| < lingua_alt) avisa por lingua_aviso s e '
            'dá a língua: machuca e puxa o pato para perto (lingua_puxao).'),
        E([vivo(o)], [], [
            E([est(o, 'perseguir')], [anim(o, 'andando')], mantem_dist(o, f'{o}.dist_min', f'{o}.dist_max')),
            E([est(o, 'patrulha')], [anim(o, 'andando')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.ataque_alcance')],
              estado(o, 'preparar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX())'),
                                       som('som_aviso_sapo.wav', 65), anim(o, 'spit')]),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.atacar_tempo')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([est(o, 'perseguir'), tm(o, 'lingua', '>', f'{o}.lingua_espera'),
               cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.lingua_alcance'),
               cmp(f'abs(pato.CenterY() - {o}.CenterY())', '<', f'{o}.lingua_alt')],
              estado(o, 'lingua_aviso') + [setb(o, 'firme'), anim(o, 'idle'), som('som_aviso_sapo.wav', 60, '1.4'),
                                           setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)')]),
            E([est(o, 'lingua_aviso')], [brilho(o, PULSO)]),
            E([est(o, 'lingua_aviso'), tm(o, 'estado', '>', f'{o}.lingua_aviso')],
              estado(o, 'lingua') + [brilho(o, '1'), anim(o, 'lingua'), som('som_lingua.wav', 75)], [
                  E([cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.lingua_alcance'),
                     cmp(f'abs(pato.CenterY() - {o}.CenterY())', '<', f'{o}.lingua_alt'),
                     cmp(f'sign(pato.CenterX() - {o}.CenterX() + 0.001)', '=', f'{o}.direcao')] + pato_livre(),
                    dano_pato(o, f'{o}.lingua_dano', f'-{o}.lingua_puxao'))]),
            E([est(o, 'lingua'), tm(o, 'estado', '>', f'{o}.lingua_duracao')],
              estado(o, 'perseguir') + [setb(o, 'firme', False), rst(o, 'lingua')]),
        ]),
        FE(o, [vivo(o), est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
           estado(o, 'atacar') + tiro(o, 'bile', '0', '0', f'{o}.cuspe_dano', extra=[
               I('AddForceXY', p, vx, '0', '1'), setn(p, 'vy', '=', vy), setn(p, 'gravidade', '=', f'{o}.cuspe_gravidade'),
               setn(p, 'ttl', '=', '4')]) + [som('som_cuspe.wav', 55, 'RandomFloatInRange(0.93, 1.07)')]),
    ] + cura_eventos)


def g_cutulu(antigos):
    o = 'cutulu'
    return G('Cutulu (elite)', [
        COM('Alterna investida e salto por cima do pato; o salto cai com um anel de anel_qtd bolhas. Abaixo de furia_abaixo '
            'da vida entra em fúria: espera entre ataques * furia_fator e cor furia_cor.'),
        FE(o, [vivo(o), est(o, 'atacar'), n(o, 'escolha', '=', '2'), tm(o, 'estado', '>', f'{o}.voo_tempo_min'), no_chao(o)],
           [som('som_impacto.wav', 70, '1.2')],
           anel(o, f'{o}.anel_qtd', 'bile', f'{o}.anel_vel', f'{o}.anel_dano', ang0='RandomFloat(36)',
                extra=[setn('projetil_inimigo', 'ttl', '=', '3')])),
        E([vivo(o), b(o, 'furia', False), cmp(f'{o}.vida', '<', f'{o}.max_vida * {o}.furia_abaixo')],
          [setb(o, 'furia'), setn(o, 'ataque_espera', '*', f'{o}.furia_fator'), cor_expr(o, f'{o}.furia_cor'),
           som('som_aviso_cutulu.wav', 80, '0.8')]),
    ] + antigos)


def g_querubim():
    o = 'querubim'
    alvo_x = f'pato.CenterX() + pato.PlatformerObject::CurrentSpeed() * DistanceBetweenPositions(pato.CenterX(), pato.CenterY(), {o}.CenterX(), {o}.CenterY()) / {o}.flecha_vel * {o}.flecha_lead'
    mira = f'ToDeg(atan2(pato.CenterY() - {o}.CenterY(), {alvo_x} - {o}.CenterX()))'
    return G('Querubim (arqueiro)', [
        COM('Fica a dist_min..dist_max do pato e altura_sobre_pato acima, e atira flechas rápidas mirando onde o pato VAI '
            'estar (flecha_lead = 1 é a previsão inteira). Abaixo de ferido_abaixo da vida atira voleio_qtd flechas, fica '
            'ferido_dist mais longe e atira mais rápido (ferido_ritmo).'),
        E([vivo(o)], [], [
            E([b(o, 'ferido', False)], [anim(o, 'voando')]),
            E([b(o, 'ferido')], [anim(o, 'voando_ferido')]),
            E([est(o, 'patrulha')], [onda(o)]),
            E([est(o, 'perseguir')],
              segue_ponto(o, f'pato.CenterX() - sign(pato.CenterX() - {o}.CenterX() + 0.001) * ({o}.dist_min + {o}.dist_max) / 2 + sin(TimeFromStart() * 2.3 + {o}.base_x) * 120',
                          f'pato.CenterY() - {o}.altura_sobre_pato + cos(TimeFromStart() * 1.7) * 50', f'{o}.segue')),
            E([b(o, 'ferido', False), cmp(f'{o}.vida', '<', f'{o}.max_vida * {o}.ferido_abaixo')],
              [setb(o, 'ferido'), setn(o, 'dist_min', '+', f'{o}.ferido_dist'), setn(o, 'dist_max', '+', f'{o}.ferido_dist'),
               setn(o, 'ataque_espera', '*', f'{o}.ferido_ritmo')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'), perto(o, 'pato', f'{o}.flecha_alcance')],
              estado(o, 'preparar')),
        ]),
        FE(o, [vivo(o), est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
           estado(o, 'perseguir') + [rst(o, 'ataque'), som('som_flecha.wav', 70)], [
               E([b(o, 'ferido', False)], tiro(o, 'flecha', mira, f'{o}.flecha_vel', f'{o}.flecha_dano',
                                              extra=[setn('projetil_inimigo', 'ttl', '=', '3')])),
               E([b(o, 'ferido')], [], leque(o, f'{o}.voleio_qtd', f'{o}.voleio_leque', 'flecha', f'{o}.flecha_vel',
                                              f'{o}.flecha_dano', centro=mira, extra=[setn('projetil_inimigo', 'ttl', '=', '3')]))]),
    ])


def g_serafim():
    o = 'serafim'
    return G('Serafim (padrões de luz)', [
        COM('Paira altura_sobre_pato acima do pato. Descansa descanso s, avisa (aviso_tempo) e alterna: espiral '
            '(espiral_bracos braços girando espiral_giro graus a cada espiral_cadencia s, por espiral_duracao s) e `aneis` '
            'anéis de anel_qtd orbes com um buraco de 2*anel_buraco_meio+1 orbes perto da direção do pato (± anel_desvio). Só ataca com o pato a menos de luz_alcance.'),
        E([vivo(o)], [], [
            E([est(o, 'atacar', '!=')], [anim(o, 'voando')]),
            E([est(o, 'patrulha')], [onda(o)]),
            E([est(o, 'patrulha', '!=')], segue_ponto(o, 'pato.CenterX() + sin(TimeFromStart() * 0.7) * 160',
                                                     f'pato.CenterY() - {o}.altura_sobre_pato', f'{o}.segue')),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.descanso'), perto(o, 'pato', f'{o}.luz_alcance')],
              estado(o, 'preparar') + [setn(o, 'padrao', '=', f'3 - {o}.padrao'), som('som_luz.wav', 50, '0.8')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
              estado(o, 'atacar') + [anim(o, 'ataque_1'), setn(o, 'aneis_feitos', '=', '0'), rst(o, 'tiro'),
                                     setn(o, 'ang', '=', 'RandomFloat(360)')]),
            E([est(o, 'atacar'), n(o, 'padrao', '=', '1'), tm(o, 'estado', '>', f'{o}.espiral_duracao')],
              estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([est(o, 'atacar'), n(o, 'padrao', '=', '2'), n(o, 'aneis_feitos', '>=', f'{o}.aneis')],
              estado(o, 'perseguir') + [rst(o, 'ataque')]),
        ]),
        FE(o, [vivo(o), est(o, 'atacar'), n(o, 'padrao', '=', '1'), tm(o, 'tiro', '>', f'{o}.espiral_cadencia')],
           [rst(o, 'tiro'), setn(o, 'ang', '+', f'{o}.espiral_giro')],
           anel(o, f'{o}.espiral_bracos', 'luz', f'{o}.espiral_vel', f'{o}.luz_dano', ang0=f'{o}.ang',
                extra=[setn('projetil_inimigo', 'ttl', '=', '5')])),
        FE(o, [vivo(o), est(o, 'atacar'), n(o, 'padrao', '=', '2'), tm(o, 'tiro', '>', f'{o}.anel_intervalo'),
               n(o, 'aneis_feitos', '<', f'{o}.aneis')],
           [rst(o, 'tiro'), setn(o, 'aneis_feitos', '+', '1'), som('som_luz.wav', 45, 'RandomFloatInRange(1, 1.2)'),
            setn(o, 'buraco_ang', '=', f'{ang_pato(o)} + RandomFloatInRange(-{o}.anel_desvio, {o}.anel_desvio)'),
            setn(o, 'i', '=', f'{o}.anel_buraco_meio + 1')],
           [REP(f'{o}.anel_qtd - 2 * {o}.anel_buraco_meio - 1',
                tiro(o, 'luz', f'{o}.buraco_ang + {o}.i * 360 / {o}.anel_qtd', f'{o}.anel_vel', f'{o}.luz_dano',
                     extra=[setn('projetil_inimigo', 'ttl', '=', '6')]) + [setn(o, 'i', '+', '1')])]),
    ])


def g_ofanim():
    o = 'ofanim'
    return G('Ofanim (roda de olhos)', [
        COM('Vai devagar até acima do pato (segue, altura). Fechado por fechado_tempo s: gira e bala ricocheteia de volta no '
            'pato (invulneravel e reflete). Pisca aviso_abrir s antes de abrir. Aberto por aberto_tempo s: leva dano e solta '
            'um anel de anel_qtd olhos de luz a cada anel_intervalo s. O soco sempre machuca.'),
        E([vivo(o)], [], [
            E([est(o, 'patrulha')], [onda(o)]),
            E([est(o, 'patrulha', '!=')], segue_ponto(o, 'pato.CenterX()', f'pato.CenterY() - {o}.altura', f'{o}.segue')),
            E([b(o, 'aberto', False)], [anim(o, 'idle'), I('SetAngle', o, '+', f'{o}.giro_fechado * {DT}')]),
            E([b(o, 'aberto')], [I('SetAngle', o, '+', f'{o}.giro_aberto * {DT}')]),
            E([b(o, 'aberto', False), est(o, 'patrulha', '!='), tm(o, 'ciclo', '>', f'{o}.fechado_tempo - {o}.aviso_abrir')],
              [brilho(o, PULSO)]),
            E([b(o, 'aberto', False), est(o, 'patrulha', '!='), tm(o, 'ciclo', '>', f'{o}.fechado_tempo')],
              [setb(o, 'aberto'), setb(o, 'invulneravel', False), setb(o, 'reflete', False), anim(o, 'ataque'),
               brilho(o, '1'), som('som_olhos.wav', 70), rst(o, 'ciclo'), rst(o, 'tiro')]),
            E([b(o, 'aberto'), tm(o, 'ciclo', '>', f'{o}.aberto_tempo')],
              [setb(o, 'aberto', False), setb(o, 'invulneravel'), setb(o, 'reflete'), rst(o, 'ciclo')]),
        ]),
        FE(o, [vivo(o), b(o, 'aberto'), tm(o, 'tiro', '>', f'{o}.anel_intervalo')],
           [rst(o, 'tiro'), setn(o, 'ang', '+', f'{o}.anel_giro'), som('som_luz.wav', 45, '0.9')],
           anel(o, f'{o}.anel_qtd', 'olho', f'{o}.anel_vel', f'{o}.luz_dano', ang0=f'{o}.ang',
                extra=[setn('projetil_inimigo', 'ttl', '=', '5')])),
    ])


def g_roda():
    o = 'roda_anjo'
    return G('Roda do anjo', [
        COM('Rola de um lado para o outro (rolagem_vel, patrulha_raio); vendo o pato rola até ele (perseguir_fator). '
            'Alinhada com ele (|dx| < investida_alcance, |dy| < investida_alt) gira no lugar por aviso_tempo s e dispara a '
            'investida_vel até bater na parede, onde quica para trás (quique_pulo) e fica atordoa_tempo s sem atacar.'),
        E([b(o, 'acertado')], [setb(o, 'acertado', False)]),
        E([vivo(o)], [anim(o, 'rolando'), I('AnimatableCapability::AnimatableBehavior::SetSpeedScale', o, 'Animation', '=',
                                           f'clamp(abs({o}.PlatformerObject::CurrentSpeed()) / {o}.rolagem_vel, 0.2, 4)')], [
            E([est(o, 'patrulha')], [maxv(o, f'{o}.rolagem_vel')], lado(o) + [
                E([I('PosX', o, '>', f'{o}.base_x + {o}.patrulha_raio')], [setn(o, 'direcao', '=', '-1')]),
                E([I('PosX', o, '<', f'{o}.base_x - {o}.patrulha_raio')], [setn(o, 'direcao', '=', '1')]),
                E([perto(o, 'pato', f'{o}.aggro_dist')], estado(o, 'perseguir'))]),
            E([est(o, 'perseguir')], [maxv(o, f'{o}.rolagem_vel * {o}.perseguir_fator'),
                                      setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)')], lado(o)),
            E([est(o, 'perseguir'), perto(o, 'pato', f'{o}.desiste_dist', inv=True)],
              estado(o, 'patrulha') + [setn(o, 'base_x', '=', f'{o}.X()')]),
            E([est(o, 'perseguir'), tm(o, 'ataque', '>', f'{o}.ataque_espera'),
               cmp(f'abs(pato.CenterX() - {o}.CenterX())', '<', f'{o}.investida_alcance'),
               cmp(f'abs(pato.CenterY() - {o}.CenterY())', '<', f'{o}.investida_alt')],
              estado(o, 'preparar') + [som('som_roda.wav', 70)]),
            E([est(o, 'preparar')], [brilho(o, PULSO), I('AnimatableCapability::AnimatableBehavior::SetSpeedScale', o, 'Animation', '=', '5'),
                                     I('Create', '', 'explosao_faiscas', f'{o}.CenterX()', f'{o}.Y() + {o}.Height()', '')]),
            E([est(o, 'preparar', '!=')], [brilho(o, '1')]),
            E([est(o, 'preparar'), tm(o, 'estado', '>', f'{o}.aviso_tempo')],
              estado(o, 'atacar') + [setn(o, 'direcao', '=', f'sign(pato.CenterX() - {o}.CenterX() + 0.001)'),
                                     maxv(o, f'{o}.investida_vel'), som('som_investida.wav', 70, '0.8'), rst(o, 'travado')]),
            E([est(o, 'atacar')], [], lado(o)),
            E([est(o, 'atacar'), anda_algo(o)], [rst(o, 'travado')]),
            E([est(o, 'atacar'), tm(o, 'estado', '>', f'{o}.investida_tempo_max')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([est(o, 'atacar'), tm(o, 'travado', '>', f'{o}.travado_tempo')],
              estado(o, 'quique') + [setn(o, 'direcao', '*', '-1'), pulo_vel(o, f'{o}.quique_pulo'), pula(o),
                                     maxv(o, f'{o}.rolagem_vel'), som('som_bate_parede.wav', 70, '1.2')]),
            E([est(o, 'quique')], [], lado(o)),
            E([est(o, 'quique'), tm(o, 'estado', '>', f'{o}.atordoa_tempo')], estado(o, 'perseguir') + [rst(o, 'ataque')]),
            E([est(o, 'patrulha'), anda_algo(o, inv=True), tm(o, 'estado', '>', '0.3')],
              [setn(o, 'direcao', '*', '-1'), rst(o, 'estado')]),
        ]),
    ])


# ---------------------------------------------------------------- partes copiadas do jogo atual
def acha_grupo(evs, nome):
    return next(e for e in evs if e['type'].endswith('::Group') and e['name'] == nome)


def tem_cond(ev, tipo, *params):
    return any(c['type']['value'] == tipo and c['parameters'][:len(params)] == list(params) for c in ev['conditions'])


def eventos_novos(antigo):
    prep = copy.deepcopy(acha_grupo(antigo, 'Preparar inimigos'))
    estados = copy.deepcopy(acha_grupo(antigo, 'Estados (terrestres)'))
    paredes = copy.deepcopy(acha_grupo(antigo, 'Paredes'))
    separa = copy.deepcopy(acha_grupo(antigo, 'Separação'))
    arvore = copy.deepcopy(acha_grupo(antigo, 'Árvore condenada'))
    caveira = copy.deepcopy(acha_grupo(antigo, 'Caveira gigante'))
    sapo = copy.deepcopy(acha_grupo(antigo, 'Sapo'))
    cutulu = copy.deepcopy(acha_grupo(antigo, 'Cutulu'))
    mina = copy.deepcopy(acha_grupo(antigo, 'Mina demoníaca'))

    # Preparar: além do que já fazia, o tranco e os cronômetros novos começam zerados.
    # Evento novo (o do começo da cena fica como está): todo inimigo ainda não preparado, inclusive os criados no meio da
    # cena, começa com os cronômetros zerados, senão as comparações de cronômetro nunca valem.
    prep['events'].append(FE('Inimigo', [b('Inimigo', 'preparado', False)], [
        setb('Inimigo', 'preparado')] + [rst('Inimigo', t) for t in
        ('ataque', 'estado', 'tiro', 'pulo', 'lingua', 'espiral', 'ciclo', 'recuo', 'frenesi', 'hit_som_cooldown')]))

    # Estados dos terrestres: com firme (estados próprios como caído ou tonto) não toma tranco.
    for ev in estados['events'][1]['events']:
        if ev['type'].endswith('Standard') and tem_cond(ev, 'BooleanObjectVariable', 'Terrestre', 'acertado', 'True'):
            for sub in ev['events']:
                if not tem_cond(sub, 'BooleanObjectVariable', 'Terrestre', 'firme'):
                    sub['conditions'].append(b('Terrestre', 'firme', False))
    estados['events'][0]['comment'] += ' Com firme = True (estados próprios, como caído, tonto ou frenesi) não toma tranco.'

    # Paredes: só pula a parede quem está perseguindo (na investida, a parede é o fim da corrida).
    for ev in paredes['events']:
        if ev['type'].endswith('Standard') and any(a['type']['value'] == 'PlatformBehavior::SimulateJumpKey' for a in ev['actions']):
            for c in ev['conditions']:
                if c['type']['value'] == 'StringObjectVariable' and c['parameters'][1] == 'estado':
                    c['parameters'][2], c['parameters'][3] = '=', '"perseguir"'
            ev['conditions'].append(b('Terrestre', 'firme', False))
    paredes['events'][0]['comment'] = ('Encostado numa parede: pula se está perseguindo (e sem firme), dá meia-volta se '
                                       'está patrulhando.')

    # Árvore: o sorteio do desenho continua; caveira: a explosão continua; sapo: a cura continua; cutulu: os dois ataques.
    sorteio = [e for e in arvore['events'] if not e['type'].endswith('Comment')]
    caveira_antigos = caveira['events']
    # da árvore de eventos do sapo, só os blocos da cura: o estado "curar" (dentro do bloco do sapo vivo) e o efeito
    sapo_vivo = sapo['events'][1]['events']
    cura_estados = [e for e in sapo_vivo if 'curar' in json.dumps(e) or ('"cura"' in json.dumps(e) and 'cura_intervalo' in json.dumps(e))]
    cura_resto = [e for e in sapo['events'][2:] if not (e['type'].endswith('Standard') and any(
        c['type']['value'] == 'FireBullet::FireBullet::HasJustFired' for c in e['conditions']))]
    cura_ev = [E([vivo('sapo')], [], cura_estados)] + cura_resto
    mina_mov = [e for e in mina['events'] if not e['type'].endswith('Comment')]
    for ev in mina_mov:            # tira a explosão antiga (agora é a morte que explode)
        ev['events'] = [s for s in ev.get('events', []) if 'som_explosao.wav' not in json.dumps(s)]
    cutulu_antigos = [e for e in cutulu['events'] if not e['type'].endswith('Comment')]

    comum = COM(f'{MARCA}: cada inimigo tem um jeito próprio de lutar (ver o comentário de cada grupo e '
                'tools/t78_inimigos_mecanicas.py). Estados comuns dos que andam (grupo Terrestre) e dos que voam (grupo '
                'Voador); firme = não toma tranco; invulneravel = bala não machuca (só o soco); reflete = bala volta.')
    return [
        comum, prep, g_projeteis(), estados,
        G('Inferno', [g_condenado(), g_condenada(), g_torto(), g_azul(), g_inchado(), g_arvore(sorteio),
                      g_caveira_gigante(caveira_antigos)], (200, 70, 50)),
        g_voadores(),
        G('Inferno (voadores)', [g_caveira_azul(), g_cabeca(), g_diabinho(), g_moscas(), g_olho(), g_mina(mina_mov)],
          (200, 70, 50)),
        G('Purgatório', [g_zumbi(), g_pigman(), g_atirador(), g_sapo(cura_ev), g_cutulu(cutulu_antigos), g_voador()],
          (110, 140, 90)),
        G('Céu', [g_querubim(), g_serafim(), g_ofanim(), g_roda()], (230, 210, 120)),
        paredes, separa,
    ]


# ---------------------------------------------------------------- Combate: invulnerável e reflexo
def patch_combate(d):
    comb = next(x for x in d['externalEvents'] if x['name'] == 'Combate')
    proj = acha_grupo(comb['events'], 'Projéteis')
    inv = b('Inimigo', 'invulneravel', False)

    def garante(ev):
        if not tem_cond(ev, 'BooleanObjectVariable', 'Inimigo', 'invulneravel'):
            ev['conditions'].append(copy.deepcopy(inv))

    # bala direta
    k = next(i for i, e in enumerate(proj['events']) if e['type'].endswith('ForEach') and e.get('object') == 'projetil'
             and tem_cond(e, 'NumberObjectVariable', 'projetil', 'raio', '<=') and tem_cond(e, 'CollisionNP', 'projetil', 'Inimigo'))
    garante(proj['events'][k])
    if 'som_ping.wav' not in json.dumps(proj['events']):
        p = 'projetil_inimigo'
        ping = FE('projetil', [n('projetil', 'raio', '<=', '0'), col('projetil', 'Inimigo'), vivo('Inimigo'),
                               b('Inimigo', 'invulneravel')], [
            I('Create', '', 'sangue_lasca', 'projetil.CenterX()', 'projetil.CenterY()', ''),
            I('SetAngle', 'sangue_lasca', '=', 'projetil.Angle() + 180')], [
            E([tm('Inimigo', 'hit_som_cooldown', '>', '.1')], [som('som_ping.wav', 45, 'RandomFloatInRange(0.9, 1.15)'),
                                                               rst('Inimigo', 'hit_som_cooldown')]),
            E([b('Inimigo', 'reflete')], tiro('Inimigo', 'olho', 'ToDeg(atan2(pato.CenterY() - projetil.CenterY(), pato.CenterX() - projetil.CenterX()))',
                                              'Inimigo.reflete_vel', 'Inimigo.reflete_dano', x='projetil.CenterX()', y='projetil.CenterY()',
                                              extra=[setn(p, 'ttl', '=', '3')])),
            E(a=[I('Delete', 'projetil', '')])])
        proj['events'].insert(k, COM('Bala em inimigo invulnerável (invulneravel = True) não machuca: ricocheteia com um '
                                     'ping; se ele tem reflete = True, volta como projétil inimigo no pato.'))
        proj['events'].insert(k + 1, ping)
    # granada direta e explosão
    for ev in anda(proj['events']):
        if ev['type'].endswith('ForEach') and ev.get('object') == 'projetil' and tem_cond(ev, 'NumberObjectVariable', 'projetil', 'raio', '>') \
                and tem_cond(ev, 'CollisionNP', 'projetil', 'Inimigo'):
            garante(ev)
        if ev['type'].endswith('ForEach') and ev.get('object') == 'Inimigo' and 'explosao_fogo' in json.dumps(ev):
            garante(ev)
    eletro = acha_grupo(comb['events'], 'Eletricidade')
    for ev in anda(eletro['events']):
        if ev['type'].endswith('ForEach') and ev.get('object') == 'Inimigo':
            garante(ev)


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


# ---------------------------------------------------------------- objetos, grupos, recursos
def var(nome, valor, *ch):
    tipo = 'boolean' if isinstance(valor, bool) else 'string' if isinstance(valor, str) else 'number'
    return {'name': nome, 'persistentUuid': uid(*ch, nome), 'type': tipo, 'value': valor}


def migra(d):
    ext = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')
    if MARCA in json.dumps(ext['events'][:1], ensure_ascii=False):
        raise SystemExit('t78 já foi aplicada (marca no topo dos eventos Inimigos); não roda de novo.')
    O = {o['name']: o for o in d['objects']}
    grupos = {g['name']: g for g in d['objectsGroups']}

    # recursos: imagens dos projéteis e sons
    res = d['resources']['resources']
    nomes = {r['name'] for r in res}
    for t in TIPOS_DESENHADOS:
        f = f'{PROJ_DIR}/{t}.png'
        if f not in nomes:
            res.append({'file': f, 'kind': 'image', 'metadata': '', 'name': f, 'smoothed': False, 'userAdded': True})
    for s in SONS:
        if s not in nomes:
            res.append({'file': f'assets/{s}', 'kind': 'audio', 'metadata': '', 'name': s, 'preloadAsMusic': False,
                        'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True})

    # projetil_inimigo: animações e variáveis
    p = O['projetil_inimigo']
    have = {a['name'] for a in p['animations']}

    def anim_de(nome, imgs, tempo=0.08, loop=False):
        return {'name': nome, 'useMultipleDirections': False, 'directions': [{'looping': loop, 'timeBetweenFrames': tempo, 'sprites': [
            {'hasCustomCollisionMask': False, 'image': im, 'points': [], 'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
             'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': []} for im in imgs]}]}
    for t in TIPOS_DESENHADOS:
        if t not in have:
            p['animations'].append(anim_de(t, [f'{PROJ_DIR}/{t}.png']))
    if 'fogo' not in have:
        p['animations'].append(anim_de('fogo', FOGO, 0.07, True))
    for k, v in dict(tipo='', gravidade=0, vy=0, gira=0, ttl=0, boom=False, raio=0, dano_bomba=0).items():
        if not any(x['name'] == k for x in p['variables']):
            p['variables'].append(var(k, v, 'projetil_inimigo'))

    # olho_raio: o desenho do raio do olho demoníaco (como o eletro_raio)
    if 'olho_raio' not in O:
        o = copy.deepcopy(O['eletro_raio'])
        o.update(name='olho_raio', persistentUuid=uid('olho_raio'), variables=[])
        o['effects'][0]['stringParameters']['color'] = '255;80;40'
        o['outlineColor'] = {'r': 255, 'g': 80, 'b': 40}
        d['objects'].append(o)
        O['olho_raio'] = o

    # roda_anjo anda no chão: comportamento de plataforma (como os que andam)
    r = O['roda_anjo']
    if not any(bh['type'] == 'PlatformBehavior::PlatformerObjectBehavior' for bh in r['behaviors']):
        modelo = next(bh for bh in O['condenado']['behaviors'] if bh['type'] == 'PlatformBehavior::PlatformerObjectBehavior')
        r['behaviors'].append(copy.deepcopy(modelo))

    # grupos: anjos viram inimigos; grupo Voador; os grupos que só o comportamento antigo usava saem
    for g in ('Inimigo', 'Personagem'):
        for a in ANJOS:
            if a not in [x['name'] for x in grupos[g]['objects']]:
                grupos[g]['objects'].append({'name': a})
    if 'Voador' not in grupos:
        d['objectsGroups'].append({'name': 'Voador', 'objects': [{'name': v} for v in VOADORES]})
    usados_fora = json.dumps([x for x in d['externalEvents'] if x['name'] != 'Inimigos'] + [l['events'] for l in d['layouts']])
    for g in ('Mergulhador', 'Flutuante', 'CorpoACorpo'):
        if g in grupos and f'"{g}"' not in usados_fora and f'{g}.' not in usados_fora:
            d['objectsGroups'].remove(grupos[g])

    # variáveis: só as que faltam
    inimigos = [x['name'] for x in next(g for g in d['objectsGroups'] if g['name'] == 'Inimigo')['objects']]
    for nome in inimigos:
        o = O[nome]
        novas = dict(TODOS)
        if nome in VOADORES:
            novas.update(VOADOR_BASE)
        if nome in VARS:
            novas.update(VARS[nome])
        for k, v in novas.items():
            if not any(x['name'] == k for x in o['variables']):
                o['variables'].append(var(k, v, nome))
    # moscas: alerta é variável de cena; olho: ponto do raio na parede (variáveis de cena das fases com inimigos)
    for cena in CENAS_INIMIGOS:
        l = next(x for x in d['layouts'] if x['name'] == cena)
        for k in ('olho_rx', 'olho_ry', 'moscas_alerta', 'moscas_alerta_x', 'moscas_alerta_y'):
            if not any(v['name'] == k for v in l['variables']):
                l['variables'].append(var(k, 0, cena))

    # eventos
    ext['events'] = eventos_novos(ext['events'])
    patch_combate(d)


def main(caminho):
    os.makedirs(os.path.join(RAIZ, PROJ_DIR), exist_ok=True)
    for t in TIPOS_DESENHADOS:
        f = os.path.join(RAIZ, PROJ_DIR, f'{t}.png')
        if not os.path.exists(f):
            desenha(t).save(f)
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
