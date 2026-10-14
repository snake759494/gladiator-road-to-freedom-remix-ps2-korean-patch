# 재빌드

준비물: Python 3.11+ (numpy, Pillow, capstone), 원본 ISO, `NanumSquareNeo-bRg.ttf`, 번역 자료(`work/ko/*.tsv`, `work/src_order.json`, `work/elf_ko.tsv` — 저장소 미포함).

```
작업폴더/
  Gladiator - Road to Freedom - Remix (Japan).iso
  NanumSquareNeo-bRg.ttf
  tools/        (이 저장소의 tools)
  work/ko/*.tsv, work/src_order.json, work/elf_ko.tsv
```

```powershell
cd tools
python build.py        # -> ..\Gladiator - Road to Freedom - Remix (Korean).iso
cd ..
xdelta3 -e -s "Gladiator - Road to Freedom - Remix (Japan).iso" "Gladiator - Road to Freedom - Remix (Korean).iso" Gladiator_Road_to_Freedom_Remix_KO_v1.0.1.xdelta
```

- `build.py`: 번역 로드 → 한글-한자 코드 대응 → GG.DAT·DATA.RBB 안 CSB/ARY/글꼴 수정 → ELF 문자열 → ISO 기록(크기가 늘면 ISO 끝으로 옮기고 ISO9660·UDF 갱신).
- 경로는 `tools/build.py`, `tools/gg.py`, `tools/kotext.py` 상단의 `ROOT`/`ISO`/`W` 상수에서 바꾼다.
- `tools/emu.ps1`: PCSX2 실행·스크린샷·키 입력 보조(자기 PID 만 다룸).
- 번역 TSV 형식: `번호<TAB>한국어` (번호는 `src_order.json` 의 원문 순서), ELF 는 `파일오프셋<TAB>한국어`.
