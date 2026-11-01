# 중문매니저 블로그 작업

사진 보정·하단 명조 로고·집 모양 PNG/GIF·모바일 원고·네이버 임시글 검증을 Mac과 Windows에서 재사용한다.

사진을 받아 처음 작업하시는 분은 **[아내분용 시작 안내](docs/아내_시작하기.md)**부터 읽습니다. 현장별 원본5~10장·메모·결과를 한 폴더에 모으는 방식입니다.

세 브랜드의 새 사진 접수는 **[공통 사진 분리 가이드](templates/blog-photo-intake/README.md)**를 사용합니다. 작업자는 `사진접수/현장`의 전·후·확인필요·영상·참고자료에 원본을 보관하고, 에이전트가 확인한 사본을 아래 기존 제작 구조로 연결합니다. Git에는 빈 양식만 있고 실제 접수 자료는 별도로 전달합니다.

## Windows 첫 실행

Git과 Python 3.10 이상을 설치한 PowerShell에서:

```powershell
git clone https://github.com/Jason-hub-star/blog.git
cd blog
py -3 scripts/setup.py
```

기존에 받은 폴더는 `git pull --ff-only` 후 `py -3 scripts/setup.py`를 다시 실행한다. 기존 `post.local.json`은 덮어쓰지 않는다. 가상환경 활성화나 PowerShell 실행 정책 변경은 필요 없다.

1. `py -3 scripts/new_job.py "지역_아파트명"`으로 현장 폴더를 만든다. `현장작업/날짜_현장명/01_원본사진`에5~10장을 넣고 `현장메모.txt`를 작성한다. 제작할 때 JPG/JPEG/PNG를 파일명순으로 읽어 photo_001부터 번호를 붙인다. 스킬이 실제 사진 장수에 맞게 본문 이미지 블록을 조정한다.
2. 현장 폴더의 `post.local.json`에서 지역·제목·본문·사진 블록·썸네일·태그15개·상담 링크를 이번 현장에 맞춘다. 예시는 실제 시공 사실이나 고객 후기가 아니다. 사실을 확인한 뒤 `needs_authoring:false`로 바꾼다. 이 작업은 스킬에 맡길 수 있다.
3. 배너 파일이 있으면 `banner_file`에 경로를 적는다. 없으면 네이버 ‘내 템플릿’에서 마지막에 직접 삽입하고 링크를 검사한다.
4. 제작한다:

```powershell
.venv\Scripts\python.exe automation/build_assets.py --config "현장작업\날짜_현장명\post.local.json"
.venv\Scripts\python.exe automation/build_assets.py --config "현장작업\날짜_현장명\post.local.json" --check
```

현장 폴더 `03_작업결과`의 `모바일_미리보기.html`, 대표사진.png, 움직이는썸네일.gif, 보정사진, 본문_1800자.txt, 태그.txt를 확인한다. 배너 뒤에 `태그_붙여넣기.html`을 따로 붙인다. 모든 경로는 설정 파일 기준으로 해석하므로 같은 저장소 구조에서 쓸 수 있다. 루트 post.local.json/data/photos/runs/current 경로도 기존 작업 호환용으로 유지한다.

## Mac

```sh
python3 scripts/setup.py
python3 scripts/new_job.py "지역_아파트명"
.venv/bin/python automation/build_assets.py --config "현장작업/날짜_현장명/post.local.json"
```

이 Mac의 기존 현장/결과물은 원래 날짜 폴더에 보존했고 로컬 설정만 그 폴더를 가리킨다. 새 컴퓨터에는 현장 사진·배너를 별도로 복사해야 한다.

## Codex / Claude

이 저장소 폴더를 작업 폴더로 열고 `$jungmun-blog-production`을 사용한다. Claude는 `/jungmun-blog-production` 또는 스킬 이름을 지목한다.

- 실행 정본: `.claude/skills/jungmun-blog-production/SKILL.md`
- Codex 발견 경로: `.agents/skills/jungmun-blog-production/SKILL.md`가 정본을 읽도록 연결한다. Git 심볼릭 링크가 필요 없다.
- 저장소 `.agents/skills` 경로는 [OpenAI Docs](https://learn.chatgpt.com/docs/build-skills)의 로컬 스킬 발견 규칙에 따른다. 갱신한 스킬이 보이지 않으면 Codex를 다시 시작한다.
- 사진/원고 생성은 Python만으로 된다. 네이버 로그인·Chrome 프로필·브라우저 제어 연결은 각 컴퓨터에서 준비한다. Git으로 세션이나 로그인 정보를 이전하지 않는다.
- 이 세션의 cua_repl 보조 모듈은 `automation/browser_helpers.mjs`. 다른 에이전트의 GUI 도구가 동일 API를 제공한다고 가정하지 않는다. 사용 가능한 UI 도구로 같은 검증 순서를 수행한다.

## 검사 범위

```powershell
.venv\Scripts\python.exe scripts/check.py
```

Node.js는 JS 보조 모듈 검사에 사용한다. 게이트는0 통과/1 실패/2 도구 부재·시간 초과로 판정 못 함이다. `self_check.py`는 임시 폴더에 합성 사진7장을 만들어 한글/공백 경로·1800자·태그·폰트·PNG/GIF·원본 보존을 검사한다. `new_job.test.py`는5/10장 복사·덮어쓰기 차단·상대 배너경로·새 현장 작성 상태를 검사한다. 실제 현장 파일은 읽지 않는다. GitHub Actions에서 Windows와 Linux에 같은 검사를 실행한다.

Mac 한국어 Umji 초안의 업로드·저장복원은 검증됐다. Windows의 이미지/원고 생성과 운영체제 분기 검사는 CI 결과로 판정하고, Windows 네이버 실제 업로드·저장복원은 첫 현장에서 별도로 확인해야 한다. 전체10분은 아직 계측 전이다.

## 폴더

| 경로 | 역할 |
|---|---|
| automation/ | 제작/검증 코드 |
| .claude/skills/ | 스킬 정본 |
| .agents/skills/ | Codex 라우터 |
| harnesses/ | 성공 판정·목표 이어받기 |
| assets/fonts/ | 배포 가능한 한글 폰트와 OFL |
| docs/STATUS.md | 목표와 현재 상태 정본 |
| post.example.json | 공개 예시 설정 |
| 현장작업/, post.local.json, data/, runs/, 날짜 폴더 | 각 컴퓨터의 비공개 입력/결과, Git 제외 |

공개 저장소에는 코드·스킬·문서·폰트만 들어간다. 기존 개인 문서와 고객 사진은 루트 허용목록 방식의 .gitignore로 제외한다.
