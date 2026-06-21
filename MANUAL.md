# HCAT — Hololive Cross-Appearance Tracker

## 개요

HCAT는 홀로라이브 멤버들의 **크로스 출연(콜라보)**을 자동으로 감지하고 추적하는 도구입니다.
Holodex API를 주 데이터 소스로 사용하며, yt-dlp를 대체 수단으로 지원합니다.

---

## 설치

```bash
git clone https://github.com/11qaws/hololive_member_collab.git
cd hololive_member_collab
pip install -r requirements.txt
```

## 설정 (최초 1회)

### Holodex API 키 등록

1. https://holodex.net 에 접속하여 로그인
2. 우측 상단 아바타 → **Account Settings** → API Key 복사
3. 아래 명령어로 저장:

```bash
python cli.py config --set holodex_api_key "여기에_API_키_입력"
```

설정 확인:

```bash
python cli.py config --get
```

---

## 사용법

### 1. 멤버 목록 확인

```bash
python cli.py members
```

등록된 모든 멤버(JP/EN/ID/DEV_IS/Official)와 상태(active/graduated)를 표시합니다.

### 2. 콜라보 스캔

**단일 멤버 스캔 (권장):**

```bash
# 최근 3개월 (기본값)
python cli.py scan ourokronii

# 최근 N개월
python cli.py scan ourokronii --months 6

# 전체 기간
python cli.py scan ourokronii --full

# 특정 채널 그룹만
python cli.py scan ourokronii --en-only
```

**전체 멤버 스캔 (권장):**

```bash
# Holodex API로 EN + Official 전체 스캔
python cli.py scan --all --en-only

# 모든 멤버 (JP/ID 포함)
python cli.py scan --all
```

**데이터 소스 선택:**

```bash
# Holodex API (기본값, 빠름)
python cli.py scan ourokronii --source holodex

# yt-dlp (느리지만 description 전체 스캔)
python cli.py scan ourokronii --source ytdlp

# 둘 다 병합
python cli.py scan ourokronii --source both
```

### 3. 결과 확인

```bash
# 특정 멤버의 출연 목록
python cli.py show ourokronii

# 자세히 보기
python cli.py show ourokronii --detail
```

### 4. 통계

```bash
python cli.py stats
```

브랜치별, 멤버별 출연 수를 요약해서 보여줍니다.

### 5. 미확인 핸들

스캔 중 발견된 아직 등록되지 않은 @handle 목록입니다.  
새로운 콜라보 파트너를 발견하는 데 유용합니다.

```bash
python cli.py unknowns
python cli.py unknowns --detail
```

### 6. 스캔 상태 관리

```bash
# 스캔 진행 상황 확인
python cli.py state

# 특정 멤버의 스캔 상태 초기화 (재스캔 시)
python cli.py reset ourokronii
```

### 7. Web UI 실행

```bash
python web/app.py
# → http://localhost:8000
```

웹 브라우저에서 멤버별 출연 내역을 확인하고, confirm/reject 상태를 변경할 수 있습니다.

### 8. 정적 사이트 생성 (GitHub Pages)

```bash
python cli.py build-site
# → _site/ 디렉토리에 생성
```

---

## GitHub Actions (자동 스캔)

이 저장소는 **매주 일요일 자정**에 전체 멤버를 자동 스캔하고 GitHub Pages를 업데이트합니다.

### GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → **New repository secret**

| Name | Value |
|---|---|
| `HOLODEX_API_KEY` | Holodex API 키 |

### 수동 실행

GitHub 저장소 → Actions → **Scan & Deploy** → Run workflow

---

## 파일 구조

```
hololive_member_collab/
├── cli.py                    # CLI 진입점
├── requirements.txt          # Python 의존성
├── MANUAL.md                 # 사용 설명서
├── .github/workflows/scan.yml # GHA 워크플로우
├── hcat/
│   ├── __init__.py
│   ├── config.py             # 설정 관리
│   ├── holodex_client.py     # Holodex API 클라이언트
│   ├── models.py             # 데이터 모델 (Member, Appearance)
│   ├── storage.py            # JSON 파일 I/O
│   ├── detector.py           # description 텍스트 분석 (yt-dlp fallback)
│   ├── fetcher.py            # yt-dlp 비디오 수집
│   ├── scanner.py            # 스캔 오케스트레이션
│   ├── scraper.py            # 공식 사이트 멤버 목록 수집
│   └── sitegen.py            # 정적 사이트 생성
├── web/
│   ├── app.py                # FastAPI 웹 UI
│   └── templates/            # Jinja2 템플릿
└── data/
    ├── channels.json          # 멤버 DB
    ├── config.json            # 설정 (API 키 등)
    ├── unknowns.json          # 미확인 핸들
    └── appearances/           # 멤버별 출연 데이터
        ├── ourokronii.json
        └── ...
```

## 명령어 참조

| 명령어 | 설명 |
|--------|------|
| `members` | 멤버 목록 출력 |
| `scan <handle>` | 특정 멤버 콜라보 스캔 |
| `scan --all` | 전체 멤버 스캔 (Holodex 전용) |
| `show <handle>` | 출연 기록 조회 |
| `unknowns` | 미확인 @handle 목록 |
| `config` | 설정 조회/변경 |
| `stats` | 통계 요약 |
| `state` | 스캔 진행 상태 |
| `reset <handle>` | 스캔 상태 초기화 |
| `build-site` | GitHub Pages 사이트 생성 |

### scan 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--source {holodex, ytdlp, both}` | 데이터 소스 | `holodex` |
| `--full` | 전체 기간 스캔 | false |
| `--months N` | 최근 N개월 | config 설정값 (3) |
| `--count N` | 채널당 N개 비디오 | 없음 |
| `--en-only` | EN+Official만 | false |
| `--all` | 전체 멤버 스캔 | false |
