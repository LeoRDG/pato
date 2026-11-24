"""Tarefa 185: a tela de carregamento ganha um fundo com a jornada do jogo (assets/splash/carregando.jpg: o pato no
portal do Inferno, o Demônio, o Cutulu no monte do Purgatório e o olho de Deus no céu). Só preenche se o fundo ainda
estiver vazio. A imagem é pintada (não é pixel art exata), então é suavizada ao escalar.
Rodar uma vez:  python3 tools/t185_tela_carregamento.py
"""
from gd_mig import *

NOME, ARQUIVO = 'splash/carregando.jpg', 'assets/splash/carregando.jpg'


def migra(d):
    if not any(r['name'] == NOME for r in d['resources']['resources']):
        d['resources']['resources'].append({'file': ARQUIVO, 'kind': 'image', 'metadata': '', 'name': NOME,
                                            'smoothed': True, 'userAdded': True})
    tela = d['properties']['loadingScreen']
    if not tela['backgroundImageResourceName']:
        tela['backgroundImageResourceName'] = NOME


if __name__ == '__main__':
    roda(migra, lambda d: any(r['name'] == NOME for r in d['resources']['resources']), 't185')
