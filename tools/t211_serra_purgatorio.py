"""Tarefa 211: serra pintada no HubPurgatorio e caverna pintada na fase Purgatorio, no lugar do tilemap de hachura.

Na camada Fundo do Purgatorio a serra era a instância de tiles_purgatorio_decor posta pela t72: blocos de 5 tiles em
degraus, todos com o mesmo tile de hachura diagonal (listras escuras em xadrez), que parecia ruído chapado. Na fase a
subida é por dentro da montanha, então lá entra um fundo de caverna; a serra (lado de fora) vai para o hub.
- bg_purgatorio_caverna (Sprite, pasta cenario), imagem assets/purgatorio/fundo/caverna.png (gerada por
  tools/arte_caverna_purgatorio.py, arte 2x): uma instância na camada Fundo do Purgatorio no lugar da serra antiga,
  com o mesmo zOrder (1), no canto (-1664, -2752) e com o dobro do tamanho da imagem.
- bg_purgatorio_serra (Sprite, pasta cenario), imagem assets/purgatorio/fundo/serra.png (gerada por
  tools/arte_serra_purgatorio.py, arte 2x, enquadrada para a câmera da camada fundo do hub): uma instância na camada
  fundo do HubPurgatorio no canto (-1280, -704), com o dobro do tamanho da imagem, no zOrder de bg_purgatorio_longe e
  posta depois dele (fica na frente do fundo opaco e atrás dos pilares, da névoa, do mercador e dos portais).
Sai só a instância de tiles_purgatorio_decor da camada Fundo do Purgatorio. O objeto tiles_purgatorio_decor, o atlas,
o terreno (tiles_purgatorio, com colisão) e as pontes não mudam; nada mais do hub muda.
Rodar uma vez:  python3 tools/t211_serra_purgatorio.py
"""
from PIL import Image
from gd_mig import *

ESCALA = 2
# (objeto, imagem, animação, cena, camada, canto x, canto y) — os cantos são os X0, Y0 dos geradores de arte
FUNDOS = [
    ('bg_purgatorio_caverna', 'assets/purgatorio/fundo/caverna.png', 'caverna', 'Purgatorio', 'Fundo', -1664, -2752),
    ('bg_purgatorio_serra', 'assets/purgatorio/fundo/serra.png', 'serra', 'HubPurgatorio', 'fundo', -1280, -704),
]


def migra(d):
    ids = Ids('t211')
    purg = cena(d, 'Purgatorio')
    antigas = [i for i in purg['instances'] if i['name'] == 'tiles_purgatorio_decor' and i['layer'] == 'Fundo']
    z_antiga = antigas[0]['zOrder'] if antigas else 1
    for i in antigas:
        purg['instances'].remove(i)
    print(f'serra antiga removida do Purgatorio: {len(antigas)} instância(s)')

    for nome, img, anim_, nome_cena, camada, x, y in FUNDOS:
        w, h = Image.open(os.path.join(RAIZ, img)).size
        poe_recursos(d, [img])
        poe_objeto(d, sprite(ids, nome, [(anim_, [img], 1, 0.1, False)]), 'cenario')
        c = cena(d, nome_cena)
        if nome_cena == 'Purgatorio':
            z, pos = z_antiga, len(c['instances'])
        else:
            longe = next(i for i in c['instances'] if i['name'] == 'bg_purgatorio_longe')
            z, pos = longe['zOrder'], c['instances'].index(longe) + 1
        c['instances'].insert(pos, inst(ids, nome, f'{nome_cena}/{anim_}', x, y, z, camada, w * ESCALA, h * ESCALA))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'bg_purgatorio_caverna') is not None, 't211')
