from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "upstream")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(rel, old, new):
    text = read(rel)
    if old not in text:
        raise RuntimeError(f"pattern not found in {rel}: {old[:120]!r}")
    text = text.replace(old, new, 1)
    write(rel, text)
    print(f"patched {rel}")


def regex_once(rel, pattern, repl, flags=0):
    text = read(rel)
    text2, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise RuntimeError(f"regex expected 1 match in {rel}, got {n}: {pattern}")
    write(rel, text2)
    print(f"patched {rel}")


# 1) Every starter costs exactly 1 point.
regex_once(
    "src/data/species-data-registry.ts",
    r"public getStarterCost\(speciesId: SpeciesId\): StarterCost \{.*?\n  \}",
    "public getStarterCost(_speciesId: SpeciesId): StarterCost {\n    return 1 as StarterCost;\n  }",
    re.S,
)

# 2) Every egg hatches on the next egg-lapse check (one battle/wave later).
replace_once(
    "src/overrides.ts",
    "readonly EGG_IMMEDIATE_HATCH_OVERRIDE: boolean = false;",
    "readonly EGG_IMMEDIATE_HATCH_OVERRIDE: boolean = true;",
)

# 3) Shop/reward luck grade starts at A (luck value 7), but higher luck is preserved.
replace_once(
    "src/modifier/modifier-type.ts",
    "return DailyLuck.value;",
    "return Math.max(7, DailyLuck.value);",
)
replace_once(
    "src/modifier/modifier-type.ts",
    "return Math.min(timedEventManager.getEventLuckBoost() + (luck ?? 0), 14);",
    "return Math.max(7, Math.min(timedEventManager.getEventLuckBoost() + (luck ?? 0), 14));",
)

# 4) Catch rate 100%: force modified catch rate to the guaranteed-capture threshold.
regex_once(
    "src/phases/attempt-capture-phase.ts",
    r"const modifiedCatchRate = Math\.round\(\n\s*\(\(\(_3m - _2h\).*?\n\s*\);",
    "const modifiedCatchRate = 255;",
    re.S,
)

# 5) Normal positive friendship gains x3. Rare Candy/item path uses capped=true and is deliberately excluded.
replace_once(
    "src/field/pokemon.ts",
    "public addFriendship(friendship: number, capped = false): void {\n",
    "public addFriendship(friendship: number, capped = false): void {\n    if (friendship > 0 && !capped) {\n      friendship *= 3;\n    }\n",
)

# 6) Egg-gacha ticket output x2 while voucher consumption stays unchanged.
rel = "src/ui/handlers/egg-gacha-ui-handler.ts"
text = read(rel)
repls = [
    ('description: `1 ${i18next.t("egg:pull")}`', 'description: `2 ${i18next.t("egg:pulls")}`'),
    ('description: `10 ${i18next.t("egg:pulls")}`', 'description: `20 ${i18next.t("egg:pulls")}`'),
    ('description: `5 ${i18next.t("egg:pulls")}`', 'description: `10 ${i18next.t("egg:pulls")}`'),
    ('description: `25 ${i18next.t("egg:pulls")}`', 'description: `50 ${i18next.t("egg:pulls")}`'),
]
for old, new in repls:
    if old not in text:
        raise RuntimeError(f"gacha UI pattern missing: {old}")
    text = text.replace(old, new)
functional = {
    "return [VoucherType.REGULAR, 1, 1];": "return [VoucherType.REGULAR, 1, 2];",
    "return [VoucherType.REGULAR, 10, 10];": "return [VoucherType.REGULAR, 10, 20];",
    "return [VoucherType.PLUS, 1, 5];": "return [VoucherType.PLUS, 1, 10];",
    "return [VoucherType.PREMIUM, 1, 10];": "return [VoucherType.PREMIUM, 1, 20];",
    "return [VoucherType.GOLDEN, 1, 25];": "return [VoucherType.GOLDEN, 1, 50];",
}
for old, new in functional.items():
    if old not in text:
        raise RuntimeError(f"gacha functional pattern missing: {old}")
    text = text.replace(old, new, 1)
text = text.replace("case 10:\n        return EggTier.RARE;", "case 20:\n        return EggTier.RARE;", 1)
text = text.replace("case 25:\n        return EggTier.EPIC;", "case 50:\n        return EggTier.EPIC;", 1)
write(rel, text)
print(f"patched {rel}")

# 7) Every selected starter begins with exactly one Mini Black Hole.
rel = "src/phases/select-starter-phase.ts"
text = read(rel)
if 'modifierTypes } from "#data/data-lists"' not in text:
    anchor = 'import { SpeciesFormChangeMoveLearnedTrigger } from "#data/form-change-triggers";\n'
    if anchor not in text:
        raise RuntimeError("select-starter import anchor missing")
    text = text.replace(anchor, 'import { modifierTypes } from "#data/data-lists";\n' + anchor, 1)
if 'getModifierType } from "#utils/modifier-utils"' not in text:
    anchor = 'import { applyChallenges } from "#utils/challenge-utils";\n'
    if anchor not in text:
        raise RuntimeError("select-starter utils import anchor missing")
    text = text.replace(anchor, anchor + 'import { getModifierType } from "#utils/modifier-utils";\n', 1)
anchor = "    overrideModifiers();\n    overrideHeldItems(party[0]);\n"
if anchor not in text:
    raise RuntimeError("select-starter modifier init anchor missing")
addition = anchor + "    for (const starterPokemon of party) {\n      const miniBlackHole = getModifierType(modifierTypes.MINI_BLACK_HOLE).newModifier(starterPokemon);\n      globalScene.addModifier(miniBlackHole, true, false, false, true);\n    }\n"
text = text.replace(anchor, addition, 1)
write(rel, text)
print(f"patched {rel}")

# 8) Classic-mode Eternatus starts with no held items.
rel = "src/phases/encounter-phase.ts"
text = read(rel)
anchor = "    enemyField.forEach((enemyPokemon, e) => {\n"
if anchor not in text:
    raise RuntimeError("encounter enemyField anchor missing")
cleanup = anchor + "      if (\n        enemyPokemon.species.speciesId === SpeciesId.ETERNATUS\n        && globalScene.gameMode.isBattleClassicFinalBoss(globalScene.currentBattle.waveIndex)\n      ) {\n        for (const heldItem of enemyPokemon.getHeldItems()) {\n          globalScene.removeModifier(heldItem, true);\n        }\n      }\n"
text = text.replace(anchor, cleanup, 1)
write(rel, text)
print(f"patched {rel}")

# 9) Classic Eternatus phase 2: remove all held items again and do not create Mini Black Hole.
rel = "src/battle-scene.ts"
text = read(rel)
pattern = r"\s*const finalBossMBH = getModifierType\(modifierTypes\.MINI_BLACK_HOLE\)\.newModifier\(\n\s*pokemon,\n\s*\) as TurnHeldItemTransferModifier;\n\s*finalBossMBH\.setTransferrableFalse\(\);\n\s*this\.addEnemyModifier\(finalBossMBH, false, true\);"
replacement = "\n      for (const heldItem of pokemon.getHeldItems()) {\n        this.removeModifier(heldItem, true);\n      }"
text2, n = re.subn(pattern, replacement, text, count=1)
if n != 1:
    raise RuntimeError(f"final boss MBH block expected 1 match, got {n}")
write(rel, text2)
print(f"patched {rel}")

print("ALL USER MODS APPLIED")
