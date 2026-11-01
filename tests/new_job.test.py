"""새 현장 폴더 생성의 파일 안전성 검사."""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/new_job.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(name, source, count):
    return subprocess.run([sys.executable, str(SCRIPT), name, "--date", "2026-11-01", "--photos-dir", str(source)],
                          cwd=ROOT, text=True, capture_output=True, check=False)


def main():
    created = []
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        for count in (5, 10):
            source = temp / f"사진 {count}장"
            source.mkdir()
            for index in range(count):
                (source / f"사진 {count-index:02d}.JpG").write_bytes(bytes([index]) * (index + 3))
            before = {path.name: digest(path) for path in source.iterdir()}
            name = f"한글 현장 {count} 장"
            result = invoke(name, source, count)
            assert result.returncode == 0, result.stderr
            job = ROOT / "현장작업" / f"2026-11-01_{name}"
            created.append(job)
            config = json.loads((job / "post.local.json").read_text(encoding="utf-8"))
            photos = [block["name"] for block in config["blocks"] if block.get("name", "").startswith("photo_")]
            assert sorted(photos) == [f"photo_{number:03d}" for number in range(1, count + 1)]
            assert config["needs_authoring"] is True
            assert (job / config["source_dir"]).resolve() == job / "01_원본사진"
            assert (job / config["output_dir"]).resolve() == job / "03_작업결과"
            assert (job / config["font"]).resolve() == ROOT / "assets/fonts/NanumSquareEB.ttf"
            assert (job / config["brand_font"]).resolve() == ROOT / "assets/fonts/NanumMyeongjo-ExtraBold.ttf"
            assert before == {path.name: digest(path) for path in source.iterdir()}
            assert sorted((path.name for path in (job / "01_원본사진").iterdir()), key=str.casefold) == sorted(before, key=str.casefold)
            assert all(digest(source / name) == digest(job / "01_원본사진" / name) for name in before)
            assert "01_원본사진" in (job / "시작하기.txt").read_text(encoding="utf-8")
            assert invoke(name, source, count).returncode != 0
        invalid = invoke('금지:이름', temp / "사진 5장", 5)
        assert invalid.returncode != 0
        draft_name = "사진 대기 현장"
        draft = subprocess.run([sys.executable, str(SCRIPT), draft_name, "--date", "2026-11-01"],
                               cwd=ROOT, text=True, capture_output=True, check=False)
        assert draft.returncode == 0, draft.stderr
        draft_job = ROOT / "현장작업" / f"2026-11-01_{draft_name}"
        created.append(draft_job)
        draft_config = json.loads((draft_job / "post.local.json").read_text(encoding="utf-8"))
        assert draft_config["needs_authoring"] is True
        # 상대경로 배너를 현장 폴더 안으로 함께 옮긴다.
        banner = temp / "배너.png"
        banner.write_bytes(b"banner")
        source_config = json.loads((ROOT / "post.example.json").read_text(encoding="utf-8"))
        for key in ("font", "brand_font"):
            source_config[key] = str(ROOT / source_config[key])
        source_config["banner_file"] = "배너.png"
        config_path = temp / "설정.json"
        config_path.write_text(json.dumps(source_config, ensure_ascii=False), encoding="utf-8")
        banner_job_name = "배너 상대경로 현장"
        banner_result = subprocess.run([sys.executable, str(SCRIPT), banner_job_name, "--date", "2026-11-01", "--config", str(config_path)],
                                      cwd=ROOT, text=True, capture_output=True, check=False)
        assert banner_result.returncode == 0, banner_result.stderr
        banner_job = ROOT / "현장작업" / f"2026-11-01_{banner_job_name}"
        created.append(banner_job)
        banner_config = json.loads((banner_job / "post.local.json").read_text(encoding="utf-8"))
        assert banner_config["banner_file"] == "02_참고자료/상담배너.png"
        assert (banner_job / banner_config["banner_file"]).read_bytes() == b"banner"
        spec = importlib.util.spec_from_file_location("new_job", SCRIPT)
        jobs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jobs)
        import datetime
        # 다른 Windows 드라이브의 relpath 오류는 폴더/사진을 만들기 전에 거절한다.
        rejected_name = "폰트 경로 거절 현장"
        with patch.object(jobs.os.path, "relpath", side_effect=ValueError("different drive")):
            try:
                jobs.create_job(rejected_name, datetime.date(2026, 11, 1))
            except ValueError as error:
                assert "다른 드라이브" in str(error)
            else:
                raise AssertionError("다른 드라이브 폰트 경로를 허용함")
        assert not (ROOT / "현장작업" / f"2026-11-01_{rejected_name}").exists()
    for job in created:
        shutil.rmtree(job)
    print("PASS: Unicode/spaces, 5/10 photos, byte-identical originals, no overwrite, Windows-invalid name")


if __name__ == "__main__":
    main()
