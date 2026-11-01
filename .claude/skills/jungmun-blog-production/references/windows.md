# Windows / Mac 연결과 첫 현장 검증

## 로컬 제작

루트 README.md대로 setup.py를 실행한다. 코드·폰트·스킬은 Git으로 오지만 원본 사진·배너·로그인 세션은 각 컴퓨터의 로컬 자산이다. 경로는 post.local.json 기준이다. UTF-8/BOM 설정, 한글/공백 파일명, JPG/JPEG/PNG 대소문자를 지원한다.

## 브라우저 보조 모듈

이 모듈은 cua_repl의 ed/Chrome app 핸들을 받는 선택 도구다. 새 환경에서는 먼저 해당 도구의 문서를 읽고 정확한 블로그 탭과 앱 창을 연결한다. Windows app은 실제 관찰한 windowId로 연결한다. 다른 에이전트 도구를 이 API인 것처럼 사용하지 않는다.

```js
var helper = await import('<repo>/automation/browser_helpers.mjs');
var ops = helper.createNaverOps(ed, chromeApp, {platform: 'windows'});
// Mac에서는 platform: 'mac'
```

- 공통: 본문 구간 선택/붙여넣기·이미지 교체·읽기 DOM 검증.
- 복사: Mac super+c, Windows ctrl+c. 경로 구분자는 두 종류를 지원한다.
- Windows 파일창: 최신 AX에서 열기/Open 창과 파일 이름/File name 입력칸이 명시적으로 보일 때만 입력한다. 입력 후 새 AX로 열기 버튼 번호를 다시 읽는다. Mac의 setValue/slash를 Windows에 호출하지 않는다.
- 접근성 역할/언어가 다른 Windows 파일창은 기본 파서가 안전하게 중단할 수 있다. 실제 관찰한 UI로 `chooseFile` 콜백을 제공하거나 해당 환경의 허용 GUI 도구로 첨부한다. 선택자·좌표를 추측하지 않는다.

chooseFile 콜백은 `{path, name, platform, ed, app}`을 받는다. 해당 환경에서 실제로 관찰한 파일창 절차를 구현하고 파일을 선택한 뒤 반환한다. 기본 파서가 맞지 않으면 콜백 구현 또는 직접 첨부로 진행한다.

## 첫 실제 현장

1. 로그인된 정확한 Chrome/블로그/초안과 현재 원고·사진 상태를 읽는다.
2. 로컬에서 출력/검증한 PNG, GIF, 현장 사진을 붙이고 PNG만 대표로 선택한다.
3. 30굵게/16/단어 굵기/세 간격·배너 링크·배너 아래 태그15개를 확인한다. 본문1800자에는 태그를 합치지 않는다.
4. 저장→새로고침→불러오기 후 `verifyEditor(ed, 최신 config)`를 실행하고 스크린샷·JSON을 로컬 출력 폴더에 보존한다.

Windows/Linux CI는 생성 코드와 모의 핸들 계약을 검사한다. 로그인된 Windows 네이버 UI 실기를 대신하지 않는다. 실패한 단계/현재 UI를 기록하고 다음 현장에서 갱신한다.
