# 🎬 HCAT 사용 설명서
### Hololive Cross-Appearance Tracker — 홀로라이브 콜라보 추적기

---

## 📖 이게 뭐 하는 거예요?

HCAT는 홀로라이브 멤버들이 **다른 멤버 채널에 출연한 영상**(콜라보)을 자동으로 찾아주는 도구입니다.

예를 들어 **오로 크로니(ourokronii)** 가:
- 카엘라 채널에서 Subnautica 2를 같이 한 영상
- 모리 칼리오페 채널에서 마인크래프트 RP를 한 영상
- 홀로라이브 공식 채널에 나온 영상

이런 것들을 자동으로 찾아서 목록으로 보여줍니다.

---

## 📋 준비물

- **Windows / Mac / Linux** 컴퓨터
- **Python 3.10 이상** 설치되어 있어야 함
  - 설치 확인: 터미널(또는 명령 프롬프트, 파워쉘)에서 아래 명령어 입력
  - ```
    python --version
    ```
  - `Python 3.10.x` 또는 `3.11.x` 또는 `3.12.x` 라고 나오면 됨
  - "not found" 오류가 나면 https://www.python.org/downloads/ 에서 설치

---

## ⬇️ 1단계: 내 컴퓨터로 프로젝트 내려받기

### 방법 A — ZIP 파일로 받기 (초보자 추천)

1. https://github.com/11qaws/hololive_member_collab 에 접속
2. 초록색 **⬇ Code** 버튼 클릭
3. **Download ZIP** 클릭
4. 다운로드 받은 `hololive_member_collab-main.zip` 파일을 원하는 폴더에 압축 풀기
5. 압축을 풀면 `hololive_member_collab-main` 폴더가 생깁니다

### 방법 B — git clone (git 설치되어 있을 때)

```
git clone https://github.com/11qaws/hololive_member_collab.git
cd hololive_member_collab
```

---

## 💻 2단계: 터미널(명령 프롬프트) 열기

### Windows
- `hololive_member_collab-main` 폴더 안에서
- 폴더의 빈 공간에 마우스 우클릭 → **"터미널에서 열기"** (Windows 11)
- 또는 주소창에 `cmd` 입력 후 엔터

### Mac
- 폴더 안에서 우클릭 → **"New Terminal at Folder"**

### Linux
- 파일 관리자에서 폴더 안에 우클릭 → **"Open in Terminal"**

---

## 📦 3단계: 필요한 패키지 설치하기

터미널에 아래 명령어를 **그대로 복사 붙여넣기** 하고 엔터:

```
pip install -r requirements.txt
```

이 명령어는 이 프로그램이 동작하는 데 필요한 부품(Python 패키지)들을 자동으로 설치합니다.

> ⚠️ 혹시 **"pip is not recognized"** 오류가 나면 `pip` 대신 `pip3` 를 입력해 보세요:
> ```
> pip3 install -r requirements.txt
> ```

> ⚠️ **"externally managed"** 오류가 나면:
> ```
> pip install -r requirements.txt --break-system-packages
> ```

---

## 🔑 4단계: Holodex API 키 발급받기 (처음 한 번만)

이 도구는 Holodex API를 사용해서 콜라보 정보를 가져옵니다. API 키가 필요합니다.

### API 키 발급 단계

1. https://holodex.net 에 접속
2. 우측 상단의 **로그인** 버튼 클릭
3. GitHub / Twitter / Google 중 편한 방법으로 회원가입 또는 로그인
4. 로그인 후 우측 상단의 **프로필 아이콘** 클릭
5. **Account Settings** 클릭
6. **API Key** 항목에 있는 긴 문자열(예: `e9a667d6-...`)을 복사
7. 이 키는 나중에 사용할 것이므로 메모장에 임시 저장해 둠

### API 키를 프로그램에 저장

터미널에 아래 명령어를 입력하세요 (`여기에_API키` 부분을 복사한 키로 바꾸기):

```
python cli.py config --set holodex_api_key "여기에_API키_붙여넣기"
```

예시:
```
python cli.py config --set holodex_api_key "여기에_발급받은_API_키를_붙여넣으세요"
```

> 정상적으로 저장되면 `Set holodex_api_key = ...` 같은 메시지가 나옵니다.

---

## 🚀 5단계: 첫 번째 콜라보 검색 실행하기

