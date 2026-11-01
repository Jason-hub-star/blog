"""실제 작업 자료의 로컬 이전 묶음. 업로드하지 않으며 인증/코드는 포함하지 않는다."""
import hashlib
import json
from pathlib import Path
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def nfc(value):
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [nfc(v) for v in value]
    if isinstance(value, dict):
        return {nfc(k): nfc(v) for k, v in value.items()}
    return value


def main():
    out = ROOT / "로컬이전/금강이지스_Windows_작업이전.zip"
    out.parent.mkdir(exist_ok=True)
    entries = []
    seen = set()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for folder in ["현장작업", "리뷰조사", "후기레퍼런스", "재료"]:
            for file in sorted((ROOT / folder).rglob("*")):
                relative = file.relative_to(ROOT)
                if not file.is_file() or file.is_symlink() or any(p.startswith('.') or p in ['이전버전','__pycache__','새_현장'] for p in relative.parts) or file.name == "모션_검사.gif":
                    continue
                name = nfc(relative.as_posix())
                assert name not in seen, "파일명 정규화 충돌: " + name
                seen.add(name)
                raw = file.read_bytes()
                data = (json.dumps(nfc(json.loads(raw.decode("utf-8-sig"))), ensure_ascii=False, indent=2)+'\n').encode('utf-8') if file.suffix.lower()=='.json' else raw
                archive.writestr(name, data)
                entries.append({"name":name,"sha256":hashlib.sha256(data).hexdigest(),"size":len(data)})
        archive.writestr("Windows_이전목록.json", json.dumps({"normalization":"NFC","files":entries}, ensure_ascii=False, indent=2).encode('utf-8'))
    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        for entry in entries:
            assert hashlib.sha256(archive.read(entry['name'])).hexdigest()==entry['sha256']
    print(f"로컬 이전 묶음 검증 완료: {out} / {len(entries)}파일 / {out.stat().st_size//1024//1024}MB")


if __name__ == "__main__":
    main()
