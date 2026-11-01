# KB자동중문 블로그 준비

대상은 **KB자동중문 / 네이버 autodoorshop**, 브랜치는 **kb-autodoor**다. 중문매니저 main·금강이지스 geumgang-aegis와 각각 다른 폴더로 받는다.

```sh
git clone --single-branch --branch kb-autodoor https://github.com/Jason-hub-star/blog.git blog-kb
cd blog-kb
```

이미 받은 KB 폴더는 `git branch --show-current`가 kb-autodoor인지 확인하고 `git pull --ff-only`로 갱신한다.

## 사진을 받으면

**[사진받기 안내](사진받기_안내.md)**와 **[세 브랜드 공통 분리 가이드](templates/blog-photo-intake/README.md)**를 따른다. 빈 `templates/blog-photo-intake/새현장` 폴더를 `사진접수/수신일_지역_현장별칭_문종류`로 복사해 전·후·확인필요·영상·참고자료로 원본을 보관한다. 현장메모만 작성하면 에이전트가 사진목록과 제작 배치를 이어받는다. 다른 브랜드와 같은 접수 양식이며 글의 디자인·서식은 KB에 맞춰 별도로 정한다.

이 브랜치는 **사진 수신 전 안내·빈 양식·로고 참고 원본**을 공유한다. KB 전용 렌더러·브라우저 업로드·초안 저장복원은 아직 구현/실증 전이다. 다른 두 브랜드의 제작 성공을 KB 성공으로 기록하지 않는다. 현재 Python 설치나 자동 생성 명령을 실행할 필요는 없다.

사용 허용된 로고 참고 원본은 [assets/brand](assets/brand/README.md)에 있다. 기존 배너·현장 사진·영상·메모·실제 사진목록·로그인 정보·로컬 분석은 Git에 포함하지 않는다. 필요한 현장 자료는 별도로 전달하며 공개 발행·통화는 자동 후속으로 하지 않는다.

Claude/Codex는 `AGENTS.md` → `STATUS.md` → 사진받기 안내 → 해당 접수 폴더 순서로 읽는다. 아직 KB 제작 성공패턴 스킬을 새로 설치하지 않았다.
