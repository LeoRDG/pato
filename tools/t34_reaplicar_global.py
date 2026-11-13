"""Tarefa 34: corrige a cadência (e recarga, velocidade, vida) dos upgrades ao trocar de cena.

O 'Aplicar upgrades' rodava com Ou(início da cena, pato.reaplicar_upgrades). A condição de objeto dentro do Ou
deixava o pato sem instâncias escolhidas no início da cena: pato.upg_cadencia lia 0 e o cooldown virava
cooldown_base * pow(0, nível) = 0 (tiro sem espera) a partir do nível 1; velocidade e vida nem eram aplicadas.
Agora o gatilho é a global reaplicar_upgrades (sem escolher objetos); a variável pato.reaplicar_upgrades
(criada na tarefa 28, só usada por isso) sai.
Rodar uma vez:  python3 tools/t34_reaplicar_global.py   (feche o projeto no GDevelop antes)
"""
from migra import carrega, salva, var, adiciona_var, objeto, externo, anda, C, A

OBJ_COND = ['pato', 'reaplicar_upgrades', 'True', '']


def main():
    d = carrega()
    n = 0
    for nome in ('AplicarUpgrades', 'Loja'):
        for e in anda(externo(d, nome)['events']):
            for c in e.get('conditions') or []:
                subs = c.get('subInstructions') or []
                for i, s in enumerate(subs):
                    if s['type']['value'] == 'BooleanObjectVariable' and s['parameters'][:3] == OBJ_COND[:3]:
                        subs[i] = C('BooleanVariable', 'reaplicar_upgrades', 'True', ''); n += 1
            acts = e.get('actions') or []
            for i, a in enumerate(acts):
                if a['type']['value'] == 'SetBooleanObjectVariable' and a['parameters'][:2] == ['pato', 'reaplicar_upgrades']:
                    acts[i] = A('SetBooleanVariable', 'reaplicar_upgrades', a['parameters'][2], ''); n += 1
    if n != 3:
        raise SystemExit(f'esperava 3 trocas (condição, desligar, compra), achei {n}; nada salvo')
    adiciona_var(d['variables'], var('reaplicar_upgrades', False))
    pv = objeto(d, 'pato')['variables']
    pv[:] = [v for v in pv if v['name'] != 'reaplicar_upgrades']
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
