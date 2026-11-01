"""고객 자료 없이 한글 경로/BOM/동봉 폰트/세 GIF 효과/브랜드 가드를 확인한다."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = json.loads((ROOT / "assets/fonts/SOURCES.json").read_text(encoding="utf-8"))
    for source in sources:
        assert hashlib.sha256((ROOT / "assets/fonts" / source["file"]).read_bytes()).hexdigest() == source["sha256"]
    jobs = ROOT / "현장작업"
    jobs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="가상 현장_", dir=jobs) as temporary:
        job = Path(temporary)
        originals = job / "01_원본사진"
        originals.mkdir()
        photo = originals / "한글 시공후.jpg"
        Image.new("RGB", (900, 1200), (215, 220, 225)).save(photo)
        sha = hashlib.sha256(photo.read_bytes()).hexdigest()
        (job / "원본목록.json").write_text(json.dumps([{"name": photo.name, "sha256": sha}], ensure_ascii=False), encoding="utf-8-sig")
        post = json.loads((ROOT / "post.example.json").read_text(encoding="utf-8"))
        post.update(needs_authoring=False, cover=photo.name, photos=[photo.name], photo_stages={photo.name: "after"}, production_status="synthetic_test")
        post["blocks"][1]["text"] = ("가상 입력 검사용 문장입니다. 실제 현장 기록이 아닙니다. " * 80)[:1600]
        config = job / "post.json"

        def run(extra=(), expected=None):
            config.write_text(json.dumps(post, ensure_ascii=False), encoding="utf-8-sig")
            result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "automation/build_post.py"), "--job", str(job), *extra], capture_output=True, text=True, encoding="utf-8", timeout=60)
            if expected:
                assert result.returncode and expected in result.stderr, result.stderr
            else:
                assert result.returncode == 0, result.stderr

        run()
        out = job / "02_제작물"
        svg = (out / "썸네일_편집원본.svg").read_text(encoding="utf-8")
        font = base64.b64encode((ROOT / "assets/fonts/NanumSquareEB.ttf").read_bytes()).decode()
        assert font in svg and post["blocks"][0]["text"] in (out / "본문.txt").read_text(encoding="utf-8")
        assert (out / "편집기_붙여넣기.html").read_text(encoding="utf-8").startswith("<blockquote")
        # ponytail: 테스트용 도형은 렌더러 입력 계약이다. 실사진/SVG의 시각 품질 판정은 아니다.
        background = Image.new("RGB", (900, 900), (215, 220, 225))
        ink = Image.new("RGBA", (900, 900))
        draw = ImageDraw.Draw(ink)
        draw.rectangle((300, 650, 600, 660), fill="#E99025")
        draw.rectangle((275, 820, 295, 840), fill="#E99025")
        draw.rectangle((298, 825, 306, 835), fill="#248A76")
        background.save(out / "썸네일_배경.png")
        ink.save(out / "썸네일_글자.png")
        Image.alpha_composite(background.convert("RGBA"), ink).convert("RGB").save(out / "대표사진.png")
        for effect in ["페이드", "올라오기", "밀어내기"]:
            post["gif_effect"] = effect
            run(["--animate"])
            run(["--check"])
            assert hashlib.sha256(photo.read_bytes()).hexdigest() == sha
        baseline = copy.deepcopy(post)
        post["photo_stages"][photo.name] = "before"
        run(expected="시공 후 사진만")
        post = copy.deepcopy(baseline)
        post["needs_authoring"] = True
        run(expected="needs_authoring")
        post = copy.deepcopy(baseline)
        post["brand"] = "다른 브랜드"
        run(expected="금강이지스 artdoorstore 전용")
        post = copy.deepcopy(baseline)
        post["blocks"][0]["text"] += "\n둘째 줄"
        run(expected="요약한 한 줄")
    print("PASS: 한글/공백 경로·UTF-8 BOM·동봉 폰트·원본 불변·세 GIF 생성/프레임/방향·가드4종")


if __name__ == "__main__":
    main()
