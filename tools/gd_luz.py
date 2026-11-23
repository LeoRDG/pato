"""Identificadores de luz e efeitos do GDevelop 5.6 (lidos do runtime e do editor instalados).

Objeto de luz: Extensions/Lighting/JsExtension.js; ações de camada: núcleo (LayerInstructions);
efeitos: Extensions/Effects/*-pixi-filter.ts.
"""
OBJ_LUZ = 'Lighting::LightObject'
COMP_SOMBRA = 'Lighting::LightObstacleBehavior'
CONTEUDO_LUZ = {'radius': 0, 'color': '255;255;255', 'texture': '', 'debugMode': False}

ACAO_RAIO_LUZ = 'Lighting::SetRadius'            # objeto, expressão
ACAO_COR_LUZ = 'Lighting::SetColor'              # objeto, "R;G;B"
ACAO_LUZ_AMBIENTE = 'SetLayerAmbientLightColor'  # "", camada, "R;G;B"
ACAO_PARAM_EFEITO_CAMADA = 'SetLayerEffectParameter'  # "", camada, efeito, parâmetro, valor
ACAO_PARAM_EFEITO_OBJ = 'EffectCapability::EffectBehavior::SetEffectDoubleParameter'  # obj, "Effect", efeito, parâmetro, valor
ACAO_MOSTRA_CAMADA = 'ShowLayer'                 # "", camada
ACAO_ESCONDE_CAMADA = 'HideLayer'                # "", camada

CAMADA_LUZ = {'isLightingLayer': True, 'followBaseLayerCamera': True,
              'ambientLightColorR': 255, 'ambientLightColorG': 255, 'ambientLightColorB': 255}

EFEITOS = {
    'Godray': ('lacunarity', 'angle', 'gain', 'light', 'x', 'y', 'animationSpeed', 'padding', 'parallel'),
    'AdvancedBloom': ('threshold', 'bloomScale', 'brightness', 'blur', 'quality', 'padding'),
    'Shockwave': ('centerX', 'centerY', 'time', 'speed', 'amplitude', 'wavelength', 'brightness', 'radius'),
    'Glow': ('innerStrength', 'outerStrength', 'distance', 'color'),
}


def _a(tipo, params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def acao_raio_luz(obj, valor):
    return _a(ACAO_RAIO_LUZ, [obj, valor])


def acao_cor_luz(obj, cor):
    return _a(ACAO_COR_LUZ, [obj, cor])


def acao_luz_ambiente(camada, cor):
    return _a(ACAO_LUZ_AMBIENTE, ['', camada, cor])


def acao_param_efeito_camada(camada, efeito, param, valor):
    return _a(ACAO_PARAM_EFEITO_CAMADA, ['', camada, efeito, param, valor])


def _texto(nome):
    """nomes de efeito e de parâmetro são textos no GDevelop: precisam de aspas, senão viram vazio."""
    return nome if nome.startswith('"') else f'"{nome}"'


def acao_param_efeito_obj(obj, efeito, param, valor):
    return _a(ACAO_PARAM_EFEITO_OBJ, [obj, 'Effect', _texto(efeito), _texto(param), valor])


def acao_mostra_camada(camada):
    return _a(ACAO_MOSTRA_CAMADA, ['', camada])


def acao_esconde_camada(camada):
    return _a(ACAO_ESCONDE_CAMADA, ['', camada])
