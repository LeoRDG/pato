"""Tarefa 219: o GDevelop acusava 405 "Invalid parameters in events" (Hubs, Loja, InimigosInferno, InimigosParaiso).

As estruturas globais das telas de atributos (t190: ui_card, ui_lin, stats_pato) estavam declaradas vazias e os filhos
só nasciam quando um evento os escrevia; o editor valida cada caminho de variável contra o que está declarado e marca
como inválido todo filho que não existe (ui_card.arma.x, ui_lin.arma.l0.rot, ui_lin.loja["l" + ...] etc.). Faltavam
também duas variáveis de objeto: demonio_chefe.socado e estrela_rastro.id.

Só ADICIONA declarações: cada caminho fixo que os eventos usam vira um filho declarado (texto se algum evento grava
texto nele, senão número), com o valor vazio que ele já tinha antes de ser escrito (0 ou ""), e ui_lin.loja vira uma
estrutura vazia (as linhas da loja são acessadas por colchetes). Nada que já existe muda. Os eventos continuam
escrevendo esses valores todo quadro, então o jogo se comporta igual.
Rodar uma vez:  python3 tools/t219_declara_variaveis_ui.py
"""
import re
from gd_mig import *

RAIZES = ('ui_card', 'ui_lin', 'stats_pato')
ESTRUTURAS_VAZIAS = [('ui_lin', 'loja')]
OBJ_VARS = [('demonio_chefe', 'socado', 0), ('estrela_rastro', 'id', 0)]
TEXTO = {'SetStringVariable', 'StringVariable'}


def caminhos(d):
    """{(raiz, filho, neto...): é_texto} para todo caminho fixo (sem colchetes) das RAIZES usado nos eventos."""
    achados = {}
    padrao = re.compile(r'\b(' + '|'.join(RAIZES) + r')((?:\.\w+)+)')

    def instrucoes(evs):
        for e in evs:
            for k in ('conditions', 'actions'):
                pilha = list(e.get(k, []))
                while pilha:
                    i = pilha.pop()
                    pilha += i.get('subInstructions', [])
                    yield i
            yield from instrucoes(e.get('events', []))

    for folha_ in d['externalEvents'] + d['layouts']:
        for i in instrucoes(folha_['events']):
            for j, p in enumerate(i.get('parameters', [])):
                for m in padrao.finditer(p or ''):
                    # caminho que continua com colchete depois (ui_lin.loja["l"...]) não é folha fixa
                    if p[m.end():m.end() + 1] == '[':
                        continue
                    partes = (m.group(1),) + tuple(m.group(2)[1:].split('.'))
                    texto = j == 0 and i['type']['value'] in TEXTO
                    achados[partes] = achados.get(partes, False) or texto
    return achados


def filho(lista, nome, dono, ids, valor=None):
    """o filho com esse nome; cria (estrutura se valor for None) se não existe."""
    for v in lista:
        if v['name'] == nome:
            return v
    if valor is None:
        novo = {'name': nome, 'persistentUuid': ids(f'var/{dono}/{nome}'), 'type': 'structure', 'children': []}
    else:
        novo = var(ids, dono, nome, valor)
    lista.append(novo)
    return novo


def migra(d):
    ids = Ids('t219')
    globais = {v['name']: v for v in d['variables']}
    folhas = caminhos(d)
    # um caminho que é prefixo de outro é estrutura, não folha
    prefixos = {c[:n] for c in folhas for n in range(1, len(c))}
    for c, texto in sorted(folhas.items()):
        if c in prefixos:
            continue
        no = globais[c[0]]
        assert no['type'] == 'structure', c
        for n, nome in enumerate(c[1:], start=1):
            dono = 'global/' + '/'.join(c[:n])
            ultimo = n == len(c) - 1
            no = filho(no['children'], nome, dono, ids, ('' if texto else 0) if ultimo else None)
            if not ultimo:
                assert no['type'] == 'structure', (c, nome)
    for raiz, nome in ESTRUTURAS_VAZIAS:
        filho(globais[raiz]['children'], nome, f'global/{raiz}', ids)
    for obj, nome, valor in OBJ_VARS:
        poe_vars(ids, objeto(d, obj).setdefault('variables', []), f'obj/{obj}', [(nome, valor)])


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'loja' for v in d['variables'] if v['name'] == 'ui_lin'
                              for c in v['children']), 't219')
