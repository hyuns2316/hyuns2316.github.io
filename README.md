# 홈페이지 관리 안내

https://hyuns2316.github.io 의 소스입니다. Jekyll 테마는 [Minimal Light](https://github.com/yaoyao-liu/minimal-light)를 씁니다.

**핵심 원리**: 이 레포의 `main` 브랜치가 바뀌면 GitHub Pages가 1~2분 안에 사이트를 다시 만듭니다.
자동화는 직접 `main`을 고치지 않고 **Pull Request(PR)** 를 만들기만 합니다. PR을 **Merge**해야 사이트에 반영됩니다.

---

## 1. 무엇을 고치면 어디가 바뀌나

| 바꾸고 싶은 것 | 고칠 파일 |
|---|---|
| 이름, 직위, 소속, 이메일, 상단 링크(Scholar, CV, GitHub, LinkedIn) | `_config.yml` |
| About Me, Research Interests, News, Lectures | `index.md` |
| Publications 목록 | `_data/publications.yml` |
| 논문 썸네일 이미지 | `assets/img/` 에 업로드 (아래 3번 참고) |
| BibTeX 파일 | `assets/bib/` |
| CV 내용 | `cv/cv.tex` (PDF는 자동 생성, 아래 4번 참고) |
| 프로필 사진 | `assets/img/avatar.png` 를 같은 이름으로 교체 |
| 페이지 구조, 맨 아래 문구 | `_layouts/homepage.html` |

- 파일은 GitHub 웹에서 파일을 열고 연필(✏️) 버튼으로 바로 고칠 수 있습니다.
- 맨 아래 **Last updated** 날짜는 사이트가 다시 만들어질 때마다 자동으로 바뀝니다.
- News는 최신 5개만 보이고 나머지는 "Show more"로 접힙니다. 개수는 `_includes/news-collapse.html` 의 `NEWS_VISIBLE` 값입니다.

### Publications 항목 형식 (`_data/publications.yml`)

```yaml
  - title: "논문 제목"
    authors: Geunhu Lee, <strong>Hyunsoo Shin</strong>, Ji-Hun Bae & Sungon Lee
    conference_short: RA-L              # 썸네일 아래 뱃지
    conference: IEEE Robotics and Automation Letters, 2026.
    pdf: https://doi.org/...            # 제목과 PDF 버튼 링크
    bibtex: ./assets/bib/xxx.bib        # 없으면 비워 두기
    image: ./assets/img/xxx.gif
    notes: Oral Presentation            # 빨간 강조 문구, 없으면 비워 두기
```

위에 있을수록 먼저 보입니다. 최신 논문을 맨 위에 둡니다.

---

## 2. 새 논문 자동 감지 (ORCID 기준)

- **언제**: 매주 월요일 오전 9시경 (Actions 탭 → *Publication sync (ORCID)* → *Run workflow* 로 즉시 실행 가능)
- **무엇을**: ORCID(`0000-0003-1159-1582`)에 새로 생긴 논문을 찾아 PR을 만듭니다. PR에는 다음이 들어 있습니다.
  - `publications.yml` 맨 위에 초안 항목 (저자는 DOI로 자동 채움, 뱃지는 `TODO`, 썸네일은 예시 이미지)
  - `index.md` News에 한 줄 (날짜는 출판 월 기준)
  - `cv/cv.tex` 의 International Journal 또는 Domestic Journal 맨 위에 한 줄
- **할 일**: PR의 *Files changed* 에서 `conference_short: "TODO"` 를 뱃지 이름으로 바꾸고, News 날짜를 채택 월로 고친 뒤 Merge.
- **전제**: ORCID에 논문이 올라와 있어야 합니다. ORCID 설정에서 Crossref 자동 업데이트를 켜 두면 DOI 있는 논문은 자동으로 들어갑니다.
- **이미 처리한 논문 목록**: `_data/scholar_seen.yml`. 여기 있는 제목은 다시 제안되지 않습니다. 줄을 지우면 다음 실행 때 다시 제안됩니다.
- 기존 항목을 지우거나 고치는 기능은 없습니다. ORCID에 없는 논문도 사이트에 그대로 남습니다.
- 프리프린트는 자동으로 제외합니다.

## 3. 썸네일 자동 연결

- `assets/img/` 에 이미지(png, jpg, gif, webp)를 **업로드만** 하면 됩니다.
- 썸네일이 아직 예시 이미지인 논문에 자동으로 연결하는 PR이 만들어집니다.
- 짝을 찾는 방법: 파일 이름의 단어가 논문 제목 단어의 앞부분과 맞으면 연결합니다 (예: `cor_sel.png` → **Cor**respondence **Sel**ection). 이름이 안 맞아도 남은 논문과 이미지가 각각 하나뿐이면 둘을 연결합니다.
- PR에서 짝이 맞는지 확인하고 Merge. 틀렸으면 `image:` 줄을 고치면 됩니다.

## 4. CV 자동 빌드

- CV 원본은 `cv/cv.tex` (양식 파일 `cv/res.cls`) 입니다.
- `cv/` 안의 파일이 바뀌어 `main`에 반영되면, PDF를 자동으로 컴파일해서 `assets/files/cv.pdf` 로 올립니다 (Actions → *Build CV*).
- 상단 CV 링크는 항상 `assets/files/cv.pdf` 를 가리키므로, 해가 바뀌어도 링크를 고칠 필요가 없습니다.
- CV 양식을 바꿔도 `\section{\sc International Journal}`, `\section{\sc Domestic Journal}` 제목을 유지하면 새 논문 자동 추가가 계속 동작합니다.

---

## 5. 파일 구조

```
_config.yml                  이름·소속·링크 등 기본 정보
index.md                     About Me, Research Interests, News, Lectures
_data/publications.yml       Publications 목록
_data/scholar_seen.yml       자동화가 이미 처리한 논문 제목
_includes/publications.md    Publications 표시 형식
_includes/news-collapse.html News 접기 기능
_layouts/homepage.html       페이지 전체 틀
assets/img/  assets/bib/  assets/files/   이미지, BibTeX, CV PDF
cv/                          CV LaTeX 원본
scripts/scholar_sync.py      새 논문 감지 스크립트 (ORCID)
scripts/thumb_sync.py        썸네일 연결 스크립트
.github/workflows/           자동화 설정
  scholar-sync.yml           매주 ORCID 확인 → PR
  thumb-sync.yml             이미지 업로드 시 → PR
  cv-build.yml               cv/ 변경 시 → PDF 빌드
```

## 6. 문제가 생겼을 때

- **사이트가 안 바뀜**: PR을 Merge했는지 확인 → Actions 탭에서 *pages build and deployment* 가 초록색인지 확인 → 브라우저 새로고침(캐시).
- **Actions가 빨간색**: 해당 실행을 눌러 오류 메시지 확인. ORCID 서버 일시 장애라면 다음 주에 자동으로 다시 시도합니다.
- **자동화가 PR을 못 만듦**: Settings → Actions → General → *Allow GitHub Actions to create and approve pull requests* 가 켜져 있어야 합니다.
- **자동화를 끄고 싶음**: Actions 탭에서 해당 workflow 선택 → 오른쪽 위 `···` → *Disable workflow*.
