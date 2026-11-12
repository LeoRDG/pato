"""Tarefa 10 (KAN-31): perks das armas (recarga ativa da pistola, pulo de recuo da doze, giro e ventilação da minigun)."""
import copy, uuid
from gd import *

d = load()
N = lambda n, v=0: {"name": n, "type": "number", "value": v}
Bo = lambda n: {"name": n, "type": "boolean", "value": False}
d['variables'].append(N('bonus_pente', 1))
obj(d, 'pistola')['variables'] += [N('recarga_atual'), Bo('perfeita')]
obj(d, 'minigun')['variables'] += [N('cooldown_up'), N('resfriamento'), Bo('ventilando')]
jan = copy.deepcopy(obj(d, 'laser'))
jan.update(name='hud_janela', persistentUuid=str(uuid.uuid4()), fillOpacity=200, fillColor={"r": 255, "g": 220, "b": 80}, outlineSize=0)
d['objects'].append(jan)
folder(d, ['hud'])['children'].append({"objectName": "hud_janela"})

FB = "FireBullet::FireBullet"
perk = lambda p: C("BooleanVariable", f"perks.{p}", "True", "")
equip = lambda a: C("BooleanObjectVariable", a, "equipada", "True", "")
num = lambda a, op, b: C("BuiltinCommonInstructions::CompareNumbers", a, op, b)
recarregando = C(f"{FB}::IsReloadInProgress", "pistola", "FireBullet", "")
razao = "pistola.FireBullet::ReloadTimeLeft() / max(0.001, pistola.FireBullet::ReloadDuration())"
perfeita = lambda v: C("BooleanObjectVariable", "pistola", "perfeita", v, "")

# ---------- pistola: recarga ativa ----------
pistola = E([perk('pistola')], [], [
    # o R de novo na janela: a recarga termina no próximo passo da FireBullet (duração 0) e o pente sai com +25% de dano
    E([equip('pistola'), C("KeyFromTextJustPressed", "", '"r"'), recarregando, num(razao, ">=", "0.35"), num(razao, "<=", "0.55")],
      [C("SetNumberObjectVariable", "pistola", "recarga_atual", "=", "pistola.FireBullet::ReloadDuration()"),
       C(f"{FB}::SetReloadDuration", "pistola", "FireBullet", "0", ""),
       C("SetBooleanObjectVariable", "pistola", "perfeita", "True", ""), C("SetNumberVariable", "bonus_pente", "=", "1.25")]),
    E([perfeita("True"), C(f"{FB}::IsReloadInProgress", "pistola", "FireBullet", "", inv=True)],
      [C(f"{FB}::SetReloadDuration", "pistola", "FireBullet", "pistola.recarga_atual", ""),
       C("SetBooleanObjectVariable", "pistola", "perfeita", "False", "")]),
    # o bônus acaba quando o pente esvazia, numa recarga normal ou trocando de arma
    E([perfeita("False")], [], [
        E([recarregando], [C("SetNumberVariable", "bonus_pente", "=", "1")]),
        E([num("pistola.FireBullet::ShotsBeforeNextReload()", "<=", "0")], [C("SetNumberVariable", "bonus_pente", "=", "1")]),
        E([C("BooleanObjectVariable", "pistola", "equipada", "False", "")], [C("SetNumberVariable", "bonus_pente", "=", "1")])]),
    # marca da janela na barra de recarga (a barra enche da esquerda: 45% a 65% do tempo)
    E([equip('pistola'), recarregando, C("SceneInstancesCount", "", "hud_recarga_trilho", ">", "0")], [], [
        E([C("SceneInstancesCount", "", "hud_janela", "=", "0")], [C("Create", "", "hud_janela", "0", "0", '"HUD"'),
                                                                   C("ChangePlan", "hud_janela", "=", "1001")]),
        E([], [C("PrimitiveDrawing::Rectangle", "hud_janela",
                 "hud_recarga_trilho.X() + 0.45 * hud_recarga_trilho.Width()", "hud_recarga_trilho.Y()",
                 "hud_recarga_trilho.X() + 0.65 * hud_recarga_trilho.Width()", "hud_recarga_trilho.Y() + hud_recarga_trilho.Height()")])]),
])

# ---------- doze: pulo de recuo ----------
doze = E([perk('doze')], [], [
    E([equip('doze'), C(f"{FB}::HasJustFired", "doze", "FireBullet", ""), C("PlatformBehavior::IsOnFloor", "pato", "PlatformerObject", "", inv=True),
       num("alvo.Y()", ">", "pato.Y()")],
      [C("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed", "pato", "PlatformerObject", "=",
         "-min(700, 900 * sin(ToRad(AngleBetweenPositions(pato.CenterX(), pato.CenterY(), alvo.CenterX(), alvo.CenterY()))))")]),
])

# ---------- minigun: giro e ventilação ----------
giro = 'TimerElapsedTime("giro")'
minigun = E([perk('minigun')], [], [
    E([C("MouseButtonFromTextPressed", "", '"Left"', inv=True)], [C("ResetTimer", "", '"giro"')]),
    # o cooldown já com o upgrade de cadência (AplicarUpgrades roda no primeiro quadro)
    E([C("NumberObjectVariable", "minigun", "cooldown_up", "=", "0"), num("TimeFromStart()", ">", "0.2")],
      [C("SetNumberObjectVariable", "minigun", "cooldown_up", "=", "minigun.FireBullet::Cooldown()"),
       C("SetNumberObjectVariable", "minigun", "resfriamento", "=", "minigun.FireBullet::ExponentialCoolingRate()"),
       C(f"{FB}::SetHeatPerShot", "minigun", "FireBullet", "0.01", "")]),
    E([equip('minigun'), C("NumberObjectVariable", "minigun", "cooldown_up", ">", "0")],
      [C(f"{FB}::SetCooldown", "minigun", "FireBullet", f"minigun.cooldown_up * (3 - 2 * min(1, {giro}))", "")]),
    # soltar com o calor entre 85% e 100%: ventila (um quadro de resfriamento enorme zera o calor)
    E([C("BooleanObjectVariable", "minigun", "ventilando", "True", "")],
      [C(f"{FB}::SetExponentialCoolingRate", "minigun", "FireBullet", "minigun.resfriamento", ""),
       C("SetBooleanObjectVariable", "minigun", "ventilando", "False", "")]),
    E([equip('minigun'), C("MouseButtonFromTextReleased", "", '"Left"'),
       num("minigun.FireBullet::HeatLevel()", ">=", "0.85"), num("minigun.FireBullet::HeatLevel()", "<", "1")],
      [C(f"{FB}::SetExponentialCoolingRate", "minigun", "FireBullet", "1000000", ""),
       C("SetBooleanObjectVariable", "minigun", "ventilando", "True", "")]),
])

grp = find_group(ext(d, 'Jogador')['events'], 'Controle das Armas')
grp['events'] += [pistola, doze, minigun]

proj = find_group(ext(d, 'Combate')['events'], 'Projéteis')
hit = [e for e in proj['events'] if e['type'] == 'BuiltinCommonInstructions::ForEach'][0]
a = [a for a in hit['actions'] if a['parameters'][:2] == ['Inimigo', 'vida']][0]
assert a['parameters'][3] == "(projetil.dano + Random(38)) * GlobalVariable(mult_dano)"
a['parameters'][3] += " * GlobalVariable(bonus_pente)"
save(d)
