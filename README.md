<div align="center">

# 🎬 HCAT — Hololive Cross-Appearance Tracker

**홀로라이브 멤버들의 콜라보 출연을 자동으로 감지하고 추적합니다**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Scan & Deploy](https://github.com/11qaws/hololive_member_collab/actions/workflows/scan.yml/badge.svg)](https://github.com/11qaws/hololive_member_collab/actions/workflows/scan.yml)

</div>

---

## ✨ 주요 기능

- **자동 콜라보 검출** — Holodex API로 특정 멤버가 다른 채널에 출연한 영상을 자동으로 찾습니다
- **전체 멤버 지원** — JP, EN, ID, DEV_IS, Official 포함 80+ 멤버
- **졸업 멤버 포함** — Mumei, Sana, Aqua, Coco 등 졸업/종료 멤버도 추적
- **빠른 검색 속도** — Holodex API 기반, 전체 EN 스캔이 10~20초면 완료
- **중복 제거** — 같은 영상에 여러 멤버가 언급되어도 한 번만 처리
- **웹 UI** — FastAPI 기반 로컬 웹 인터페이스 (confirm/reject 기능)
- **GitHub Pages 지원** — 정적 사이트 자동 생성 및 배포
- **자동 스캔** — GitHub Actions로 매주 정기 업데이트 가능

---

## 🚀 빠른 시작

```bash
# 1. 프로젝트 내려받기
git clone https://github.com/11qaws/hololive_member_collab.git
cd hololive_member_collab

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Holodex API 키 설정 (https://holodex.net → Account Settings)
python cli.py config --set holodex_api_key "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

# 4. 콜라보 검색 실행
python cli.py scan ourokronii

# 5. 결과 확인
python cli.py show ourokronii --detail
```

> 📖 **자세한 설명은 [MANUAL.md](MANUAL.md)를 참고하세요.** (초보자용 상세 가이드 포함)

---

## 📊 최근 스캔 결과

| 구분 | 검출 수 | 소요 시간 |
|------|---------|----------|
| EN + Official (20명) | **1,314개** 출연 | ~15초 |
| Kronii 단일 | **84개** 출연 | ~2초 |

---

## 🧩 구성

```
📦 hololive_member_collab
 ├── cli.py              # CLI 진입점
 ├── hcat/               # 코어 엔진
 │   ├── holodex_client  # Holodex API 클라이언트
 │   ├── scanner         # 스캔 오케스트레이션
 │   ├── detector        # description 텍스트 분석 (fallback)
 │   └── ...
 ├── web/                # FastAPI 웹 UI
 └── data/               # 검색 결과 (JSON)
```

---

## 🖥️ 사용 예시

```bash
# 멤버 목록 보기
python cli.py members

# 단일 멤버 스캔 (최근 3개월)
python cli.py scan ourokronii

# 전체 EN 멤버 스캔
python cli.py scan --all --en-only

# 웹 UI 실행
python web/app.py
# → http://localhost:8000
```

---

## 🤖 자동화 (GitHub Actions)

1. GitHub 저장소에 `HOLODEX_API_KEY` [시크릿 등록](https://github.com/11qaws/hololive_member_collab/settings/secrets/actions)
2. [GitHub Pages](https://github.com/11qaws/hololive_member_collab/settings/pages)를 **GitHub Actions** 소스로 설정
3. 매주 일요일 자정에 자동 스캔 + Pages 배포

---

## 📝 라이선스

MIT License — 자유롭게 사용, 수정, 배포하세요.
