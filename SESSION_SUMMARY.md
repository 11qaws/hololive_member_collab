# HCAT Session Summary

> **목적:** 세션 초기화/모델 교체 시 빠른 재개를 위한 프로젝트 컨텍스트 기록
> **최종 업데이트:** 2026-06-23

---

## 프로젝트 개요

Hololive 멤버들의 크로스-출연(Collab)을 Holodex API로 감지하고, 멤버별 타임라인(page)에 자기 방송 + 콜라보 출연을 날짜별로 그룹화하여 보여주는 CLI + Web UI + GitHub Pages 정적 사이트.

### 핵심 데이터 흐름
```
Holodex API → 출연 데이터 → appearances/<handle>.json
                         → timeline/<handle>.json (자기 방송 + 콜라보 병합)
                         → build-site (정적 HTML)
                         ├─ index.html (멤버 목록)
                         └─ members/<handle>.html (멤버 상세 페이지)
```

---

## 멤버 구성 (총 82명)

| Branch | 인원 | 비고 |
|--------|------|------|
| EN | 20 | Myth 5, Council 5, Advent 4, Justice 4, 졸업(Amelia/Gura/Sana/Mumei/Fauna) |
| JP | 29 | 0기~6기, 졸업(Aqua/Shion/Kanata/Coco) 포함 |
| ID | 9 | 1기~3기 |
| DEV_IS | 12 | ReGLOSS 5 + 2기?명, 일부 channel_id 없음 |
| Official | 3 | hololive, hololiveenglish, hololiveindonesia |
| 기타 | 9 | Holostars 등 |
| **합계** | **82** | |

---

## 인프라/환경

- **API Key:** `e9a667d6-...` (data/config.json, .gitignore)
- **Rate Limit:** 80 req/min (GHA는 더 엄격), 429 시 Retry-After + exponential backoff
- **Python:** 3.10+, httpx 비동기
- **배포:** GitHub Pages (`https://11qaws.github.io/hololive_member_collab/`)
  - `main` 브랜치 root에 정적 파일 직접 커밋
  - GitHub Actions: scan.yml (주간 스캔 + 배포)
- **로컬 웹:** FastAPI + uvicorn (`web/app.py`)
- **CI 스킵:** 커밋 메시지에 `[skip ci]` 포함 시 Actions 생략

---

## 주요 데이터 파일

| 파일 | 설명 |
|------|------|
| `data/channels.json` | Holodex 채널 정보 (handle, channel_id, photo_url, channel_handle) |
| `data/config.json` | API key (gitignore) |
| `data/appearances/<handle>.json` | 출연(다른 채널에 나간) 데이터 |
| `data/timeline/<handle>.json` | 자기 방송 + 콜라보 병합 타임라인 |
| `data/unknowns.json` | 미식별 채널 목록 |
| `hcat/_member_data.py` | 멤버 정의 (handle, name, branch) |

---

## 완료된 작업

### 1. Holodex API 연동
- `hcat/holodex_client.py`: `get_channel_videos()`, `get_all_videos()`
- 429 재시도: `while True` + Retry-After 헤더 우선, 없으면 exponential backoff
- Holodex API key를 `data/config.json`에서 로드

### 2. 스캐너 (`hcat/scanner.py`)
- `scan` CLI: 멤버별/일괄 스캔, `--full` 플래그로 전체 기록 재스캔
- uploader map에 `hololiveenglish`/`hololiveindonesia` channel_id 수동 추가 (Social Blade/vidIQ 확인)
  - `hololiveenglish`: `UCotXwY6s8pWmuWd_snKYjhg`
  - `hololiveindonesia`: `UCfrWoRGlawPQDQxxeIDRP0Q`
- Fuwawa/Mococo: 같은 channel_id `UCt9H_RpQzhxzlyBxFqrdHqA` 공유 → POV/SOLO 타이틀 마커로 구분

### 3. 타임라인 (`hcat/timeline.py`)
- `timeline refresh` CLI: 자기 방송 + 콜라보를 날짜+content_key 기준으로 페어링
- 그룹 콜라보: 같은 날짜+제목의 여러 collab을 `sub_entries`로 묶음
- 페어 뷰: 같은 날짜+내용의 자기 방송과 그룹 콜라보를 좌우로 나란히 표시
- `refresh_timeline()` 안전장치: stream 0건 발견 시 기존 데이터 유지 (`--full` 없으면 덮어쓰지 않음)
- `fuwamoco_display()`: Fuwawa/Mococo 표시명 처리 함수

