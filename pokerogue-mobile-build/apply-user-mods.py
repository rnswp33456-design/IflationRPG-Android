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


# 1) Every player starter costs exactly 1 point.
regex_once(
    "src/data/species-data-registry.ts",
    r"public getStarterCost\(speciesId: SpeciesId\): StarterCost \{.*?\n  \}",
    "public getStarterCost(_speciesId: SpeciesId): StarterCost {\n    return 1 as StarterCost;\n  }",
    re.S,
)

# 2) Eggs hatch at the next EggLapsePhase: one battle/wave after obtaining them.
replace_once(
    "src/overrides.ts",
    "readonly EGG_IMMEDIATE_HATCH_OVERRIDE: boolean = false;",
    "readonly EGG_IMMEDIATE_HATCH_OVERRIDE: boolean = true;",
)

# 3) Shop/reward luck grade starts at A (luck value 7), preserving anything higher.
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

# 4) Normal positive friendship gains x2. Rare Candy/item capped path is deliberately excluded.
replace_once(
    "src/field/pokemon.ts",
    "public addFriendship(friendship: number, capped = false): void {\n",
    "public addFriendship(friendship: number, capped = false): void {\n    if (friendship > 0 && !capped) {\n      friendship *= 2;\n    }\n",
)

# 5) Every voucher/ticket reward is doubled at the point it is awarded.
# This changes ticket acquisition, not voucher consumption or egg-gacha pull pricing.
replace_once(
    "src/modifier/modifier.ts",
    "voucherCounts[this.voucherType] += this.count;",
    "voucherCounts[this.voucherType] += this.count * 2;",
)

# 6) Every selected player starter begins with exactly one Mini Black Hole.
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

# 7) Classic-mode Eternatus only: remove every held item before battle setup.
rel = "src/phases/encounter-phase.ts"
text = read(rel)
anchor = "    enemyField.forEach((enemyPokemon, e) => {\n"
if anchor not in text:
    raise RuntimeError("encounter enemyField anchor missing")
cleanup = anchor + "      if (\n        enemyPokemon.species.speciesId === SpeciesId.ETERNATUS\n        && globalScene.gameMode.isBattleClassicFinalBoss(globalScene.currentBattle.waveIndex)\n      ) {\n        for (const heldItem of enemyPokemon.getHeldItems()) {\n          globalScene.removeModifier(heldItem, true);\n        }\n      }\n"
text = text.replace(anchor, cleanup, 1)
write(rel, text)
print(f"patched {rel}")

# 8) Classic Eternatus phase 2: remove all held items again and never create its Mini Black Hole.
rel = "src/battle-scene.ts"
text = read(rel)
pattern = r"\s*const finalBossMBH = getModifierType\(modifierTypes\.MINI_BLACK_HOLE\)\.newModifier\(\n\s*pokemon,\n\s*\) as TurnHeldItemTransferModifier;\n\s*finalBossMBH\.setTransferrableFalse\(\);\n\s*this\.addEnemyModifier\(finalBossMBH, false, true\);"
replacement = "\n      for (const heldItem of pokemon.getHeldItems()) {\n        this.removeModifier(heldItem, true);\n      }"
text2, n = re.subn(pattern, replacement, text, count=1)
if n != 1:
    raise RuntimeError(f"final boss MBH block expected 1 match, got {n}")
write(rel, text2)
print(f"patched {rel}")

print("ALL FINAL USER MODS APPLIED")
