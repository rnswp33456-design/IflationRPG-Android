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