### 4. GitHub Pages 정적 사이트 (`hcat/sitegen.py`)
- `build-site` CLI: Jinja2 템플릿 → 정적 HTML 생성
- 모든 링크를 `href="members/<handle>.html"` 형식으로 변환
- 템플릿 변수: `member`, `timeline`, `partner_groups`, `top_partners`, `member_photos`, `fuwamoco_display`

### 5. 웹 UI (`web/app.py`)
- FastAPI + Jinja2
- `/member/<handle>` 동적 페이지
- `partner_groups`, `member_photos`, `fuwamoco_display` 동일하게 적용

### 6. EN 멤버 전체 스캔 완료 (2026-06-23)
- Myth 5명, Council 5명, Advent 4명, Justice 4명, 쌍둥이 2명
- 졸업 멤버(Amelia, Gura, Sana): 3개월 참가자로 스캔 완료
- 모두 `--full` 스캔 + `--full` 타임라인 완료 (데뷔 ~ 현재)

---

## UI/UX 변경사항

### 필터 UI (타임라인)
- 키워드 검색, 날짜 범위(From/To), 파트너 다중 선택
- 파트너 선택 드롭다운: Branch별 그룹화 (EN/ID/JP/DEV_IS) + 접이식
- 선택된 파트너: 드롭다운 위에 태그로 표시, 클릭 시 제거
- 드롭다운: 바깥 클릭 시 자동 닫힘 (blur/click-outside)
- 필터 결과 카운트: "Showing X of Y entries"
- 초기화 버튼

### 월 구분선
- 연한 가로선 + "YYYY년 M월" 레이블
- **이전** 월 entries 위에 표시 (첫 월에는 구분선 없음, 마지막 월 아래에 추가 구분선)

### 그룹 콜라보 카드
- 카드 전체 클릭 → sub-entry 슬라이드 다운 (기존 "▼ N videos" 버튼 제거)
- "N videos" 텍스트는 카드 body에 유지
- `▶` 화살표 표시 (열리면 `▼`로 90° 회전)
- sub-entry 왼쪽: 빨간 점 대신 **파트너 프로필 사진** (`member_photos` 맵에서 조회, 없으면 dot 폴백)

### FuwaMoco 표시 규칙
- 공유 채널(`@FUWAMOCOch`): POV/SOLO 아닌 일반 방송
- Fuwawa 솔로(POV/SOLO, partner_handle=fuwawa_abyssgard): `@FUWAmoco`
- Mococo 솔로(POV/SOLO, partner_handle=mococo_abyssgard): `@fuwaMOCO`
- 모든 멤버 페이지에서 위 규칙 동일 적용 (viewer 무관, partner_handle 기준)

### YouTube @handle 검증 (2026-06-23)
- 전체 82명 YouTube @handle 일괄 확인
- 5명 channel_handle 수정:
  | Handle | YouTube @handle | 사유 |
  |--------|-----------------|------|
  | `aniamelfissa` | `AnyaMelfissa` | "ani"→"Anya" 철자 차이 |
  | `nakiri_ayame` | `nakiriayame` | 언더바 제거 |
  | `moona_hoshinova` | `MoonaHoshinova` | 언더바 제거, CamelCase |
  | `vestia_zeta` | `vestiazeta` | 언더바 제거 |
  | `mizumiya_su` | `mizumiyasu` | 언더바 제거 |

---

## CLI 명령어

```bash
# 스캔
python cli.py scan <handle>              # 특정 멤버 스캔
python cli.py scan <handle> --full       # 전체 기록 재스캔 (API limit 주의)
python cli.py scan --all                 # 모든 멤버 스캔
python cli.py scan --all --full          # 모든 멤버 전체 재스캔

# 타임라인
python cli.py timeline refresh <handle>  # 타임라인 갱신
python cli.py timeline refresh --all     # 전체 갱신

# 사이트
python cli.py build-site                 # 정적 사이트 생성
```

---

## 커밋 규칙

- 커밋 메시지는 **한국어**로 작성
- `[skip ci]` 포함 시 GitHub Actions 건너뜀
- 배포는 `git push`로 main 브랜치에 직접

---

## 다음 작업 (미완료)

- [ ] ReGLOSS(DEV_IS) 및 기타 미스캔 멤버 스캔/타임라인
- [ ] 비 EN 멤버 타임라인 생성

## 알려진 이슈

- `otonosekanade`, `ichijouririka`, `juufuuteiraden`, `todorokihajime`, `izuki_michiru`, `hanazono_sayaka`, `kazeshiro_yuki`: channel_id 없음 (DEV_IS 일부)
- `harusaki_nodoka`: 자체 채널 없음 (holoAN 채널에서 활동), 2025년 9월 퇴사
- `friend_a`: 자체 채널 없음, 2024년 은퇴
