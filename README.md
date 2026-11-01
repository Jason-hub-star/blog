# 금강이지스 블로그 — 별도 브랜치

대상은 **금강이지스 / 네이버 artdoorstore**다. 같은 저장소의 `main`은 중문매니저이고 이 프로젝트는 `geumgang-aegis` 브랜치다. 작업 폴더를 따로 받는다.

새 사진은 **[공통 사진 분리 가이드](templates/blog-photo-intake/README.md)**대로 `사진접수/현장`의 전·후·확인필요·영상·참고자료에 나눕니다. 원본 보관과 기존 `현장작업`의 제작 사본을 구분하며, 다른 브랜드와 같은 빈 양식만 공유합니다.

## Windows 시작

Git, Python3.10 이상, Node.js를 준비한 PowerShell에서:

```powershell
git clone --single-branch --branch geumgang-aegis https://github.com/Jason-hub-star/blog.git blog-geumgang
cd blog-geumgang
py -3 scripts/setup.py
```

이미 받은 금강이지스 폴더는 `git branch --show-current`가 `geumgang-aegis`인지 확인하고 `git pull --ff-only`로 갱신한다. 중문매니저 작업 폴더에서 브랜치를 바꾸지 않는다.

자세한 이전·제작 순서는 [Windows 시작 안내](docs/Windows_시작하기.md)를 읽는다. Git에는 코드·프로젝트 스킬·제공 브랜드 자료·폰트·가상 예시가 있다. 현재 실제 현장·원고·후기 캡처는 별도 이전 묶음으로 옮긴다. 로그인 세션은 컴퓨터마다 준비한다.

## 에이전트 작업

이 폴더를 Codex/Claude에서 열고 **geumgang-aegis-blog-production** 스킬을 지정한다. Claude의 `.claude/skills`가 정본, Codex의 `.agents/skills`는 정본을 읽는 일반 파일 라우터다. Windows 심볼릭 링크 권한이 필요 없다. 공용 하네스에는 설치하지 않는다.

- 한 줄 요약 인용문19 / 본문15 / 소제목30 / 가운데 정렬 / 본문1500~1800자
- 확인된 시공 후 사진으로만900² PNG/GIF, 지정 로고와 #E99025·#248A76
- 전후는 왼쪽 전·오른쪽 후 네이티브 콜라주, 사용자 변경 보존
- 개별 후기마다 실제 캡처를 해당 설명 뒤에 배치하고 같은 상품 원문 연결
- 공식스토어→전화→카카오톡→인스타그램→태그15개

## 제작·검사

아래 명령에는 항상 `--job`을 명시합니다. 인자를 생략하면 기존 명지 현장을 찾으며, 새 clone에는 실제 고객 현장 자료가 없습니다. 새 현장은 setup의 가상 `새_현장`을 고유 이름으로 복사하고 실제 사진·메모·원본목록·전후/대표 근거·본문을 채운 뒤 제작합니다.

```powershell
.venv\Scripts\python.exe automation/build_post.py --job "현장작업\대상현장"
```

생성된 `02_제작물/썸네일_렌더.html`을 Chrome에서 열고 대표/배경/글자PNG 버튼으로 각각 저장한다. 파일명은 `대표사진.png`, `썸네일_배경.png`, `썸네일_글자.png`로 맞춘다. GIF 생성에는 FFmpeg를 설치하고 `ffmpeg -version`으로 PATH를 확인한다.

```powershell
.venv\Scripts\python.exe automation/build_post.py --job "현장작업\대상현장" --animate
.venv\Scripts\python.exe automation/build_post.py --job "현장작업\대상현장" --check
.venv\Scripts\python.exe scripts/check.py
```

Mac에서는 `py -3` 대신 `python3`, `.venv\Scripts\python.exe` 대신 `.venv/bin/python`을 쓴다. `scripts/check.py`는 고객 자료가 없는 합성 입력으로 UTF-8/BOM·한글/공백 경로·폰트 임베딩·세 GIF 효과·원본 불변·브랜드 가드·가상 편집기 계약을 검사한다. 실제 현장3편이 로컬에 있으면 `node automation/check_editor_verifier.mjs`로 저장DOM30회귀 검사도 실행할 수 있다.

GitHub Actions는 Windows/Linux에서 같은 생성·검사를 실행한다. Windows 로그인 Chrome의 실제 업로드·네이버 임시저장/복원은 첫 작업에서 별도로 확인한다. Python/Node 검사만으로 UI 실기를 완료했다고 하지 않는다.

상태 정본은 [STATUS.md](STATUS.md), 브랜드 규칙은 [AGENTS.md](AGENTS.md), 실행 스킬은 [.claude/skills/geumgang-aegis-blog-production/SKILL.md](.claude/skills/geumgang-aegis-blog-production/SKILL.md)다.
