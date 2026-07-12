# Jetendard 베이스 폰트를 non-Mono로 교체

- 작성일: 2026-07-13
- 상태: 설계 승인됨 (구현 대기)

## 배경 / 문제

Jetendard는 `JetBrainsMono Nerd Font **Mono**` 변형을 Latin/기호 베이스로 사용한다.
Nerd Fonts의 "Mono" 변형은 모든 아이콘 글리프를 1셀 폭(advance width = 1 cell)에
욱여넣도록 축소한다. 그 결과 기호(Nerd Font 아이콘)가 텍스트 대비 "절반 크기"로
작게 렌더링된다.

`JetBrainsMono Nerd Font`(non-Mono) 변형은 넓은 아이콘 글리프에 2셀 폭
(advance width = 2 cells)을 허용하므로 아이콘이 원래 크기로 렌더링된다.
Latin 텍스트 글리프는 두 변형 모두 고정폭(1셀)으로 동일하다.

**목표:** 산출물 폰트의 베이스를 `JetBrainsMono Nerd Font Mono` →
`JetBrainsMono Nerd Font`(non-Mono)로 교체하여, 아이콘이 2셀 풀사이즈로
렌더링되게 한다. Latin은 1셀 고정폭, 한글/CJK는 기존과 동일하게 2셀(full-width)을
유지한다.

## 핵심 사실 (설계 근거)

- 아이콘 크기는 **글리프의 advance width**로 결정된다. non-Mono 소스는 넓은 아이콘에
  2셀 advance를 갖는다.
- `merge_fonts`는 **기존 Latin/아이콘 글리프의 advance를 재작성하지 않는다.**
  (한글/CJK 글리프만 새로 추가·설정) 따라서 소스를 non-Mono로 바꾸면 2셀 아이콘
  advance가 그대로 산출물까지 살아남는다.
- `isFixedPitch` / OS/2 panose `bProportion`은 아이콘 크기가 아니라 폰트를
  **monospace로 분류할지**를 나타내는 힌트다. 아이콘 렌더 크기와 직접 관계없다.
- `derive_latin_advance`는 ASCII 샘플 `" A0Hinmw"`로 고정폭 advance를 유도한다.
  non-Mono에서도 ASCII 글리프는 모두 1셀 고정폭이므로 이 로직은 변경 불필요.

## 설계

### 1. 소스 폰트 파일명 교체 (핵심, 유일한 필수 기능 변경)

`src/jetendard/builder.py`의 `make_font_variant`:

```python
# before
latin_filename=f"JetBrainsMonoNerdFontMono-{latin_suffix}.ttf",
# after
latin_filename=f"JetBrainsMonoNerdFont-{latin_suffix}.ttf",
```

`download_upstream.py`의 다운로드/추출은 `variant.latin_filename`을 참조하므로
자동으로 non-Mono 파일을 받게 된다(코드 변경 불필요, 문자열/주석만 갱신).

### 2. monospace 분류 메타데이터: 업스트림 non-Mono에 정합

현재 `merge_fonts`는 `enforce_monospace_flags(latin_font)`로
`post.isFixedPitch=1` 및 panose `bProportion=9`를 **강제**한다. non-Mono는
2셀 아이콘을 갖는 폰트이므로, 이 강제가 업스트림의 실제 설계와 어긋날 수 있다.

**방침:** 업스트림 `JetBrainsMonoNerdFont-Regular.ttf`의 실제
`post.isFixedPitch` / panose `bProportion` 값을 **구현 단계에서 파일을 열어 확인**한 뒤
그 값에 맞춘다.

- 업스트림이 `isFixedPitch=0`(비고정폭 분류)이라면 → `enforce_monospace_flags`
  호출을 제거하여 소스 값을 그대로 보존한다.
- 업스트림이 `isFixedPitch=1`이라면 → 현행 강제를 유지한다.

근거: 결과 폰트가 "검증된 업스트림 non-Mono와 동일한 분류 동작 + 한글 추가"가 되도록
한다. 우리가 추가하는 한글 글리프도 정확히 2셀이라 원본의 double-width 설계와
일관된다. **삭제를 미리 확정하지 않고, 경험적으로 결정한다.**

### 3. 하드 의존성 사전 검증

