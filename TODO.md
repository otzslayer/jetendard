# TODO / Handoff

## 현재 상태 (2026-07-13)

**브랜치:** `feat/base-font-nonmono` (커밋 `0bdbbab`)

베이스 폰트를 **non-Mono 기본 + `--mono` 플래그로 Mono 선택**하도록 구현 완료.
설계·근거·검증은 `docs/superpowers/specs/2026-07-13-base-font-nonmono-design.md`
(as-built로 갱신됨) 참고.

### 완료된 것
- `make_font_variant(..., mono=False)` 파라미터를 CLI(`--mono`)까지 배선
  (`builder.py` → `cli.py`). 기본 non-Mono, `--mono`면 기존 Mono 동작.
- `download_upstream.py`가 Mono·non-Mono 두 세트(32개) 모두 추출.
- 테스트 정합 + `mono` 플래그 커버리지, README(.ko)/pyproject/spec 갱신.
- 검증: pytest 33 passed·1 skipped, ruff 클린, end-to-end CLI 정상,
  산출물 실측(non-Mono fa-heart 아웃라인 923 vs Mono 599, 한글 2×, isFixedPitch=1).

### 핵심 컨텍스트 (다음 작업자용)
- Mono·non-Mono **둘 다 아이콘 advance는 1셀(600)**. 차이는 아웃라인 크기 →
  non-Mono는 다음 셀로 넘침(overflow). "2셀 advance"는 존재하지 않음.
- `isFixedPitch=1` **유지**(advance 그리드 보존 + 편집기 monospace 목록 노출).
  spec 최초안의 "제거" 지시와 다름 — 의도된 변경.
- **Ghostty는 자체 아이콘 로직**으로 Mono/non-Mono 차이 미미. 효과는 Zed/VS Code에서.

## 남은 작업

- [ ] **PR 생성** — `feat/base-font-nonmono` → `main`
      (`otzslayer/jetendard`). 본문에 non-Mono 기본 전환 + `--mono` + 아이콘
      오버플로 트레이드오프 요약.
- [ ] **시각 확인 (Zed/VS Code)** — non-Mono 기본 빌드로 아이콘이 실제로 커지는지,
      다음 셀 오버플로(인접 글자 겹침)가 수용 가능한지 육안 확인. 문제 시 `--mono`
      회피 가능함을 문서에 이미 명시.
- [ ] **전체 16변형 빌드 검증** — `make download` 후
      `JETENDARD_RUN_FULL_INTEGRATION=1 uv run pytest` 또는 `make run`으로 16변형
      전량 non-Mono 빌드 확인(현재는 Regular normal/italic만 통합 통과).
- [ ] **README 스크린샷 갱신 (선택)** — 현재 스크린샷은 구(Mono) 렌더링.
      특히 Zed 스크린샷은 이제 더 큰 아이콘을 보여주므로 갱신 고려.

## 재개 방법
```bash
git checkout feat/base-font-nonmono
uv sync --all-groups
make download          # Mono + non-Mono 둘 다 추출
uv run pytest -q       # 회귀 확인
uv run jetendard --variants Regular            # non-Mono 샘플
uv run jetendard --mono --variants Regular     # Mono 샘플(기존 동작)
```
