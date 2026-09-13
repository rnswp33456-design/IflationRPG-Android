from pathlib import Path
import re

root = Path("/tmp/IflationRPG")

# Default/fallback language -> Korean
targets = [
    root / "src/types/saveData.ts",
    root / "src/stores/gameStore.ts",
    root / "src/components/SettingsModal.tsx",
    root / "src/data/languageData.ts",
    root / "src/data/names.ts",
    root / "src/data/equipmentNames.ts",
    root / "src/data/equipmentDescriptions.ts",
]
replacements = {
    "language: 'zh-Hans'": "language: 'ko'",
    "saveData.language || 'zh-Hans'": "saveData.language || 'ko'",
    "lang.name['zh-Hans']": "lang.name['ko']",
    "ko: '닫는다'": "ko: '닫기'",
    "ko: '스테이터스'": "ko: '능력치'",
    "ko: 'Bonus'": "ko: '보너스'",
    "ko: 'Money'": "ko: '골드'",
    "ko: 'LEVEL UP!'": "ko: '레벨 업!'",
    "ko: '게임 스타트'": "ko: '게임 시작'",
    "ko: '옵션'": "ko: '설정'",
    "ko: '다시 하기'": "ko: '처음부터'",
    "ko: '캐릭터를 선택하십시오.'": "ko: '캐릭터를 선택해 주세요.'",
    "ko: '베이스 능력'": "ko: '기본 능력'",
    "ko: '베이스 능력와 캐릭터 능력의 합계가 높을\\n수록 스테이터스 수치에 배율 보너스가 가산됩니다'": "ko: '기본 능력과 캐릭터 능력의 합이 높을수록\\n능력치에 배율 보너스가 적용됩니다.'",
    "ko: '새로 획득한 장비 등은 게임 오버가되지 않으면 계승되지 않습니다\\n다시 하시겠습니까?'": "ko: '새로 획득한 장비는 게임 오버까지 진행해야 계승됩니다.\\n처음부터 다시 시작하시겠습니까?'",
    "ko: '레벨이 오르면 능력치를 강화하기 위한 스테이터스 포인트를 획득할 수 있습니다. 레벨이 오르면 곧바로 배분하세요!\\n플레이어의 능력치에 따라 연속 공격, 위기 히트가 작렬합니다.'": "ko: '레벨이 오르면 능력치를 올릴 수 있는 포인트를 획득합니다.\\n레벨업할 때마다 바로 분배해 주세요!\\n능력치에 따라 연속 공격과 치명타가 발동합니다.'",
    "ko: '슈퍼 패자·하드'": "ko: '슈퍼 패왕·하드'",
    "ko: '합성만'": "ko: '합성 전용'",
}
for p in targets:
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    for a,b in replacements.items():
        s = s.replace(a,b)
    p.write_text(s,encoding="utf-8")

# Build base path suitable for WebViewAssetLoader root.
vite = root / "vite.config.ts"
s = vite.read_text(encoding="utf-8")
s = s.replace("base: command === 'build' ? '/IflationRPG/' : '/',", "base: '/',")
vite.write_text(s,encoding="utf-8")

# Use one dedicated image file per bossId.
enemy_map = root / "src/data/enemyImageMap.ts"
s = enemy_map.read_text(encoding="utf-8")
old = """export const getBossImageUrl = (bossId: number, difficulty: number = 0): string | undefined => {
  const difficultyMap = BOSS_IMAGE_MAP[bossId];
  if (!difficultyMap) return undefined;
  const imageName = difficultyMap[difficulty] || difficultyMap[0];
  if (!imageName) return undefined;
  return imageFileMap[imageName];
};"""
new = """export const getBossImageUrl = (bossId: number, difficulty: number = 0): string | undefined => {
  return \`/images/enemies/boss_fem_\${bossId}.png\`;
};"""
if old not in s:
    raise RuntimeError("getBossImageUrl block not found")
s = s.replace(old, new)
enemy_map.write_text(s, encoding="utf-8")

# Boss battles: show the boss image as a full-screen battle background.
battle = root / "src/components/BattleScreen.tsx"
s = battle.read_text(encoding="utf-8")
anchor = "  const playerHpPercent = player.maxHp > 0 ? (player.hp / player.maxHp) * 100 : 0;\n"
if anchor not in s:
    raise RuntimeError("BattleScreen playerHpPercent anchor not found")
s = s.replace(anchor, anchor + "  const isBossBattle = Boolean(battle.enemy.imageUrl && battle.enemy.imageUrl.includes('/boss_fem_'));\n", 1)

bg_anchor = """        <div className="absolute inset-0 overflow-hidden">
          {/* 深空基底层 */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#020010] via-[#0a0520] to-[#060018]" />"""
bg_repl = """        <div className="absolute inset-0 overflow-hidden">
          {isBossBattle && battle.enemy.imageUrl && (
            <>
              <div
                className="absolute inset-0 z-0"
                style={{
                  backgroundImage: \`url("\${battle.enemy.imageUrl}")\`,
                  backgroundPosition: 'center center',
                  backgroundRepeat: 'no-repeat',
                  backgroundSize: 'contain',
                  imageRendering: 'pixelated',
                  transform: 'scale(1.18)',
                  transformOrigin: 'center center',
                }}
              />
              <div className="absolute inset-0 z-[1] bg-black/20" />
            </>
          )}
          {/* 深空基底层 */}
          <div className={\`absolute inset-0 bg-gradient-to-b from-[#020010] via-[#0a0520] to-[#060018] \${isBossBattle ? 'opacity-35' : ''}\`} />"""
if bg_anchor not in s:
    raise RuntimeError("BattleScreen background anchor not found")
s = s.replace(bg_anchor, bg_repl, 1)

small_img = """            {battle.enemy.imageUrl ? (
              <img 
                src={battle.enemy.imageUrl} 
                alt={battle.enemy.name}
                className="w-16 h-16 sm:w-24 sm:h-24 md:w-32 md:h-32 object-contain rounded-lg border-2 border-red-500/50 mx-auto"
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.style.display = 'none';
                  img.nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}"""
small_repl = """            {battle.enemy.imageUrl && !isBossBattle ? (
              <img 
                src={battle.enemy.imageUrl} 
                alt={battle.enemy.name}
                className="w-16 h-16 sm:w-24 sm:h-24 md:w-32 md:h-32 object-contain rounded-lg border-2 border-red-500/50 mx-auto"
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.style.display = 'none';
                  img.nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}"""
if small_img not in s:
    raise RuntimeError("BattleScreen enemy image block not found")
s = s.replace(small_img, small_repl, 1)

fallback = """            <div className={\`w-16 h-16 sm:w-24 sm:h-24 md:w-32 md:h-32 bg-[#3d2b6e] rounded-lg border-2 border-red-500 flex items-center justify-center mx-auto \${battle.enemy.imageUrl ? 'hidden' : ''}\`}>"""
fallback_repl = """            <div className={\`w-16 h-16 sm:w-24 sm:h-24 md:w-32 md:h-32 bg-[#3d2b6e] rounded-lg border-2 border-red-500 flex items-center justify-center mx-auto \${battle.enemy.imageUrl || isBossBattle ? 'hidden' : ''}\`}>"""
if fallback not in s:
    raise RuntimeError("BattleScreen fallback block not found")
s = s.replace(fallback, fallback_repl, 1)

battle.write_text(s, encoding="utf-8")
