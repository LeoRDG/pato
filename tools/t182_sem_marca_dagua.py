"""Tarefa 182: tira o "Made with GDevelop" do canto do jogo (marca d'água; a tela de abertura já estava desligada).
Rodar uma vez:  python3 tools/t182_sem_marca_dagua.py
"""
from gd_mig import *


def migra(d):
    d['properties']['watermark']['showWatermark'] = False


if __name__ == '__main__':
    roda(migra, lambda d: not d['properties']['watermark']['showWatermark'], 't182')
