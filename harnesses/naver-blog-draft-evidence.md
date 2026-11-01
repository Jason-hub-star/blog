# 네이버 초안 성공 판정

[제작 스킬](../.claude/skills/jungmun-blog-production/SKILL.md)의 실행 절차와 [성공/실패 패턴](../.claude/skills/jungmun-blog-production/references/success-patterns.md)을 정본으로 사용한다.

입력 이벤트, 실제 표시, 임시저장, 새로고침 복원, 공개 목록 노출은 같은 증거가 아니다. Python 검사·CI가 실제 네이버 게시/저장 성공을 대신하지 않는다. 다른 OS에서는 같은 완료 기준으로 다시 관찰한다.

현재 검증 기준은 저장복원16조건이다. 본문1800자에는 배너 아래 태그15개를 합치지 않는다. 사용자 세 간격은 보존하고 사진 컴포넌트ID를 전후 대조한다. 로컬 게이트는 `python scripts/check.py`이며0 통과/1 실패/2 판정 불가다. 새 현장 인계는 `docs/아내_시작하기.md`를 사용한다.
