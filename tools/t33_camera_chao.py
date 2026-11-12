"""Tarefa 33: o chão mais baixo não sai da tela quando o pato pula.

A câmera (SmoothCamera, que anda antes dos eventos) subia junto com o pato sem limite. Agora um evento segura a subida:
  - pato.chao_baixo guarda o chão mais baixo em que o pato já pisou na cena (o Y dos pés; cresce se ele descer mais);
  - a câmera não sobe além do ponto em que sobram MARGEM px desse chão no pé da tela;
  - exceção: se o pato subir tanto (plataformas altas) que ficaria a menos de TETO px do topo da tela, a câmera volta a
    acompanhar: o pato nunca some por cima.
Rodar:  python3 tools/t33_camera_chao.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, C, E, PATH, comentario, grupo, upsert

NOME = 'Câmera não perde o chão'
MARGEM = 140   # px do chão mais baixo que sempre aparecem no pé da tela
TETO = 150     # px mínimos entre o topo da tela e o pato
SEM_CHAO = -999999
MEIA = 'CameraHeight("", 0) / 2'
LIMITE = f'min(pato.chao_baixo + {MARGEM} - {MEIA}, pato.Y() - {TETO} + {MEIA})'


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    pato = next(o for o in d['objects'] if o['name'] == 'pato')
    upsert(pato['variables'], 'chao_baixo', SEM_CHAO)
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    ctrl = next(e for e in walk(jog['events']) if e.get('name') == 'Controle do Pato')
    ctrl['events'] = [e for e in ctrl['events'] if e.get('name') != NOME]
    ctrl['events'].append(grupo(NOME, [
        comentario(f'O chão mais baixo em que o pato já pisou (pato.chao_baixo) fica sempre com pelo menos {MARGEM} px na tela: a câmera não sobe '
                   f'além disso quando o pato pula. Se o pato subir muito (ficaria a menos de {TETO} px do topo), a câmera volta a acompanhar.'),
        E([C('PlatformBehavior::IsOnFloor', 'pato', 'PlatformerObject')],
          [A('SetNumberObjectVariable', 'pato', 'chao_baixo', '=', 'max(pato.chao_baixo, pato.Y() + pato.Height())')]),
        E([C('NumberObjectVariable', 'pato', 'chao_baixo', '>', str(SEM_CHAO + 1)), C('CameraCenterY', '', '<', LIMITE, '""', '0')],
          [A('SetCameraCenterY', '', '=', LIMITE, '""', '0')]),
    ]))
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
