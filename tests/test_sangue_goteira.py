import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
G = next(o for o in JOGO['objects'] if o['name'] == 'sangue_goteira')


def test_goteira_pinga_sem_parar():
    assert G['type'] == 'ParticleSystem::ParticleEmitter'
    assert G['tank'] < 0 and G['destroyWhenNoParticles'] is False        # não acaba nem some
    assert 0 < G['flow'] <= 10                                           # gotas contadas, não um jorro
    assert G['maxParticleNb'] >= G['flow'] * G['particleLifeTimeMax']    # cabe toda gota viva


def test_gota_cai_pela_gravidade_e_aponta_para_a_queda():
    assert G['particleGravityY'] > 0 and G['particleGravityX'] == 0
    queda = 0.5 * G['particleGravityY'] * G['particleLifeTimeMin'] ** 2
    assert queda > 300                                                   # cai um bom pedaço antes de sumir
    assert G['emitterForceMax'] * G['particleLifeTimeMax'] < 0.1 * queda  # o empurrão inicial quase não conta: é gota, não jato
    # o GDevelop gira a partícula no sentido do movimento só com os dois ângulos em 0 e gravidade ligada
    assert G['particleAngle1'] == 0 and G['particleAngle2'] == 0
    assert G['rendererType'] == 'Line' and G['rendererParam1'] > G['rendererParam2'] > 0     # alongada


def test_cor_de_sangue():
    r, g, b = (int(x) for x in G['particleColor1'].split(';'))
    assert r > 120 and g < 40 and b < 40 and G['additive'] is False
    assert (G['particleRed1'], G['particleGreen1'], G['particleBlue1']) == (r, g, b)
    assert G['particleAlpha2'] > 100                                     # não desbota no ar
