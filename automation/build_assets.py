"""수치 보정·한글 타이핑 GIF·편집용 HTML. 원본은 읽기만 한다."""
import argparse
import hashlib
import html
import json
import re
import shutil
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat


def load_config(path):
    """설정 파일을 기준으로 경로를 풀어 실행 폴더·OS에 종속되지 않게 한다."""
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    for key in ("source_dir", "output_dir", "font", "brand_font", "banner_file"):
        if config.get(key):
            value = Path(config[key]).expanduser()
            config[key] = str((path.parent / value).resolve())
    return config


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def styled(text):
    # ponytail: 저자가 정한 의미 단위 줄바꿈만 사용. 자동 문장 분리는 약어를 깨뜨린다.
    parts = re.split(r"(\*\*.*?\*\*)", text, flags=re.S)
    return "".join("<strong>" + html.escape(s[2:-2]) + "</strong>"
                   if s.startswith("**") else html.escape(s) for s in parts).replace("\n", "<br>")


def body_text(config):
    return "".join(b["text"].replace("**", "").replace("\n", "")
                   for b in config["blocks"] if b["type"] != "image")


def tags_text(config):
    tags = config.get("tags", [])
    if tags and (len(tags) != 15 or len(set(tags)) != 15 or not all(re.fullmatch(r"\w+", t) for t in tags)):
        raise ValueError("태그는 #/공백 없이 서로 다른 단어15개를 지정하세요")
    return "\n".join(" ".join("#" + tag for tag in tags[i:i+3]) for i in range(0, len(tags), 3))


def tone(image, gammas):
    # 채널별 감마로 중간 밝기·온도를 올리되 흰색255와 검정0은 유지한다.
    return image.point([round(255 * (v / 255) ** gamma)
                        for gamma in gammas for v in range(256)])


