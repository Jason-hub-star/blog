"""공개 예시와 합성 사진으로 검사. 실제 현장 사진/원고는 읽거나 쓰지 않는다."""
import importlib.util
import json
from pathlib import Path
import tempfile

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_assets", ROOT / "automation/build_assets.py")
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


def must_fail(config, message):
    try:
        assets.build(config)
    except (ValueError, AssertionError):
        return
    raise AssertionError(message)


def main():
    for row in json.loads((ROOT / "assets/fonts/SOURCES.json").read_text(encoding="utf-8")):
        assert assets.sha(ROOT / "assets/fonts" / row["file"]) == row["sha256"]
    skill = ROOT / ".claude/skills/jungmun-blog-production/SKILL.md"
    router = ROOT / ".agents/skills/jungmun-blog-production/SKILL.md"
    assert skill.is_file() and router.is_file()
    assert "../../../.claude/skills/jungmun-blog-production/SKILL.md" in router.read_text(encoding="utf-8")
    for folder in ["automation", "scripts", "tests", ".claude", ".agents", "harnesses", "docs"]:
        for file in (ROOT / folder).rglob("*"):
            if file.is_file() and file.suffix in {".py", ".mjs", ".md", ".json"}:
                content = file.read_text(encoding="utf-8")
                assert ("/Users/" + "family/") not in content, "Mac 절대경로: " + str(file.relative_to(ROOT))

    with tempfile.TemporaryDirectory(prefix="jungmun-") as temp:
        base = Path(temp)
        photos = base / "한글 공백 사진"
        photos.mkdir()
        for i in range(1, 8):
            suffix = [".jpg", ".JPEG", ".PNG"][i % 3]
            im = Image.new("RGB", (480, 640), (90+i*9, 110+i*5, 130))
            ImageDraw.Draw(im).rectangle((80, 60, 400, 600), outline=(65, 55, 45), width=8)
            im.save(photos / (f"사진 {i}" + suffix))
        raw = json.loads((ROOT / "post.example.json").read_text(encoding="utf-8"))
        raw.update(source_dir="한글 공백 사진", output_dir="결과", font=str(ROOT / raw["font"]), brand_font=str(ROOT / raw["brand_font"]))
        config_file = base / "설정.json"
        config_file.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8-sig")
        config = assets.load_config(config_file)
        assert Path(config["source_dir"]) == photos.resolve()
        out = assets.build(config)
        assets.check(out)
        report = json.loads((out / "검증결과.json").read_text(encoding="utf-8"))
        assert report["photos"] == 7 and report["body_chars"] == 1800
        assert report["duration_ms"] == 5000
        assert (out / "모바일_미리보기.html").is_file()
        # 실패 입력은 원본/출력을 건드리기 전에 거부해야 한다.
        before = {p: assets.sha(p) for p in photos.iterdir()}
        must_fail({**config, "body_target_chars": 1801}, "잘못된 글자 수 허용")
        must_fail({**config, "output_dir": str(photos)}, "원본 덮어쓰기 허용")
        must_fail({**config, "output_dir": str(photos / "output")}, "원본 내부 출력 허용")
        must_fail({**config, "output_dir": str(base)}, "출력 내부 원본 허용")
        must_fail({**config, "blocks": [b for b in config["blocks"] if b.get("name") != "photo_007"]}, "사진 번호 불일치 허용")
        assert before == {p: assets.sha(p) for p in photos.iterdir()}
    print("PASS: fonts, skill routes, portable paths, Unicode/BOM config, 7-photo build, 1800 chars, GIF/PNG, input guards")


if __name__ == "__main__":
    main()
