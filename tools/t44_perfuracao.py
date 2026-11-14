"""Tarefa 44: upgrade "Perfuração" na loja: +1 inimigo atravessado por nível (1 nível = 1 furo).

- Novo item no catálogo: id "perfuracao"; upgrades.perfuracao = 0.
- Ao nascer, a bala soma GlobalVariable(upgrades.perfuracao) aos furos da arma (Arma.furos). O resto já existia:
  cada inimigo acertado gasta um furo e a bala some quando não sobra nenhum. A granada continua explodindo no inimigo.
Rodar uma vez:  python3 tools/t44_perfuracao.py
"""
import json
from migra import carrega, salva, var, estrutura, adiciona_var, externo, A


def main():
    d = carrega()
    proj = next(e for e in externo(d, 'Combate')['events'] if e.get('name') == 'Projéteis')['events']
    if 'upgrades.perfuracao' in json.dumps(proj):
        print('já migrado'); return
    cat = next(v for v in d['variables'] if v['name'] == 'loja_catalogo')
    if not any(c['value'] == 'perfuracao' for i in cat['children'] for c in i['children'] if c['name'] == 'id'):
        cat['children'].append(estrutura(None, {'id': 'perfuracao', 'nome': 'Perfuração',
                                                'descricao': '+1 inimigo atravessado por bala por nível',
                                                'tipo': 'upgrade', 'nivel_max': 3, 'preco_base': 50, 'preco_mult': 1.6,
                                                'requer': ''}))
    adiciona_var(next(v for v in d['variables'] if v['name'] == 'upgrades')['children'], var('perfuracao', 0))

    nasce = next(e for e in proj if e.get('name') == 'Balas (alcance, queda e perfuração)')['events'][1]
    i = next(n for n, a in enumerate(nasce['actions']) if a['parameters'][:4] == ['projetil', 'furos', '=', 'Arma.furos'])
    nasce['actions'].insert(i + 1, A('SetNumberObjectVariable', 'projetil', 'furos', '+', 'GlobalVariable(upgrades.perfuracao)'))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
