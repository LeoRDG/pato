"""Tarefa 198: preços da loja de acordo com o que se ganha.
Antes todo item custava preco_base 50 e preco_mult 1,6 (50, 80, 128): a loja inteira saía por ~2900 moedas, e uma ida ao
Inferno solta ~137 moedas de valor médio ~27 (~3700), então uma corrida comprava quase tudo. Como as moedas ficam com o pato
quando ele morre, o laço é morrer, comprar e tentar de novo, e cada compra precisa pesar.
Novos preços (preço do nível n = preco_base * preco_mult^n):
- atributos básicos (cadência, dano, recarga, velocidade, pulo, vida): 200 * 2^n = 200, 400, 800;
- ímã (conforto, não poder): 150 * 2^n = 150, 300, 600;
- efeitos que mudam o jeito de lutar (ricochete, perfuração, eletricidade, vampirismo, incendiária, cadáver): 350 * 2^n
  = 350, 700, 1400;
- laser (um nível só, muda a arma): 1500.
Total ~25.600 moedas, umas 7 idas ao Inferno; a primeira compra 6 a 8 primeiros níveis.
Só muda o item que ainda está no padrão antigo (50 e 1,6); preço que o usuário já mexeu fica como está.
Rodar uma vez:  python3 tools/t198_precos.py
"""
from gd_mig import *

PRECOS = {}
for u in ('cadencia', 'dano', 'recarga', 'velocidade', 'pulo', 'vida'):
    PRECOS[u] = (200, 2)
PRECOS['ima'] = (150, 2)
for u in ('ricochete', 'perfuracao', 'eletricidade', 'vampirismo', 'incendiaria', 'cadaver'):
    PRECOS[u] = (350, 2)
PRECOS['laser'] = (1500, 2)


def migra(d):
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    for it in cat['children']:
        c = {x['name']: x for x in it['children']}
        u = c['id']['value']
        if u in PRECOS and c['preco_base']['value'] == 50 and c['preco_mult']['value'] == 1.6:
            c['preco_base']['value'], c['preco_mult']['value'] = PRECOS[u]


def feito(d):
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    return not any({x['name']: x.get('value') for x in it['children']}['preco_base'] == 50 for it in cat['children'])


if __name__ == '__main__':
    roda(migra, feito, 't198')
