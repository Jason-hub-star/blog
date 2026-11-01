"""새 현장용 로컬 작업 폴더를 만든다. 외부 패키지 없이 실행한다."""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
INVALID_WINDOWS_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_WINDOWS_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_job_name(value):
    if not value or value != value.strip() or value.rstrip(". ") != value:
        raise ValueError("현장명은 비어 있거나 앞뒤 공백·마침표로 끝날 수 없습니다")
    if INVALID_WINDOWS_NAME.search(value) or value.split(".")[0].upper() in RESERVED_WINDOWS_NAMES:
        raise ValueError("현장명에 Windows에서 쓸 수 없는 문자가 있습니다: <>:\"/\\|?*")
    return value


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("날짜는 YYYY-MM-DD 형식이어야 합니다") from error


def relative_to_config(path, config_file):
    return Path(os.path.relpath(path, config_file.parent)).as_posix()


def load_config(source):
    source = source.resolve()
    config = json.loads(source.read_text(encoding="utf-8-sig"))
    for key in ("source_dir", "output_dir", "font", "brand_font", "banner_file"):
        if config.get(key):
            config[key] = (source.parent / Path(config[key]).expanduser()).resolve()
    return config


def photo_blocks(config, count):
    """기존 서식 키는 보존하며 photo_001..N만 조정한다."""
    blocks = []
    present = set()
    for block in config["blocks"]:
        name = block.get("name", "")
        match = re.fullmatch(r"photo_(\d{3})", name)
        if match:
            number = int(match.group(1))
            if number > count:
                continue
            present.add(number)
        blocks.append(block)
    missing = [number for number in range(1, count + 1) if number not in present]
    if missing:
        try:
            final_heading = max(index for index, block in enumerate(blocks) if block.get("type") == "heading")
        except ValueError:
            final_heading = len(blocks)
        additions = [{"type": "image", "name": f"photo_{number:03d}", "marker": f"〔사진 {number:03d}〕"}
                     for number in missing]
        blocks[final_heading:final_heading] = additions
    config["blocks"] = blocks


def write_memo(job):
    (job / "현장메모.txt").write_text(
        "지역/아파트: 미확인\n"
        "제품·방식(모르면 미확인): 미확인\n"
        "고객 고민: 미확인\n"
        "선택 이유(확인된 것만): 미확인\n"
        "강조점: 미확인\n"
        "대표사진 후보: 미확인\n",
        encoding="utf-8",
    )


def write_start(job, copied):
    photo_note = ("사진을 이미 01_원본사진에 복사했습니다. 순서는 원본 파일명 기준입니다."
                  if copied else "받은 JPG/JPEG/PNG 사진 5~10장을 01_원본사진에 그대로 넣어 주세요.")
    (job / "시작하기.txt").write_text(
        "1. " + photo_note + "\n"
        "2. 현장 확인 내용은 현장메모.txt에 적어 주세요. 모르는 내용은 미확인으로 둡니다.\n"
        "3. Codex/Claude에 이 폴더와 jungmun-blog-production 스킬을 지정합니다.\n"
        "   현장 사진·메모로 원고/태그를 확인한 뒤에만 needs_authoring을 false로 바꿉니다.\n"
        "4. 결과물은 03_작업결과에 생성됩니다. 참고 이미지·자료는 02_참고자료에 넣어 주세요.\n",
        encoding="utf-8",
    )


def create_job(name, date, photos_dir=None, config_source=None):
    validate_job_name(name)
    job = ROOT / "현장작업" / f"{date.isoformat()}_{name}"
    if job.exists():
        raise FileExistsError("기존 현장 작업 폴더를 덮어쓸 수 없습니다: " + str(job))

    source_config = (config_source or ROOT / "post.example.json").expanduser().resolve()
    if not source_config.is_file():
        raise ValueError("설정 파일이 없습니다: " + str(source_config))
    photos = None
    if photos_dir is not None:
        if not photos_dir.is_dir():
            raise ValueError("사진 폴더가 아닙니다: " + str(photos_dir))
        photos = sorted(path for path in photos_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
        if not 5 <= len(photos) <= 10:
            raise ValueError("사진 폴더에는 JPG/JPEG/PNG 사진이 5~10장 필요합니다")

    config = load_config(source_config)
    banner = Path(config["banner_file"]) if config.get("banner_file") else None
    if banner and not banner.is_file():
        raise ValueError("설정한 배너 파일이 없습니다: " + str(banner))
    config_file = job / "post.local.json"
    for key in ("font", "brand_font"):
        if not config[key].is_file():
            raise ValueError("설정 기준 폰트 파일이 없습니다: " + str(config[key]))
        try:
            config[key] = relative_to_config(config[key], config_file)
        except ValueError as error:
            raise ValueError("폰트가 저장소와 다른 드라이브에 있습니다. 저장소 안의 설정·동봉 폰트를 사용하세요") from error
    if photos is not None:
        photo_blocks(config, len(photos))
    job.mkdir(parents=True)
    originals, references, output = (job / "01_원본사진", job / "02_참고자료", job / "03_작업결과")
    for folder in (originals, references, output):
        folder.mkdir()
    if photos is not None:
        for source in photos:
            target = originals / source.name
            shutil.copy2(source, target)
            if sha256(source) != sha256(target):
                raise RuntimeError("복사한 원본 사진 바이트가 다릅니다: " + source.name)

    # ponytail: 사진 유무와 무관하게 새 현장의 사실·원고는 사람이/에이전트가 확인한다.
    config["needs_authoring"] = True
    config["source_dir"] = relative_to_config(originals, config_file)
    config["output_dir"] = relative_to_config(output, config_file)
    if banner:
        target = references / ("상담배너" + banner.suffix)
        shutil.copy2(banner, target)
        config["banner_file"] = relative_to_config(target, config_file)
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_memo(job)
    write_start(job, photos is not None)
    return job


def main(argv=None):
    parser = argparse.ArgumentParser(description="중문매니저 새 현장 작업 폴더 생성")
    parser.add_argument("name", help="현장명")
    parser.add_argument("--date", type=parse_date, default=dt.date.today())
    parser.add_argument("--photos-dir", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    try:
        job = create_job(args.name, args.date, args.photos_dir, args.config)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(job)


if __name__ == "__main__":
    main()
