"""Tarefa 28: dados da loja do Hub e do mercador (só adiciona o que falta).

- Global loja_catalogo: lista de upgrades à venda (o menu da loja é montado a partir dela). Para criar um upgrade novo,
  basta adicionar um item no editor de variáveis do GDevelop: id, nome, descricao, tipo ("upgrade" ou "arma"),
  nivel_max, preco_base, preco_mult (preço = round(preco_base * pow(preco_mult, nivel))) e requer (id exigido, "" = nenhum).
- Global trader_morto, variáveis do mercador (paciência, multa, dano quando hostil, raio da loja), do pato (na_loja,
  reaplicar_upgrades, velocidade_base, ultimo_agressor, moedas_perdidas), projetil_inimigo.origem e variáveis de cena do Hub.
- Objetos do menu: loja_painel, loja_linha, loja_desc, loja_dica.
- Mercador: estado "patrulha" (sobra de inimigo) vira "calmo"; vida 10 vira 1500 só se ainda for 10.
Rodar uma vez:  python3 tools/t28_loja_dados.py   (feche o projeto no GDevelop antes)
"""
from migra import (carrega, salva, var, estrutura, lista, adiciona_var, acha_var, objeto, cena, copia_objeto)

CATALOGO = [
    ('cadencia', 'Cadência', '-15% de espera entre tiros por nível'),
    ('dano', 'Dano', '+20% de dano por nível'),
    ('recarga', 'Recarga', '-20% no tempo de recarga por nível'),
    ('velocidade', 'Velocidade', '+10% de velocidade por nível'),
    ('vida', 'Vida', '+25 de vida máxima por nível'),
]
VIDA_TRADER = 1500


def main():
    d = carrega()
    novos = []

    def add(lista_vars, v, onde):
        if adiciona_var(lista_vars, v):
            novos.append(f'{onde}.{v["name"]}')

    itens = [estrutura(None, {'id': i, 'nome': n, 'descricao': desc, 'tipo': 'upgrade', 'nivel_max': 3,
                              'preco_base': 50, 'preco_mult': 1.6, 'requer': ''}) for i, n, desc in CATALOGO]
    add(d['variables'], lista('loja_catalogo', itens), 'global')
    add(d['variables'], var('trader_morto', False), 'global')

    t = objeto(d, 'trader')
    for k, v in dict(paciencia=1, golpes=0, vida_vista=0, multa=0.5, dano_hostil=20, loja_raio=160,
                     nome_barra='Mercador').items():
        add(t['variables'], var(k, v), 'trader')
    est = acha_var(t['variables'], 'estado')
    if est['value'] == 'patrulha':
        est['value'] = 'calmo'
    else:
        print('trader.estado mantido:', est['value'])
    for k in ('vida', 'max_vida'):
        v = acha_var(t['variables'], k)
        if v['value'] == 10:
            v['value'] = VIDA_TRADER
        else:
            print(f'trader.{k} mantido: {v["value"]}')

    p = objeto(d, 'pato')
    for k, v in dict(na_loja=False, reaplicar_upgrades=False, velocidade_base=0, ultimo_agressor='',
                     moedas_perdidas=0).items():
        add(p['variables'], var(k, v), 'pato')
    add(objeto(d, 'projetil_inimigo')['variables'], var('origem', ''), 'projetil_inimigo')

    hub = cena(d, 'Hub')
    for k, v in dict(loja_aberta=False, loja_sel=0, loja_i=0, loja_x=80, loja_y=80, loja_largura=620, loja_linha_alt=56,
                     loja_cor_ok='255;255;255', loja_cor_caro='120;120;120', loja_cor_max='240;200;80',
                     loja_cor_bloq='200;80;80', loja_cor_sel='255;230;120').items():
        add(hub['variables'], var(k, v), 'Hub')

    def texto(nome, tamanho, alinhamento, string=''):
        if objeto(d, nome):
            return objeto(d, nome)
        o = copia_objeto(d, 'resumo_txt', nome, characterSize=tamanho, textAlignment=alinhamento, string=string)
        o['content'] = dict(o['content'], characterSize=tamanho, textAlignment=alinhamento, text=string)
        novos.append(f'objeto {nome}')
        return o

    if not objeto(d, 'loja_painel'):
        copia_objeto(d, 'resumo_fundo', 'loja_painel')
        novos.append('objeto loja_painel')
    linha = texto('loja_linha', 28, 'left')
    add(linha['variables'], var('indice', 0), 'loja_linha')
    texto('loja_desc', 24, 'left')
    texto('loja_dica', 28, 'center', 'E')

    salva(d)
    print('adicionado:', ', '.join(novos) or 'nada')


if __name__ == '__main__':
    main()
