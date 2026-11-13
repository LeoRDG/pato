"""Tarefa 35: números fixos dos eventos de jogabilidade viram variáveis de objeto (editáveis no GDevelop).

Cada número que estava escrito dentro de um evento (distância de aviso, tempo de espera, velocidade de investida, força do soco, gravidade da moeda...)
passa a ser lido de uma variável do objeto dono, com o MESMO valor de antes (o jogo se comporta igual).
Só ADICIONA: se a variável já existe no objeto, o valor atual é mantido. Os eventos só são trocados se ainda tiverem o número antigo.
Fora do escopo (continuam fixos): volume/tom dos sons, posições da HUD, parallax, constantes de matemática.
Rodar:  python3 tools/t35_numeros_em_variaveis.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json, re, uuid
from t12_armas import PATH

GRUPOS = {}  # preenchido em main()
VARS = []    # (objetos|grupo, nome, valor)
EDS = []     # (folha, caminho|None, antigo, novo, n)


def v(alvo, **vals):
    for k, x in vals.items():
        VARS.append((alvo, k, x))


def ed(folha, caminho, antigo, novo, n=1):
    EDS.append((folha, caminho, antigo, novo, n))


TERR = 'Terrestre'; MERG = 'Mergulhador'; FLUT = 'Flutuante'; CAC = 'CorpoACorpo'; ARMA = 'Arma'; FEED = 'Feedback'

# ---------- Inimigos: comuns ----------
v(TERR, empurrao_vel=250, dano_duracao=0.2, patrulha_fator=0.5, patrulha_raio=200, aggro_dist=800, desiste_dist=1000, travado_tempo=0.3, parar_dist=40)
ed('Inimigos', '2.1.0.0', '250', 'Terrestre.empurrao_vel')
ed('Inimigos', '2.1.0.0', 'Terrestre.kb_dir * 250', 'Terrestre.kb_dir * Terrestre.empurrao_vel')
ed('Inimigos', '2.1.1', '0.2', 'Terrestre.dano_duracao')
ed('Inimigos', '2.1.2', 'Terrestre.velocidade * 0.5', 'Terrestre.velocidade * Terrestre.patrulha_fator')
ed('Inimigos', '2.1.2.0', 'Terrestre.base_x + 200', 'Terrestre.base_x + Terrestre.patrulha_raio')
ed('Inimigos', '2.1.2.1', 'Terrestre.base_x - 200', 'Terrestre.base_x - Terrestre.patrulha_raio')
ed('Inimigos', '2.1.2.4', '800', 'Terrestre.aggro_dist')
ed('Inimigos', '2.1.3.0', '1000', 'Terrestre.desiste_dist')
ed('Inimigos', '17.3', '0.3', 'Terrestre.travado_tempo')
ed('Inimigos', '17.4', '0.3', 'Terrestre.travado_tempo')

v(MERG, empurrao_x=40, dano_duracao=0.2, patrulha_vel=180, aggro_dist=800, desiste_dist=1000, parar_dist=20, altura_sobre_pato=250,
  onda_amp=60, onda_suave=4, ataque_espera=2.5, ataque_alcance=80, aviso_tempo=0.5, mergulho_vel=900, mergulho_tempo=0.45)
ed('Inimigos', '8.1.0', 'Mergulhador.kb_dir * 40', 'Mergulhador.kb_dir * Mergulhador.empurrao_x')
ed('Inimigos', '8.1.1', '0.2', 'Mergulhador.dano_duracao')
ed('Inimigos', '8.1.2', '* 180 *', '* Mergulhador.patrulha_vel *')
ed('Inimigos', '8.1.2.0', '800', 'Mergulhador.aggro_dist')
ed('Inimigos', '8.1.3', 'pato.Y() - 250', 'pato.Y() - Mergulhador.altura_sobre_pato')
ed('Inimigos', '8.1.3.0', '20', 'Mergulhador.parar_dist')
ed('Inimigos', '8.1.3.1', '1000', 'Mergulhador.desiste_dist')
ed('Inimigos', '8.1.4', 'sin(TimeFromStart() * 3) * 60', 'sin(TimeFromStart() * 3) * Mergulhador.onda_amp')
ed('Inimigos', '8.1.4', 'min(1, 4 * TimeDelta())', 'min(1, Mergulhador.onda_suave * TimeDelta())')
ed('Inimigos', '8.1.5', '2.5', 'Mergulhador.ataque_espera')
ed('Inimigos', '8.1.5', '80', 'Mergulhador.ataque_alcance')
ed('Inimigos', '8.1.8', '0.5', 'Mergulhador.aviso_tempo')
ed('Inimigos', '8.1.9', '900 * TimeDelta()', 'Mergulhador.mergulho_vel * TimeDelta()')
ed('Inimigos', '8.1.10', '0.45', 'Mergulhador.mergulho_tempo')

v(FLUT, empurrao_x=40, dano_duracao=0.2, aggro_dist=700, desiste_dist=1000)
ed('Inimigos', '13.1.0', 'Flutuante.kb_dir * 40', 'Flutuante.kb_dir * Flutuante.empurrao_x')
ed('Inimigos', '13.1.1', '0.2', 'Flutuante.dano_duracao')
ed('Inimigos', '13.1.2', '700', 'Flutuante.aggro_dist')
ed('Inimigos', '13.1.3', '1000', 'Flutuante.desiste_dist')

# ---------- Inimigos: por tipo ----------
v(['zumbi'], parar_dist=40)
ed('Inimigos', '3.1.0', '40', 'zumbi.parar_dist')

v(['pigman'], parar_dist=40, ataque_espera=2.5, ataque_alcance=450, ataque_alt=200, aviso_tempo=0.5, investida_vel=650, investida_tempo=0.8)
ed('Inimigos', '4.1.0.0', '40', 'pigman.parar_dist')
ed('Inimigos', '4.1.2', '2.5', 'pigman.ataque_espera')
ed('Inimigos', '4.1.2', '450', 'pigman.ataque_alcance')
ed('Inimigos', '4.1.2', '200', 'pigman.ataque_alt')
ed('Inimigos', '4.1.3', '0.5', 'pigman.aviso_tempo')
ed('Inimigos', '4.1.3', '650', 'pigman.investida_vel')
ed('Inimigos', '4.1.5', '0.8', 'pigman.investida_tempo')

v(['atirador'], dist_max=600, dist_min=400, ataque_espera=2.5, ataque_alcance=800, aviso_tempo=0.5, tiro_vel=900, rajada=3)
ed('Inimigos', '5.1.0.0', '600', 'atirador.dist_max')
ed('Inimigos', '5.1.0.1', '400', 'atirador.dist_min')
ed('Inimigos', '5.1.1', '2.5', 'atirador.ataque_espera')
ed('Inimigos', '5.1.1', '800', 'atirador.ataque_alcance')
ed('Inimigos', '5.1.2', '0.5', 'atirador.aviso_tempo')
ed('Inimigos', '5.1.3', '900', 'atirador.tiro_vel')
ed('Inimigos', '5.1.5', '3', 'atirador.rajada')

v(['sapo'], dist_max=500, dist_min=300, ataque_espera=2.5, ataque_alcance=700, aviso_tempo=0.5, tiro_vel=700, atacar_tempo=0.4,
  cura_intervalo=4, cura_tempo=0.8, cura_raio=300, cura_valor=20, cura_brilho=0.4)
ed('Inimigos', '6.1.0.0', '500', 'sapo.dist_max')
ed('Inimigos', '6.1.0.1', '300', 'sapo.dist_min')
ed('Inimigos', '6.1.2', '2.5', 'sapo.ataque_espera')
ed('Inimigos', '6.1.2', '700', 'sapo.ataque_alcance')
ed('Inimigos', '6.1.3', '0.5', 'sapo.aviso_tempo')
ed('Inimigos', '6.1.3', '700', 'sapo.tiro_vel')
ed('Inimigos', '6.1.4', '0.4', 'sapo.atacar_tempo')
ed('Inimigos', '6.1.5', '4', 'sapo.cura_intervalo')
ed('Inimigos', '6.1.6', '0.8', 'sapo.cura_tempo')
ed('Inimigos', '6.2.0', '300', 'sapo.cura_raio')
ed('Inimigos', '6.2.0', 'Inimigo.vida + 20', 'Inimigo.vida + sapo.cura_valor')
ed('Inimigos', '6.3', '0.4', 'sapo.cura_brilho')

v(['cutulu'], parar_dist=40, ataque_espera=2.5, ataque_alcance=500, aviso_tempo=0.5, investida_vel=550, investida_tempo=0.4,
  voo_vel=380, voo_pulo=900, voo_tempo_min=0.3, pulo_normal=600)
ed('Inimigos', '7.1.0.0', '40', 'cutulu.parar_dist')
ed('Inimigos', '7.1.2', '2.5', 'cutulu.ataque_espera')
ed('Inimigos', '7.1.2', '500', 'cutulu.ataque_alcance')
ed('Inimigos', '7.1.4', '0.5', 'cutulu.aviso_tempo')
ed('Inimigos', '7.1.4.0', '550', 'cutulu.investida_vel')
ed('Inimigos', '7.1.4.1', '380', 'cutulu.voo_vel')
ed('Inimigos', '7.1.4.1', '900', 'cutulu.voo_pulo')
ed('Inimigos', '7.1.6', '0.4', 'cutulu.investida_tempo')
ed('Inimigos', '7.1.7', '0.3', 'cutulu.voo_tempo_min')
ed('Inimigos', '7.1.7', '600', 'cutulu.pulo_normal')

v(CAC, parar_dist=40, ataque_espera=2.5, ataque_alcance=150, aviso_tempo=0.45, investida_fator=4, investida_tempo=0.35)
ed('Inimigos', '9.1.0.0', '40', 'CorpoACorpo.parar_dist')
ed('Inimigos', '9.1.2', '2.5', 'CorpoACorpo.ataque_espera')
ed('Inimigos', '9.1.2', '150', 'CorpoACorpo.ataque_alcance')
ed('Inimigos', '9.1.3', '0.45', 'CorpoACorpo.aviso_tempo')
ed('Inimigos', '9.1.3', 'CorpoACorpo.velocidade * 4', 'CorpoACorpo.velocidade * CorpoACorpo.investida_fator')
ed('Inimigos', '9.1.5', '0.35', 'CorpoACorpo.investida_tempo')

v(['condenado_inchado'], parar_dist=40, ataque_espera=2.5, ataque_alcance=160, aviso_tempo=0.6, explosao_raio=230, explosao_empurrao=600)
ed('Inimigos', '10.1.0.0', '40', 'condenado_inchado.parar_dist')
ed('Inimigos', '10.1.2', '2.5', 'condenado_inchado.ataque_espera')
ed('Inimigos', '10.1.2', '160', 'condenado_inchado.ataque_alcance')
ed('Inimigos', '10.1.3', '0.6', 'condenado_inchado.aviso_tempo')
ed('Inimigos', '10.1.3.0', '230', 'condenado_inchado.explosao_raio')
ed('Inimigos', '10.1.3.0', '* 600', '* condenado_inchado.explosao_empurrao')

v(['caveira_gigante'], parar_dist=40, ataque_espera=2.5, ataque_espera_extra=4, ataque_alcance=350, aviso_tempo=0.6, fogo_inicio=0.4, fogo_fim=1.4,
  fogo_raio=260, fogo_empurrao=600, ataque_duracao=1.6)
ed('Inimigos', '11.1.0.0', '40', 'caveira_gigante.parar_dist')
ed('Inimigos', '11.1.1', '2.5', 'caveira_gigante.ataque_espera')
ed('Inimigos', '11.1.1', '4', 'caveira_gigante.ataque_espera_extra')
ed('Inimigos', '11.1.1', '350', 'caveira_gigante.ataque_alcance')
ed('Inimigos', '11.1.2', '0.6', 'caveira_gigante.aviso_tempo')
ed('Inimigos', '11.1.3', '0.4', 'caveira_gigante.fogo_inicio')
ed('Inimigos', '11.1.3', '1.4', 'caveira_gigante.fogo_fim')
ed('Inimigos', '11.1.3', '260', 'caveira_gigante.fogo_raio')
ed('Inimigos', '11.1.3', '* 600', '* caveira_gigante.fogo_empurrao')
ed('Inimigos', '11.1.4', '1.6', 'caveira_gigante.ataque_duracao')

v(['moscas'], onda_amp=20, onda_suave=4, tremor=3, vertical_fator=0.7)
ed('Inimigos', '14.1.0', 'sin(TimeFromStart() * 6) * 20', 'sin(TimeFromStart() * 6) * moscas.onda_amp')
ed('Inimigos', '14.1.0', 'min(1, 4 * TimeDelta())', 'min(1, moscas.onda_suave * TimeDelta())')
ed('Inimigos', '14.1.1', 'moscas.base_x) * 3', 'moscas.base_x) * moscas.tremor')
ed('Inimigos', '14.1.1', 'TimeFromStart() * 11) * 3', 'TimeFromStart() * 11) * moscas.tremor')
ed('Inimigos', '14.1.1', 'moscas.velocidade * 0.7', 'moscas.velocidade * moscas.vertical_fator')

v(['olho_demoniaco'], onda_amp=40, onda_suave=4, altura_sobre_pato=200, dist_max=550, dist_min=350, ataque_espera=2.5, ataque_alcance=700,
  aviso_tempo=0.5, tiro_vel=650, atacar_tempo=0.3)
ed('Inimigos', '15.1.0', 'sin(TimeFromStart() * 2) * 40', 'sin(TimeFromStart() * 2) * olho_demoniaco.onda_amp')
ed('Inimigos', '15.1.0', 'min(1, 4 * TimeDelta())', 'min(1, olho_demoniaco.onda_suave * TimeDelta())')
ed('Inimigos', '15.1.1', 'pato.Y() - 200', 'pato.Y() - olho_demoniaco.altura_sobre_pato')
ed('Inimigos', '15.1.1.0', '550', 'olho_demoniaco.dist_max')
ed('Inimigos', '15.1.1.1', '350', 'olho_demoniaco.dist_min')
ed('Inimigos', '15.1.2', '2.5', 'olho_demoniaco.ataque_espera')
ed('Inimigos', '15.1.2', '700', 'olho_demoniaco.ataque_alcance')
ed('Inimigos', '15.1.3', '0.5', 'olho_demoniaco.aviso_tempo')
ed('Inimigos', '15.1.3', '650', 'olho_demoniaco.tiro_vel')
ed('Inimigos', '15.1.4', '0.3', 'olho_demoniaco.atacar_tempo')

v(['mina_demoniaca'], onda_amp=15, onda_suave=4, perseguir_dist=400, explodir_dist=140, aviso_tempo=0.5, explosao_raio=200, explosao_empurrao=600)
ed('Inimigos', '16.1', 'sin(TimeFromStart() * 2) * 15', 'sin(TimeFromStart() * 2) * mina_demoniaca.onda_amp')
ed('Inimigos', '16.1', 'min(1, 4 * TimeDelta())', 'min(1, mina_demoniaca.onda_suave * TimeDelta())')
ed('Inimigos', '16.1.0', '400', 'mina_demoniaca.perseguir_dist')
ed('Inimigos', '16.1.1', '140', 'mina_demoniaca.explodir_dist')
ed('Inimigos', '16.1.2', '0.5', 'mina_demoniaca.aviso_tempo')
ed('Inimigos', '16.1.2.0', '200', 'mina_demoniaca.explosao_raio')
ed('Inimigos', '16.1.2.0', '* 600', '* mina_demoniaca.explosao_empurrao')

# ---------- Boss ----------
v(['boss'], pulo_dist=1200, pulo_cooldown=5, pulo_x1=0.25, pulo_x2=0.75, pulo_alt1_min=300, pulo_alt1_max=400, pulo_alt2_min=600, pulo_alt2_max=1000,
  pulo_dur_min=1, pulo_dur_max=3, pulo_giro_min=3, pulo_giro_max=6)
ed('Boss', '1.1', '1200', 'boss.pulo_dist')
ed('Boss', '1.1', 'boss.CenterX()) * 0.25', 'boss.CenterX()) * boss.pulo_x1')
ed('Boss', '1.1', 'boss.CenterX()) * 0.75', 'boss.CenterX()) * boss.pulo_x2')
ed('Boss', '1.1', 'RandomInRange(-400, -300)', 'RandomInRange(-boss.pulo_alt1_max, -boss.pulo_alt1_min)')
ed('Boss', '1.1', 'RandomInRange(-1000, -600)', 'RandomInRange(-boss.pulo_alt2_max, -boss.pulo_alt2_min)')
ed('Boss', '1.1', 'RandomInRange(1, 3)', 'RandomInRange(boss.pulo_dur_min, boss.pulo_dur_max)')
ed('Boss', '1.1', 'RandomFloatInRange(3, 6)', 'RandomFloatInRange(boss.pulo_giro_min, boss.pulo_giro_max)')
ed('Boss', '1.2', '5', 'boss.pulo_cooldown')

# ---------- Upgrades ----------
v(['pato'], upg_cadencia=0.85, upg_recarga=0.8, upg_dano=0.2, upg_velocidade=0.1, upg_vida_base=100, upg_vida_nivel=25, f1_moedas=500)
ed('AplicarUpgrades', None, 'pow(0.85, ', 'pow(pato.upg_cadencia, ')
ed('AplicarUpgrades', None, 'pow(0.8, ', 'pow(pato.upg_recarga, ')
ed('AplicarUpgrades', None, '1 + 0.2 * ', '1 + pato.upg_dano * ')
ed('AplicarUpgrades', None, '(1 + 0.1 * ', '(1 + pato.upg_velocidade * ')
ed('AplicarUpgrades', None, '100 + 25 * ', 'pato.upg_vida_base + pato.upg_vida_nivel * ')
ed('AplicarUpgrades', '2.1', '500', 'pato.f1_moedas')

# ---------- Combate ----------
v(['pato'], iframes_tempo=0.75)
ed('Combate', '1.5', '0.75', 'pato.iframes_tempo')
v(['projetil'], gravidade=900, dano_var=0.15)
ed('Combate', '2.2.1', '900 * TimeDelta()', 'projetil.gravidade * TimeDelta()')
ed('Combate', '2.7', 'RandomFloatInRange(0.85, 1.15)', 'RandomFloatInRange(1 - projetil.dano_var, 1 + projetil.dano_var)')
v(['explosao_fogo'], dano_var=0.1)
ed('Combate', '2.4.1.0.0', 'RandomFloatInRange(0.9, 1.1)', 'RandomFloatInRange(1 - explosao_fogo.dano_var, 1 + explosao_fogo.dano_var)')
v(['hit'], duracao=0.2)
ed('Combate', '2.8', '.2', 'hit.duracao')
v(FEED, subida=240, escala_decai=0.993, opacidade_decai=0.95)
ed('Combate', '4.3', '240 * TimeDelta()', 'Feedback.subida * TimeDelta()')
ed('Combate', '4.3', 'pow(0.993,', 'pow(Feedback.escala_decai,')
ed('Combate', '4.3', 'pow(0.95,', 'pow(Feedback.opacidade_decai,')
v(['moeda'], espalha_x=250, lanca_min=400, lanca_max=700, gravidade=1800, quique=0.5, atrito_x=0.7, parada_vy=120, iman_dist=150, iman_vel=10,
  pisca_inicio=4, duracao=6)
ed('Combate', '5.1.1.0', 'RandomInRange(-250, 250)', 'RandomInRange(-moeda.espalha_x, moeda.espalha_x)')
ed('Combate', '5.1.1.0', 'RandomInRange(-700, -400)', 'RandomInRange(-moeda.lanca_max, -moeda.lanca_min)')
ed('Combate', '7.1.1', '1800 * TimeDelta()', 'moeda.gravidade * TimeDelta()')
ed('Combate', '7.1.2', '-0.5', '-moeda.quique')
ed('Combate', '7.1.2', '0.7', 'moeda.atrito_x')
ed('Combate', '7.1.2.0', '-120', '-moeda.parada_vy')
ed('Combate', '7.2.1', '150', 'moeda.iman_dist')
ed('Combate', '7.2.1', ') * 10 * TimeDelta()', ') * moeda.iman_vel * TimeDelta()', 2)
ed('Combate', '7.2.2', '4', 'moeda.pisca_inicio')
ed('Combate', '7.2.3', '6', 'moeda.duracao')

# ---------- Jogador: pato ----------
v(['pato'], pulo_buffer=0.12, pulo_corte=0.45, pulo_corte_vel=250, dash_queda_max=700, dash_gravidade=1400, poeira_queda_min=250,
  dano_anim_tempo=0.3, camera_abaixo=140, camera_acima=150, morte_escala_tempo=0.3, morte_espera=0.15,
  soco_alcance_parede=150, soco_dano=12, soco_empurrao=4, soco_stun=0.2, soco_vel_inimigo=900, soco_duracao=0.16,
  soco_alcance_ini=35, soco_alcance_extra=95, soco_rastro_dist=120, soco_hit_alcance=150, soco_hit_folga=60,
  recuo_decai=0.98, coice_decai=0.000001, recuo_max=35, laser_alcance=4000, giro_decai=1.6, giro_sobe=3.6)
ed('Jogador', '3.3.2', '0.12', 'pato.pulo_buffer')
ed('Jogador', '3.3.4', '-250', '-pato.pulo_corte_vel')
ed('Jogador', '3.3.4', 'CurrentFallSpeed() * 0.45', 'CurrentFallSpeed() * pato.pulo_corte')
ed('Jogador', '3.3.5', 'min(700,', 'min(pato.dash_queda_max,')
ed('Jogador', '3.3.5', '+ 1400 *', '+ pato.dash_gravidade *')
ed('Jogador', '3.3.8', '250', 'pato.poeira_queda_min')
ed('Jogador', '3.3.8', '(pato.queda_vy - 250) / 450', '(pato.queda_vy - pato.poeira_queda_min) / 450')
ed('Jogador', '3.4.2', '0.3', 'pato.dano_anim_tempo')
ed('Jogador', '3.5.2', 'pato.chao_baixo + 140', 'pato.chao_baixo + pato.camera_abaixo', 2)
ed('Jogador', '3.5.2', 'pato.Y() - 150', 'pato.Y() - pato.camera_acima', 2)
ed('Jogador', '3.2.1', '0.3', 'pato.morte_escala_tempo')
ed('Jogador', '3.2.2', '0.15', 'pato.morte_espera')
ed('Jogador', '3.6.4.1', 'pato.soco_cos * 150', 'pato.soco_cos * pato.soco_alcance_parede')
ed('Jogador', '3.6.4.1', 'pato.soco_sin * 150', 'pato.soco_sin * pato.soco_alcance_parede')
ed('Jogador', '3.6.4.2', 'pato.soco_cos * 150', 'pato.soco_cos * pato.soco_alcance_parede')
ed('Jogador', '3.6.4.2', 'pato.soco_sin * 150', 'pato.soco_sin * pato.soco_alcance_parede')
ed('Jogador', '3.6.4.3', 'pato.soco_cos * 150', 'pato.soco_cos * pato.soco_alcance_parede')
ed('Jogador', '3.6.4.3', 'pato.soco_sin * 150', 'pato.soco_sin * pato.soco_alcance_parede')
ed('Jogador', '3.6.4.6', 'round(12 *', 'round(pato.soco_dano *')
ed('Jogador', '3.6.4.6', 'pato.soco_lado * 4', 'pato.soco_lado * pato.soco_empurrao')
ed('Jogador', '3.6.4.6', '0.2', 'pato.soco_stun')
ed('Jogador', '3.6.4.6', '150', 'pato.soco_hit_alcance')
ed('Jogador', '3.6.4.6', '/ 4) + 60', '/ 4) + pato.soco_hit_folga')
ed('Jogador', '3.6.8', '35 + 95 * sin', 'pato.soco_alcance_ini + pato.soco_alcance_extra * sin', 2)
ed('Jogador', '3.6.8', '/ 0.16)', '/ pato.soco_duracao)', 2)
ed('Jogador', '3.6.9', '120 *', 'pato.soco_rastro_dist *', 2)
ed('Jogador', '3.6.10', '0.16', 'pato.soco_duracao')
ed('Jogador', '3.6.11', '0.16', 'pato.soco_duracao')
ed('Jogador', '3.6.12.0', '900', 'pato.soco_vel_inimigo')
ed('Jogador', '3.6.12.0', '* 900', '* pato.soco_vel_inimigo')
ed('Jogador', '2.4', 'pow(0.98,', 'pow(pato.recuo_decai,')
ed('Jogador', '2.4', 'pow(0.000001,', 'pow(pato.coice_decai,')
ed('Jogador', '2.4', '* 4000', '* pato.laser_alcance', 2)
ed('Jogador', '5.1.1.1', 'min(recuo, 35)', 'min(recuo, pato.recuo_max)')
ed('Jogador', '5.2.1', 'giro - 1.6 *', 'giro - pato.giro_decai *')
ed('Jogador', '5.2.2', 'giro + (1.6 + 1 / 0.5) *', 'giro + pato.giro_sobe *')

# ---------- Jogador: armas ----------
v(ARMA, disp_tempo=2.5)
ed('Jogador', '5.1.2.2', '/ 2.5)', '/ Arma.disp_tempo)')
for caminho, arma, dur, esc in (('5.1.1.5.1', 'pistola', 0.05, 3), ('5.1.1.5.2', 'doze', 0.07, 3.5), ('5.1.1.5.3', 'minigun', 0.04, 3), ('5.1.1.5.4', 'lanca', 0.09, 4)):
    v([arma], flash_dur=dur, flash_escala=esc)
    ed('Jogador', caminho, str(dur), f'{arma}.flash_dur')
    ed('Jogador', caminho, f'{esc} * RandomFloatInRange', f'{arma}.flash_escala * RandomFloatInRange')
v(['doze'], pump_espera=0.29)
ed('Jogador', '5.1.1.3.0', '.29', 'doze.pump_espera')


# ---------- aplicação ----------
def e_num(s):
    return re.fullmatch(r'-?\d*\.?\d+', s) is not None


def evento(evs, caminho):
    partes = [int(x) for x in caminho.split('.')]
    e = evs[partes[0]]
    for i in partes[1:]:
        e = e['events'][i]
    return e


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def params(e):
    for k in ('conditions', 'actions'):
        for ins in e.get(k) or []:
            yield ins['parameters']


def aplica(d):
    folhas = {x['name']: x['events'] for x in d['externalEvents']}
    objs = {o['name']: o for o in d['objects']}
    grupos = {g['name']: [o['name'] for o in g['objects']] for g in d['objectsGroups']}
    for alvo, nome, valor in VARS:
        for on in (grupos[alvo] if isinstance(alvo, str) else alvo):
            vs = objs[on].setdefault('variables', [])
            if not any(x['name'] == nome for x in vs):
                vs.append({'name': nome, 'persistentUuid': str(uuid.uuid4()), 'type': 'number', 'value': valor})
    for folha, caminho, antigo, novo, n in EDS:
        evs = folhas[folha]
        alvos = [evento(evs, caminho)] if caminho else list(todos(evs))
        feitos = 0
        for e in alvos:
            for ps in params(e):
                for i, p in enumerate(ps):
                    if not isinstance(p, str):
                        continue
                    if e_num(antigo):
                        if p == antigo:
                            ps[i] = novo; feitos += 1
                    elif antigo in p:
                        feitos += p.count(antigo); ps[i] = p.replace(antigo, novo)
        if feitos == 0:
            # idempotência: já trocado numa rodada anterior?
            if any(novo in p for e in alvos for ps in params(e) for p in ps if isinstance(p, str)):
                continue
            raise SystemExit(f'NÃO ACHEI {folha} {caminho} {antigo!r}')
        if feitos != n:
            raise SystemExit(f'{folha} {caminho} {antigo!r}: esperava {n}, troquei {feitos}')


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    aplica(d)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    print('variáveis:', len(VARS), 'trocas:', len(EDS))


if __name__ == '__main__':
    main()
