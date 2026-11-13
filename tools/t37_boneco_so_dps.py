"""Tarefa 37: o texto do boneco mostra só o DPS, e a vida do boneco é multiplicada por 100 (a partir do valor atual).
Rodar uma vez:  python3 tools/t37_boneco_so_dps.py   (feche o projeto no GDevelop antes)
"""
from migra import carrega, salva, acha_var, objeto, cena, anda

VELHO = ('"DPS " + ToString(round(boneco.dps_total / max(boneco.dps_tempo, boneco.dps_min_tempo)))'
         ' + "   total " + ToString(round(boneco.dps_total))')
NOVO = '"DPS " + ToString(round(boneco.dps_total / max(boneco.dps_tempo, boneco.dps_min_tempo)))'


def main():
    d = carrega()
    g = next(e for e in cena(d, 'Hub')['events'] if e.get('name') == 'Boneco de teste')
    acts = [a for e in anda([g]) for a in e.get('actions') or [] if a['parameters'][:1] == ['boneco_dps'] and VELHO in a['parameters']]
    if len(acts) != 1:
        raise SystemExit('texto do boneco não encontrado (ou já editado); nada alterado')
    acts[0]['parameters'][acts[0]['parameters'].index(VELHO)] = NOVO
    b = objeto(d, 'boneco')['variables']
    for k in ('vida', 'max_vida'):
        acha_var(b, k)['value'] *= 100
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