리네임을 신뢰하기 전에 JetBrainsMono.zip(nerd-fonts v3.4.0) 아카이브에 non-Mono
16개 파일이 정확한 이름으로 존재하는지 확인한다:

```
JetBrainsMonoNerdFont-Thin.ttf, -ExtraLight, -Light, -Regular, -Medium,
-SemiBold, -Bold, -ExtraBold, 그리고 각 Italic
(-Italic, -ThinItalic, ..., -ExtraBoldItalic)
```

(현재 `DEFAULT_VARIANTS` = 8 weight × 2 style = 16개.)

### 4. 테스트 정합

- `tests/test_builder.py:107` — `latin_filename == "JetBrainsMonoNerdFontMono-Italic.ttf"`
  → non-Mono 이름으로 갱신.
- `tests/test_builder.py:258` — 하드코딩된 Mono 경로 → non-Mono 경로로 갱신.
- `tests/test_builder.py:242` (`test_enforce_monospace_flags`),
  `:278` (`isFixedPitch == 1` 단언) — 2번의 경험적 결정 결과에 맞게 조정.
  (업스트림이 0이면 이 두 테스트의 기대값/대상 함수도 함께 재검토 — 기존 테스트가
  옛 동작에 조용히 고정시키지 않도록.)

### 5. 문서 / 문자열 갱신

"Nerd Font Mono" / `JetBrainsMonoNerdFontMono` 참조를 non-Mono 기준으로 갱신:

- `pyproject.toml:4` (description)
- `src/jetendard/cli.py:63,70,240` (help/에러 문자열)
- `src/jetendard/builder.py:614` (docstring)
- `download_upstream.py:134,152` (SOURCES 노트 텍스트, docstring)
- `README.md` 7,16,20,65,87,108,114행 — 특히 108~114행 "Mono만 쓴다 / Black 소스가
  없다" 서술을 non-Mono 기준으로 재작성.
- `README.ko.md` 대응 행(9,16,21,65,88,108,115).

## 검증 (판별력 있는 체크)

1. **업스트림 원본 확인:** `JetBrainsMonoNerdFont-Regular.ttf`에서 넓은 아이콘
   글리프의 advance == ASCII advance × 2 임을 확인. `post.isFixedPitch`,
   panose `bProportion` 값 기록.
2. **병합 출력 확인:** 생성된 `Jetendard-Regular.ttf`에서
   - 넓은 아이콘 advance == ASCII advance × 2 (아이콘 풀사이즈의 실제 근거)
   - 한글(`가`) advance == ASCII advance × 2
   - `isFixedPitch` == 업스트림과 일치
   - `ccmp`, `calt` 피처 존재
3. **테스트:** `uv run pytest -v` 통과 (`ruff check`, `ruff format`,
   `uv run ty check` 클린).
4. **실사용 육안 확인:** 사용자 환경(Ghostty)에서 렌더링 확인.
   - ⚠️ 주의: Ghostty 1.2.0+는 자체 아이콘 크기/폭 로직을 적용하며,
     Mono/non-Mono 구분과 무관하게 동작할 수 있다. Ghostty에서 눈에 띄는 변화가
     없더라도 Zed/VS Code 등 advance width를 존중하는 앱에서는 아이콘이 2셀
     풀사이즈로 커진다. Ghostty에서의 결과는 앱 측 요인일 수 있으므로, 폰트 측
     교체가 올바르게 되었는지는 위 2번(advance width)으로 판정한다.

## 범위 밖 (YAGNI)

- Mono/non-Mono를 선택하는 CLI 옵션 추가 — 하지 않음. 하드 교체.
- 아이콘 크기 커스터마이징 로직 — 하지 않음.
- 한글 스케일(1.15) 변경 — 하지 않음.

## 리스크 / 미결

- **Ghostty 렌더링:** 사용자 주 환경이 Ghostty이고, Ghostty 1.2.0+의 자체
  아이콘 로직 때문에 폰트 교체의 시각적 효과가 Ghostty에서는 제한적일 수 있다.
  이는 폰트 산출물 정확성(advance width)과 별개 문제이며, 본 작업의 완료 기준은
  "산출물 폰트가 non-Mono advance를 올바르게 담는다"로 정의한다.
