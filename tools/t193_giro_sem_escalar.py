"""Tarefa 193: o pato não escala mais parede com o giro do pulo no ar.
Causa: o giro (tween "giroPulo" no ângulo do pato) gira junto a máscara de colisão. Encostado numa parede, a quina girada
entra nela; no começo do quadro seguinte o comportamento de plataforma separa o pato da parede e, como faz sempre que
precisa separar e o pulo não está apertado, devolve o pulo (_separateFromPlatforms(...) && !_jumpKey -> _canJump = true).
Apertando o pulo rápido contra a parede, cada giro devolvia um pulo e o pato subia sem fim.
Correção: o giro fica só no desenho. Logo depois de desenhar o quadro, enquanto o tween giroPulo existe, o ângulo do pato
volta a 0; no quadro seguinte a plataforma anda com a máscara reta e só depois o tween (que vem depois dela na lista de
comportamentos) põe o ângulo do giro de volta, a tempo dos eventos e do desenho.
Rodar uma vez:  python3 tools/t193_giro_sem_escalar.py
"""
from gd_mig import *

CODIGO = [
    '// Giro do pulo só no desenho (t193): a máscara girada entrava na parede e a plataforma devolvia o pulo ao separar.',
    '// Depois de desenhar, o pato volta a ângulo 0; o tween "giroPulo" põe o giro de volta depois da plataforma andar.',
    'const cena = runtimeScene;',
    'if (!cena.__giroSoNoDesenho) {',
    '  cena.__giroSoNoDesenho = true;',
    '  const desenha = cena.render.bind(cena);',
    '  cena.render = function (...a) {',
    '    const r = desenha(...a);',
    '    for (const p of cena.getObjects("pato")) {',
    '      const tw = p.getBehavior("Tween");',
    '      if (tw && tw.exists("giroPulo")) p.setAngle(0);',
    '    }',
    '    return r;',
    '  };',
    '}',
]


def migra(d):
    jog = folha(d, 'Jogador')['events']
    js = {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': CODIGO, 'parameterObjects': '', 'useStrict': True,
          'eventsSheetExpanded': False}
    jog.insert(1, grupo('Giro do pulo so no desenho', [js]))


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'Jogador')['events'], 'Giro do pulo so no desenho') is not None, 't193')
