# Jetendard 베이스 폰트: non-Mono를 기본으로, `--mono`로 Mono 선택

- 작성일: 2026-07-13
- 갱신일: 2026-07-13 (구현 결과·실측 반영)
- 상태: 구현됨 (`feat/base-font-nonmono`)

> **설계 변경 고지:** 최초 설계는 "Mono → non-Mono 하드 교체"였고, 그 근거로
> "non-Mono는 넓은 아이콘에 2셀 advance를 갖는다"를 가정했다. 구현 단계에서 pinned
> 아카이브의 실제 파일을 열어보니 이 전제가 **거짓**임이 확인되어(아래 "실측으로
> 확인된 사실"), 설계를 다음과 같이 변경했다:
> (1) 하드 교체 대신 `--mono` 플래그로 두 베이스를 선택, (2) non-Mono를 기본값,
> (3) `isFixedPitch` 강제는 유지(제거하지 않음).

## 배경 / 문제

Nerd Fonts는 같은 폰트를 여러 변형으로 제공한다:

- `JetBrainsMonoNerdFontMono` (Mono): 모든 글리프를 1셀에 맞춰 아이콘을 축소.
- `JetBrainsMonoNerdFont` (non-Mono, Nerd Fonts 기본): 아이콘을 자연 크기로 유지.

Jetendard는 지금까지 Mono 변형만 썼기 때문에 아이콘이 텍스트 대비 작게(1셀에
욱여넣어져) 렌더링됐다. "아이콘을 크게" 보고 싶다는 요구에서 출발했다.

## 실측으로 확인된 사실 (설계 근거)

pinned 아카이브(nerd-fonts v3.4.0)의 실제 파일과 병합 산출물을 직접 열어 확인:

- **Mono·non-Mono 둘 다 모든 글리프의 advance가 1셀(600)이다.** advance가 2셀
  (1200)인 아이콘은 어느 변형에도 없다. → 최초 설계의 "non-Mono = 2셀 advance"
  전제는 거짓.
- Mono와 non-Mono의 실제 차이는 **글리프 아웃라인(잉크) 크기**다. non-Mono는
  아이콘을 자연 크기로 그려 1셀 박스를 오른쪽으로 넘긴다(예: fa-heart U+F004
  아웃라인 폭 Mono 599 → non-Mono 923, 셀의 약 1.54배). advance는 600으로 동일.
- 이는 Nerd Fonts 공식 동작과 일치한다: non-Mono는 "advance는 1셀로 두고 심볼이
  다음 셀로 넘치게" 하며, "다음 셀이 비어 있을 때만 보기 좋다".
- `post.isFixedPitch`: non-Mono=0, Mono=1. panose `bProportion`은 둘 다 9.
- `merge_fonts`는 기존 Latin/아이콘의 advance·아웃라인을 재작성하지 않으므로,
  non-Mono의 큰 아웃라인이 그대로 산출물까지 살아남는다(실측: 산출물 fa-heart
  아웃라인 923 유지).
- 사용자 주 환경 **Ghostty**는 자체 아이콘 렌더링을 적용해 Mono/non-Mono 차이가
  거의 보이지 않는다. 커진 아이콘은 advance를 존중하는 **Zed/VS Code**에서 나타난다.

## 설계 (구현됨)

### 1. `--mono` 플래그로 베이스 선택 (하드 교체 아님)

`src/jetendard/builder.py`의 `make_font_variant(weight, style, *, mono=False)`가
파일명 접두사를 선택한다:

```python
latin_base = "JetBrainsMonoNerdFontMono" if mono else "JetBrainsMonoNerdFont"
latin_filename = f"{latin_base}-{latin_suffix}.ttf"
```

- `mono=False`(기본) → non-Mono 베이스 (아이콘 풀사이즈)
- `mono=True` → Mono 베이스 (기존 동작, 아이콘 1셀 축소)

`mono` 키워드를 `get_variants_by_names` / `get_variants_by_weights_and_styles`
/ CLI `select_variants`까지 배선했고, CLI에 `--mono`(store_true) 인자를 추가했다.

### 2. monospace 분류 메타데이터: `isFixedPitch=1` 유지

`enforce_monospace_flags`(post.isFixedPitch=1, panose bProportion=9)를 **그대로
유지**한다.

- non-Mono도 아이콘 advance는 600으로 동일하고 잉크만 넘치므로, advance 그리드
  (Latin 600 / 한글 1200)는 두 베이스 모두 보존된다.
- Jetendard는 이미 한글을 1200 advance로 넣으며 `isFixedPitch=1`로 출하해 왔고,
  이와 일관된다. 편집기의 "monospace 폰트" 목록 노출에도 유리하다.
- (최초 설계 §2는 "업스트림 non-Mono가 0이니 `enforce_monospace_flags` 제거"를
  지시했으나, 위 근거로 유지 쪽으로 변경. 이것이 "만 바꾸면"이라는 최소 변경
  취지에도 부합 — 함수를 건드리지 않음.)

### 3. 다운로더: Mono·non-Mono 둘 다 추출

`--mono`가 "기존처럼" 동작하려면 Mono 파일도 있어야 하므로, `download_upstream.py`의
`jetbrains_expected_files()`가 두 세트(총 32개)를 모두 추출한다.

### 4. 테스트 / 문서

- 기본(non-Mono) 파일명 단언 갱신 + `mono` 플래그 커버리지(`test_builder`,
  `test_cli`).
- `README.md`/`README.ko.md`/`pyproject.toml`의 "Mono만 사용" 서술을 non-Mono
  기본 + `--mono` 옵션 + 아이콘 오버플로 트레이드오프로 정정.

## 검증 (구현 결과)

1. **산출물 실측(Regular):** non-Mono·Mono 각각 병합 후 —
   - 한글 `가` advance == ASCII `A` advance × 2 (양쪽 1200 = 600×2) ✓
   - fa-heart 아웃라인 폭: non-Mono 923(셀 1.54×) vs Mono 599(셀 안) — 아이콘
     확대의 실제 근거 ✓
   - `isFixedPitch` == 1, `ccmp`·`calt` 존재 ✓
2. **테스트:** `uv run pytest` 33 passed, 1 skipped(env-gated 전체 매트릭스).
   `ruff check`/`ruff format` 클린. (`ty`는 이 프로젝트에 미설정.)
3. **end-to-end CLI:** 기본·`--mono` 둘 다 ttf/otf/woff2/css 정상 생성.
4. **실사용 육안:** Ghostty는 자체 로직으로 차이 미미 → Zed/VS Code에서 확인.

## 범위 밖 (YAGNI)

- 아이콘 크기 커스터마이징 로직 — 하지 않음.
- 한글 스케일(1.15) 변경 — 하지 않음.
- (최초 설계는 "Mono/non-Mono 선택 CLI 옵션"을 YAGNI로 제외했으나, 사용자 요청으로
  `--mono` 플래그를 추가하는 것으로 변경.)

## 리스크 / 미결

- **Ghostty 렌더링:** non-Mono 전환 효과가 Ghostty에서는 제한적이다(자체 아이콘
  로직). 완료 기준은 "산출물 폰트가 non-Mono 아웃라인을 올바르게 담는다"이며 실측으로
  충족.
- **아이콘 오버플로:** non-Mono 아이콘은 Zed/VS Code에서 다음 셀로 넘쳐 인접 글자와
  겹칠 수 있다(다음 셀이 비어 있으면 문제없음). 기본값을 non-Mono로 두되 `--mono`로
  회피 가능.
- **전량 빌드 미수행:** 16변형 전체를 CLI로 빌드하진 않았다(Regular normal/italic
  통합 통과 + 16개 non-Mono 파일 존재 확인). 전량은
  `JETENDARD_RUN_FULL_INTEGRATION=1 uv run pytest`로 검증 가능.
