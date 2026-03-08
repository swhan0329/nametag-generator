# Nametag Generator

`.xlsx` 파일을 입력으로 받아 A4 출력용 네임태그 PDF를 만드는 오픈소스 도구입니다.

영문 문서: [README.md](README.md)

릴리스 버전: `0.1.0`

`Nametag Generator`는 행사 운영자가 디자인 툴을 따로 열지 않고도, 스프레드시트에서 실제 출력 가능한 네임태그 PDF까지 빠르게 만들 수 있도록 설계되었습니다. 현재 포함된 기능은 다음과 같습니다.

- 공통 Python 렌더링 코어
- 배치 생성용 CLI
- 업로드, 미리보기, PDF 생성을 지원하는 로컬 웹 UI
- 공개 가능한 더미 샘플 데이터
- 실제 카드 규격에 맞춘 mm 기반 레이아웃 계산

## 주요 특징

- `93mm × 122mm` 같은 실제 카드 규격 기준 출력
- CLI와 웹 UI가 같은 렌더링 엔진을 사용
- 영어 기본, 한국어 전체 페이지 전환 지원
- 역할 바 설정 확장 지원:
  기본 `SPEAKER + STAFF`, 필요 시 최대 6개까지 추가
- 가상의 미국식 이름/회사명을 사용한 공개용 샘플 워크북 제공

## 0.1.0 포함 내용

`0.1.0` 릴리스에는 다음이 포함됩니다.

- `src/nametag_generator/` 기반 패키지 구조
- CLI PDF 생성 기능
- 브라우저 미리보기를 지원하는 로컬 웹 UI
- 역할 라벨/색상 편집 기능
- 최대 6개까지 확장 가능한 role row UI
- 샘플 워크북과 샘플 PDF
- 로더, 레이아웃, 렌더링, CLI, UI 테스트

릴리스 변경 사항은 [CHANGELOG.md](CHANGELOG.md)에서 확인할 수 있습니다.

## 입력 스키마

필수 컬럼:

- `name`
- `organization`

선택 컬럼:

- `role`
- `title`

주로 사용하는 역할 값:

- `ATTENDEE` 또는 빈 값: 역할 바 없음
- `HOST`
- `SPEAKER`
- `STAFF`

`role` 컬럼이 비어 있거나 아예 없어도 일반 이름표로 생성됩니다.

## 빠른 시작

```bash
python3 -m pip install -e ".[dev]"
python3 -m nametag_generator generate sample/attendees.sample.xlsx --output sample/badges.sample.pdf
```

## CLI 사용법

워크북에서 바로 PDF를 생성하려면:

```bash
python3 -m nametag_generator generate sample/attendees.sample.xlsx --output output/pdf/nametags.pdf
```

`pip install -e .` 후에는 설치된 커맨드로도 실행할 수 있습니다.

```bash
nametag-generator generate sample/attendees.sample.xlsx --output output/pdf/nametags.pdf
```

## 로컬 웹 UI 실행

```bash
PYTHONPATH=src python3 -m nametag_generator web --host 127.0.0.1 --port 8123
```

브라우저에서 [http://127.0.0.1:8123](http://127.0.0.1:8123) 를 열면 됩니다.

웹 UI에서 가능한 작업:

- 워크북 업로드
- 브라우저에서 생성 전 미리보기
- 영어/한국어 전환
- 역할 라벨/색상 편집
- 기본 `SPEAKER + STAFF`에서 시작해 최대 6개까지 role row 추가
- 샘플 워크북 / 샘플 PDF 다운로드

## 실측 출력

기본 카드 규격은 `93mm × 122mm`입니다.

실제 출력 크기를 확인하려면:

1. PDF를 생성합니다.
2. 프린터 설정에서 `100%` 또는 `Actual Size`로 출력합니다.
3. 자로 카드 한 장을 측정합니다.
4. `93mm × 122mm`와 일치하는지 확인합니다.

## 샘플 파일

공개용 샘플 자산:

- [attendees.sample.xlsx](sample/attendees.sample.xlsx)
- [badges.sample.pdf](sample/badges.sample.pdf)

샘플 워크북은 저장소를 공개해도 안전하도록 가상의 미국식 이름과 회사명만 사용합니다.

## 프로젝트 구조

```text
sample/                     더미 워크북과 샘플 결과물
src/nametag_generator/      공통 로더, 레이아웃, 렌더, CLI, 웹 UI 코드
tests/                      로더, 레이아웃, 렌더링, CLI, UI 테스트
ui/                         UI 관련 메모
```

## 개발

현재 회귀 테스트 실행:

```bash
python3 -m pytest tests/test_web_ui.py tests/test_cli.py tests/test_render_smoke.py tests/test_loader.py -q
```

## 라이선스

MIT 라이선스입니다. 자세한 내용은 [LICENSE](LICENSE)를 참고하세요.