이제 실제로 실행해 봅시다. 가장 먼저 **오로 크로니(ourokronii)** 의 콜라보를 검색해 보겠습니다.

터미널에 아래 명령어 입력:

```
python cli.py scan ourokronii
```

### 실행 결과 예시

```
Starting scan for @ourokronii [ALL channels] [recent 3mo] [source: Holodex API]

  Fetching collabs for @ourokronii (UCmbs8T6MWqUHP1tIQvSgKrg)... 1011 total, 83 after date filter
    → DETECTED: @ourokronii in @holoen_raorapanthera's "【Backrooms Cleanup Crew】PIZZATIME CLEAN!..."
    → DETECTED: @ourokronii in @irys's "【ENigmatic Recollection】HPO Has Awakened..."
    ... (여러 줄 계속) ...

Scan complete. 83 videos checked, 73 new appearances.
Total recorded for @ourokronii: 84
```

> ⏱ 보통 1~3초면 끝납니다.

---

## 👀 6단계: 결과 확인하기

### 검색된 콜라보 목록 보기

```
python cli.py show ourokronii
```

간단한 요약이 표시됩니다:
```
Appearances for @ourokronii: 84 total

  @hakosbaelz: 9 total (3 confirmed, 6 unreviewed, 0 rejected)
  @holoen_gigimurin: 9 total (0 confirmed, 9 unreviewed, 0 rejected)
  @mococo_abyssgard: 9 total (0 confirmed, 9 unreviewed, 0 rejected)
  @hololive: 6 total (0 confirmed, 4 unreviewed, 2 rejected)
  ...
```

### 상세 목록 보기

```
python cli.py show ourokronii --detail
```

각 영상의 제목과 URL까지 자세히 보여줍니다.

### 통계 보기

```
python cli.py stats
```

각 브랜치(EN, JP, ID, DEV_IS, Official)별 멤버 수와 출연 수를 요약해서 보여줍니다.

---

## 🌐 7단계: 웹 UI로 보기 (선택 사항)

터미널이 아니라 브라우저에서 예쁘게 보고 싶다면:

터미널에 입력:
```
python web/app.py
```

브라우저를 열고 주소창에 `http://localhost:8000` 입력

웹 UI에서는:
- ✅ **Confirm** 버튼: "이 출연은 진짜다!" 하고 확인
- ❌ **Reject** 버튼: "이건 콜라보가 아니야" 하고 제외
- 멤버별 필터링, 검색 가능

종료하려면 터미널에서 `Ctrl + C` 누름

---

## 🏠 8단계: 정적 사이트 생성 (GitHub Pages용)

```
python cli.py build-site
```

`_site/` 폴더에 HTML 파일들이 생성됩니다. 이 파일들을 GitHub Pages에 올리면 누구나 볼 수 있는 웹사이트가 됩니다.

---

## 🔄 9단계: 전체 멤버 한 번에 검색하기

### EN + Official 채널만 (약 20명, 10~20초 소요)

```
python cli.py scan --all --en-only
```

### 모든 멤버 (JP, ID 포함, 약 1분 소요)

```
python cli.py scan --all
```

> **원리 설명:** `--all` 옵션은 모든 멤버를 한꺼번에 검색합니다.
> 중복을 제거하고 처리하므로, 같은 영상이 여러 번 처리되지 않습니다.

---

## 🔧 기타 명령어

### 멤버 목록 보기

```
python cli.py members
```

등록된 모든 홀로라이브 멤버(총 82명)와 각각의 채널 정보를 보여줍니다.

### 발견된 미확인 @handles 보기

```
python cli.py unknowns
```

스캔 중 발견되었지만 아직 HCAT에 등록되지 않은 @handle들을 보여줍니다.
새로운 콜라보 파트너 발견에 유용합니다.

### 스캔 진행 상태 보기

```
python cli.py state
```

어느 채널까지 검색했는지 진행 상황을 보여줍니다.

### 특정 멤버 스캔 상태 초기화

```
python cli.py reset ourokronii
```

재스캔이 필요할 때 사용합니다.

---

## 🤖 GitHub Actions — 자동 스캔 설정 (선택 사항)

이 프로젝트는 **매주 일요일 자정**에 자동으로 전체 멤버를 스캔하고
GitHub Pages를 업데이트하도록 설정할 수 있습니다.