def build(config):
    start = time.monotonic()
    if config.get("needs_authoring"):
        raise ValueError("새 현장 사진·메모로 원고/태그를 확인하고 needs_authoring을 false로 바꾸세요")
    assert len(body_text(config)) == config["body_target_chars"], "본문 글자 수 불일치"
    hashtags = tags_text(config)
    source, out = Path(config["source_dir"]), Path(config["output_dir"])
    source, out = source.resolve(), out.resolve()
    if source == out or source in out.parents or out in source.parents:
        raise ValueError("원본과 출력 폴더는 서로 포함되지 않는 별도 폴더로 지정하세요")
    photos = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not photos:
        raise ValueError("JPG/JPEG/PNG 사진이 없습니다")
    photo_names = {f"photo_{i:03d}" for i in range(1, len(photos)+1)}
    requested = {b["name"] for b in config["blocks"] if b["type"] == "image" and b["name"].startswith("photo_")}
    if requested != photo_names:
        raise ValueError("사진 수/번호와 본문 사진 블록이 다릅니다")
    thumbnail_name = config.get("thumbnail_photo", "photo_001")
    if thumbnail_name not in photo_names:
        raise ValueError("썸네일 원본 번호가 없습니다")
    for key in ("font", "brand_font"):
        if not Path(config[key]).is_file():
            raise ValueError("폰트 파일 없음: " + key)
    banner_source = Path(config["banner_file"]) if config.get("banner_file") else None
    if banner_source and not banner_source.is_file():
        raise ValueError("설정한 배너 파일이 없습니다")
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "보정사진"
    dest.mkdir(exist_ok=True)
    font_path = config["font"]
    font = lambda size: ImageFont.truetype(font_path, size)
    brand_font = lambda size: ImageFont.truetype(config["brand_font"], size)
    gammas = config["tone_gammas"]
    if len(gammas) != 3 or not all(0 < gamma <= 1 for gamma in gammas):
        raise ValueError("RGB 감마값은 0보다 크고 1 이하여야 합니다")
    before = {str(p): sha(p) for p in photos}
    manifest = {"source_sha256": before, "photos": [], "config": config,
                "method": "RGB gamma " + str(gammas) + "; original geometry; dark serif wordmark without box",
                "design": {"house_points": [[60,388],[540,68],[1020,388],[1020,954],[60,954]],
                           "brand_text": config["brand_text"], "brand_box": False,
                           "footer": config["thumbnail_footer"]}}
    for number, path in enumerate(photos, 1):
        photo_name = f"photo_{number:03d}"
        original = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        corrected = tone(original, gammas)
        layer = Image.new("RGBA", corrected.size)
        d = ImageDraw.Draw(layer)
        size = max(20, round(corrected.width * .055))
        d.text((corrected.width/2, corrected.height*.90), config["brand_text"],
               font=brand_font(size), anchor="mt", fill="#423228", stroke_width=1)
        if photo_name == thumbnail_name:
            layer.crop(layer.getbbox()).save(out/"브랜드_글자.png")
        final = Image.alpha_composite(corrected.convert("RGBA"), layer).convert("RGB")
        target = dest / (photo_name + ".jpg")
        final.save(target, quality=96, subsampling=0)
        manifest["photos"].append({"source": str(path), "output": str(target),
            "size": list(original.size), "sha256": sha(target),
            "mean_before": ImageStat.Stat(original.convert("L")).mean[0],
            "mean_after": ImageStat.Stat(final.convert("L")).mean[0]})

    bg = Image.new("RGB", (1080, 1080), "#f5f1e9")
    raw = tone(ImageOps.exif_transpose(Image.open(photos[int(thumbnail_name[-3:])-1])).convert("RGB"), gammas)
    # ponytail: 정사각형 썸네일만 크롭한다. 본문 사진은 전체 치수를 보존한다.
    raw = ImageOps.fit(raw, (960, 886), centering=(.5, .32))
    photo_layer = bg.copy()
    photo_layer.paste(raw, (60, 68))
    house_mask = Image.new("L", bg.size)
    ImageDraw.Draw(house_mask).polygon(manifest["design"]["house_points"], fill=255)
    bg.paste(photo_layer, (0, 0), house_mask)
    house_mask.save(out/"집모양_마스크.png")
    d = ImageDraw.Draw(bg)
    d.line((0, 66, 1080, 66), fill="#a69b8c", width=1)
    d.line((0, 954, 1080, 954), fill="#a69b8c", width=1)
    d.line((60, 0, 60, 1080), fill="#c2b7a5", width=1)
    d.line((1020, 0, 1020, 1080), fill="#c2b7a5", width=1)
    top = "BEYOND THE ENTRANCE"
    d.text((540, 24), top, font=font(30), anchor="mt", fill="#a12b21")
    d.text((540, 987), config["thumbnail_footer"].replace(" | ", "  |  "), font=brand_font(46),
           anchor="mt", fill="#423228", stroke_width=1)
    lines = config["thumbnail_lines"]
    f = font(76)
    positions = [(82, 646), (82, 770)]
    for line, (x, y) in zip(lines, positions):
        width = d.textbbox((0, 0), line, font=f)[2]
        if width > 900:
            raise ValueError("썸네일 문구가 너무 깁니다")
        d.rectangle((60, y-15, x+width+25, y+92), fill="#52382b")

    visible = [("", "")]
    a, b = "", ""
    for char in lines[0]:
        a += char
        visible.append((a, b))
    for char in lines[1]:
        b += char
        visible.append((a, b))
    frames = []
    for pair in visible:
        frame = bg.copy()
        dr = ImageDraw.Draw(frame)
        for value, pos in zip(pair, positions):
            dr.text(pos, value, font=f, fill="white")
        frames.append(frame)
    png = out / "대표사진.png"
    frames[-1].save(png)
    # 하나의 팔레트를 공유해 프레임마다 사진 색이 출렁이는 것을 막는다.
    palette = frames[-1].quantize(colors=256)
    gif_frames = [im.quantize(palette=palette) for im in frames]
    durations = [400] + [180] * (len(frames)-2) + [2080]
    gif = out / "움직이는썸네일.gif"
    gif_frames[0].save(gif, save_all=True, append_images=gif_frames[1:], duration=durations,
                       loop=0, disposal=1, optimize=False)
    manifest["animation"] = {"frames_requested": len(frames), "visible_text": visible,
        "duration_ms": sum(durations), "gif_sha256": sha(gif), "png_sha256": sha(png)}

    fragments, preview, plain = [], [], [config["title"], ""]
    text_groups, group = [], []
    for block in config["blocks"]:
        if block["type"] == "image":
            if group:
                text_groups.append("".join(group))
                group = []
            name = block["name"]
            rel = {"thumbnail": "대표사진.png", "animation": "움직이는썸네일.gif"}.get(name, "보정사진/"+name+".jpg")
            fragment = '<p style="font-size:16px">'+block["marker"]+'</p><p style="font-size:16px"><br></p>'
            preview.append('<img src="'+rel+'" alt="'+html.escape(name)+'">')
            plain += [block["marker"], ""]
        else:
            heading = block["type"] == "heading"
            size = 30 if heading else 16
            content = styled(block["text"])
            if heading:
                content = "<strong>"+content+"</strong>"
            # 교체할 구간이 굵은 소제목으로 시작해도 일반 본문은 굵기를 상속하지 않는다.
            fragment = f'<p style="font-family:나눔스퀘어;font-size:{size}px;font-weight:normal;line-height:{1.5 if heading else 2.1};">{content}</p>'
            if block.get("gap_after", True):
                fragment += '<p style="font-size:16px;font-weight:normal;line-height:2.1;"><br></p>'
            preview.append(fragment)
            group.append(fragment)
            plain += [block["text"].replace("**", "")]
            if block.get("gap_after", True):
                plain.append("")
        fragments.append(fragment)
    if group:
        text_groups.append("".join(group))
    (out/"구간별_본문.json").write_text(json.dumps(text_groups, ensure_ascii=False, indent=2), encoding="utf-8")
    (out/"편집기_붙여넣기.html").write_text("".join(fragments), encoding="utf-8")
    (out/"본문.txt").write_text("\n".join(plain), encoding="utf-8")
    (out/"본문_1800자.txt").write_text("".join(b["text"].replace("**", "") + ("\n\n" if b.get("gap_after", True) else "\n") for b in config["blocks"] if b["type"] != "image"), encoding="utf-8")
    tags_html = "".join('<p style="font-family:나눔스퀘어;font-size:16px;font-weight:normal;line-height:2.1;">'+html.escape(line)+'</p>' for line in hashtags.splitlines())
    (out/"태그.txt").write_text(hashtags, encoding="utf-8")
    (out/"태그_붙여넣기.html").write_text(tags_html, encoding="utf-8")
    banner_target = out/"템플릿_상담배너.png"
    if banner_source and banner_source.resolve() != banner_target.resolve():
        shutil.copy2(banner_source, banner_target)
    banner = ('<a href="'+html.escape(config["banner_link"], quote=True)+'"><img src="템플릿_상담배너.png" alt="중문매니저 전화 상담"></a>') if banner_target.exists() else '<p style="font-size:16px">[네이버 내 템플릿의 기존 전화 상담 배너를 마지막에 삽입]</p>'
    preview_html = '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(config["title"])+'</title><style>body{max-width:720px;margin:36px auto;padding:0 20px;font-family:Arial,sans-serif;color:#222}h1{font-size:25px;line-height:1.5}p{margin:0;overflow-wrap:anywhere}img{width:100%;height:auto;margin:22px 0}</style><h1>'+html.escape(config["title"])+'</h1>'+"".join(preview)+banner+tags_html+'</html>'
    (out/"모바일_미리보기.html").write_text(preview_html, encoding="utf-8")
    assert before == {str(p): sha(p) for p in photos}, "원본 변경 감지"
    manifest["build_seconds"] = round(time.monotonic()-start, 3)
    (out/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def check(out):
    m = json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    assert all(sha(Path(p)) == expected for p, expected in m["source_sha256"].items())
    assert len(m["photos"]) == len(m["source_sha256"]) > 0
    for row in m["photos"]:
        target = Path(row["output"])
        assert list(Image.open(target).size) == row["size"]
        assert sha(target) == row["sha256"]
        assert row["mean_after"] > row["mean_before"]
        expected = tone(ImageOps.exif_transpose(Image.open(row["source"])).convert("RGB"), m["config"]["tone_gammas"])
        area = (0,0,expected.width,int(expected.height*.88))
        error = ImageStat.Stat(ImageChops.difference(expected.crop(area),Image.open(target).crop(area))).mean
        assert max(error) < 1.5, "수치 보정 외 원본 구조 변경 감지"
    png, gif = Image.open(out/"대표사진.png"), Image.open(out/"움직이는썸네일.gif")
    assert png.size == gif.size == (1080, 1080)
    house = Image.open(out/"집모양_마스크.png")
    assert house.getpixel((80,160)) == house.getpixel((1000,160)) == 0
    assert house.getpixel((540,90)) == house.getpixel((80,420)) == 255
    assert png.getpixel((80,160)) == png.getpixel((1000,160)) == (245,241,233)
    alpha = Image.open(out/"브랜드_글자.png").getchannel("A")
    coverage = sum(alpha.histogram()[1:])/(alpha.width*alpha.height)
    assert 0.1 < coverage < .65, "브랜드 글자 뒤 배경 상자 감지"
    assert gif.n_frames >= 10 and gif.info["loop"] == 0
    duration = 0
    gif_palette = gif.copy()
    first = gif.convert("RGB")
    for i in range(gif.n_frames):
        gif.seek(i)
        duration += gif.info["duration"]
        # 글자가 들어가는 영역 밖 사진·머리글·브랜드는 프레임 전체에서 고정.
        assert gif.convert("RGB").crop((0,0,1080,620)).tobytes() == first.crop((0,0,1080,620)).tobytes()
    assert duration == m["animation"]["duration_ms"]
    assert gif.info["duration"] >= 2000
    assert ImageStat.Stat(ImageOps.grayscale(gif.convert("RGB"))).mean[0] > 0
    assert sha(out/"대표사진.png") == m["animation"]["png_sha256"]
    assert sha(out/"움직이는썸네일.gif") == m["animation"]["gif_sha256"]
    # 마지막 GIF 프레임은 정지 PNG를 같은 팔레트로 바꾼 결과와 정확히 같아야 한다.
    assert png.convert("RGB").quantize(palette=gif_palette).convert("RGB").tobytes() == gif.convert("RGB").tobytes()
    doc = (out/"편집기_붙여넣기.html").read_text(encoding="utf-8")
    assert 'font-size:30px' in doc and 'font-size:16px' in doc and '<strong>' in doc
    assert len(re.findall(r'〔사진 \d{3}〕', doc)) == len(m["photos"])
    actual_body = (out/"본문_1800자.txt").read_text(encoding="utf-8").replace("\n", "")
    assert actual_body == body_text(m["config"])
    assert len(actual_body) == m["config"]["body_target_chars"]
    assert (out/"태그.txt").read_text(encoding="utf-8") == tags_text(m["config"])
    result = {"result":"PASS", "photos":len(m["photos"]), "gif_frames":gif.n_frames,
              "body_chars":len(actual_body), "body_count_rule":m["config"]["body_count_rule"],
              "tag_count":len(m["config"].get("tags", [])),
              "duration_ms":duration, "build_seconds":m["build_seconds"],
              "checks":["source hashes", "dimensions", "photo geometry", "brighter", "house silhouette", "brand without box", "fixed background", "loop", "end hold", "PNG matches final GIF", "font styles", "photo slots", "exact body character count", "separate tags"]}
    (out/"검증결과.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1]/"post.local.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    out = Path(config["output_dir"]) if args.check else build(config)
    check(out)