### 설정 방법

1. https://github.com/11qaws/hololive_member_collab/settings/secrets/actions 접속
2. **New repository secret** 클릭
3. 아래 정보 입력:
   - Name: `HOLODEX_API_KEY`
   - Secret: 아까 발급받은 API 키
4. **Add secret** 클릭

5. https://github.com/11qaws/hololive_member_collab/settings/pages 접속
6. **Source** 항목에서 **GitHub Actions** 선택

### 수동 실행

1. https://github.com/11qaws/hololive_member_collab/actions 접속
2. 왼쪽 메뉴에서 **Scan & Deploy** 클릭
3. **Run workflow** → **Run workflow** 클릭
4. 완료될 때까지 기다림 (보통 1~2분)
5. 잠시 후 GitHub Pages에서 결과 확인 가능

### GitHub Pages URL 예시

```
https://11qaws.github.io/hololive_member_collab/
```

---

## 📁 파일 구조 설명

```
hololive_member_collab/          ← 이 폴더
├── cli.py                       ← 실행 파일 (터미널에서 python cli.py 로 실행)
├── requirements.txt             ← 설치할 패키지 목록
├── MANUAL.md                    ← 이 파일 (사용 설명서)
├── .github/workflows/scan.yml   ← 자동 스캔 설정 파일
├── hcat/                        ← 프로그램 본체 (소스 코드)
│   ├── holodex_client.py        ← Holodex API 통신 담당
│   ├── scanner.py               ← 스캔 실행 엔진
│   ├── config.py                ← 설정 관리
│   ├── models.py                ← 데이터 구조 정의
│   ├── storage.py               ← 파일 저장/읽기
│   └── ... (기타 파일들)
├── web/                         ← 웹 UI
│   ├── app.py                   ← FastAPI 웹 서버
│   └── templates/               ← HTML 템플릿
├── data/                        ← 검색 결과 저장소
│   ├── channels.json            ← 멤버 정보
│   ├── config.json              ← 설정 (API 키 등)
│   ├── unknowns.json            ← 미확인 핸들 목록
│   └── appearances/             ← 멤버별 출연 기록
│       ├── ourokronii.json
│       ├── moricalliope.json
│       └── ...
└── _site/                       ← 정적 사이트 (build-site 시 생성)
```

---

## ❓ 자주 묻는 질문

### Q. "pip"가 뭔가요?
Python 패키지(부품)를 설치해 주는 프로그램입니다. Python 설치 시 자동으로 함께 설치됩니다.

### Q. "python"이라고 쳤는데 오류가 나요
Windows라면 `python` 대신 `python3` 또는 `py` 를 입력해 보세요.
또는 Python이 설치되지 않은 경우 https://www.python.org/downloads/ 에서 설치하세요.

### Q. 검색 결과가 너무 많아요
`--en-only` 옵션을 붙이면 EN + Official 채널만 검색합니다.
`--months 1` 옵션을 붙이면 최근 1개월만 검색합니다.

### Q. "Illegal Access" 오류가 나요
API 키가 없거나 잘못되었습니다. 4단계를 다시 확인하세요.

### Q. 웹 UI가 안 열려요
`http://localhost:8000` 을 주소창에 정확히 입력했는지 확인하세요.
터미널에 `python web/app.py` 실행 후 "Uvicorn running on http://0.0.0.0:8000" 메시지가 나왔는지 확인하세요.

### Q. GitHub Actions는 어떻게 동작하나요?
매주 일요일 자정에 자동 실행됩니다. 또는 GitHub 웹사이트에서 수동으로 실행할 수 있습니다 (위 9단계 참조).
자동 실행하려면 `HOLODEX_API_KEY` 시크릿을 GitHub 저장소에 등록해야 합니다.

---

## ⚙️ 고급 옵션 (잘 사용하지 않음)

### 검색할 기간 지정
```
python cli.py scan ourokronii --months 6   # 최근 6개월
python cli.py scan ourokronii --full       # 모든 기간
```

### yt-dlp 방식으로 검색 (Holodex보다 느림)
```
python cli.py scan ourokronii --source ytdlp
```

### Holodex + yt-dlp 결과 병합
```
python cli.py scan ourokronii --source both
```

### 특정 채널만 검색 (옵션은 scan보다 앞에)
```
python cli.py scan --en-only ourokronii
```
