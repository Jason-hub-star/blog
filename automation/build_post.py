#!/usr/bin/env python3
"""금강이지스 전용 원고·편집 가능한 SVG·로컬 렌더 화면. 원본 사진은 읽기만 한다."""
import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOB = ROOT / "현장작업/2026-11-01_명지_오픈형3연동"


def main():
    check = argparse.ArgumentParser()
    check.add_argument("--check", action="store_true")
    check.add_argument("--animate", action="store_true")
    check.add_argument("--job", default=str(DEFAULT_JOB))
    args = check.parse_args()
    JOB = Path(args.job).resolve()
    assert JOB.is_relative_to(ROOT / "현장작업"), "현장작업 안의 글 폴더만 사용하세요"
    OUT = JOB / "02_제작물"
    post = json.loads((JOB / "post.json").read_text(encoding="utf-8-sig"))
    assert not post.get("needs_authoring"), "사진·현장 사실·원고를 확인한 뒤 needs_authoring을 false로 바꾸세요"
    originals = json.loads((JOB / "원본목록.json").read_text(encoding="utf-8-sig"))
    assert post["brand"] == "금강이지스" and post["blog_id"] == "artdoorstore", "금강이지스 artdoorstore 전용입니다"
    assert (post["body_size"], post["heading_size"]) == (15, 30)
    assert originals and post["photos"] and set(post["photos"]) <= {e["name"] for e in originals}
    assert post.get("photo_stages", {}).get(post["cover"]) == "after", "섬네일·GIF는 확인된 시공 후 사진만 사용하세요"
    assert not set(post["photos"]) & set(post["excluded"])
    for entry in originals:
        raw = (JOB / "01_원본사진" / entry["name"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], entry["name"]
    for capture in post.get("review_captures", []):
        raw = (JOB / "01_리뷰캡처" / capture["name"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == capture["sha256"], "리뷰 캡처 원본 변경"
        assert capture["source_url"] == post["source_reviews"], "리뷰 캡처 상품 출처 불일치"
    assert [x["suffix"] for x in post["banners"]] == ["15-18-10.png", "15-18-18.png", "15-17-53.png"]
    quotes = [b for b in post["blocks"] if b["type"] == "quote"]
    assert len(quotes) == 1 and post["blocks"][0] is quotes[0], "관심 문구 인용구는 본문 맨 위 한 개만 배치하세요"
    assert quotes[0]["text"].strip() and quotes[0]["size"] == 19 and quotes[0]["style"] == "인용구 1"
    assert "\n" not in quotes[0]["text"], "상단 인용문은 본문을 요약한 한 줄로 작성하세요"
    if "photo_groups" in post:
        assert [p for group in post["photo_groups"] for p in group] == post["photos"], "콜라주 사진 순서를 확인하세요"
        assert post["photo_layout"] == "left_before_right_after_collage"
        assert [post["photo_stages"][p] for p in post["photo_groups"][0]] == ["before", "after"], "전후 콜라주는 왼쪽 전·오른쪽 후 순서입니다"
    text = "\n\n".join(b["text"] for b in post["blocks"] if "text" in b)
    body_length = len(text.replace("\n", ""))
    if post.get("review_reference_year"):
        mentioned = {f'{int(y or post["review_reference_year"]):04d}-{int(m):02d}-{int(d):02d}' for y, m, d in re.findall(r'(?:(\d{4})년 )?(\d{1,2})월 (\d{1,2})일 (?:구매 고객은|구매후기에는|후기에는|후기에서는|후기에서도)', text)}
        assert mentioned == {c["date"] for c in post["review_captures"]}, "본문에서 언급한 모든 구매후기의 실제 캡처를 연결하세요"
        review_blocks = [b for b in post["blocks"] if b.get("name", "").startswith("review_")]
        assert len(review_blocks) == len(post["review_captures"])
        for index, capture in enumerate(post["review_captures"], 1):
            position = next(i for i, b in enumerate(post["blocks"]) if b.get("name") == f"review_{index:03d}")
            assert post["blocks"][position-1].get("text", "").endswith(capture["after_text"]), "해당 후기 설명 바로 뒤에 캡처를 배치하세요"
    assert post["body_length_min"] <= body_length <= post["body_length_max"], f"본문 분량 {body_length}자: 1500~1800자 범위를 확인하세요"
    assert all(phrase not in text for phrase in post.get("removed_body_phrases", [])), "사용자가 삭제한 문구가 다시 포함되었습니다"
    assert all(x not in text + post["title"] for x in ["중문매니저", "KB자동중문", "205호", "128동"])
    assert len(post["tags"]) == len(set(post["tags"])) == 15
    logo = base64.b64encode((ROOT / post["logo"]).read_bytes()).decode()
    assert hashlib.sha256((ROOT / post["logo"]).read_bytes()).hexdigest() == post["logo_sha256"]
    assert post["accent_color"] == "#E99025"
    assert post["logo_star_color"] == "#248A76"
    if args.animate:
        ffmpeg = shutil.which("ffmpeg")
        assert ffmpeg, "FFmpeg를 설치하고 ffmpeg -version을 확인하세요. Windows 안내: docs/Windows_시작하기.md"
        effect = post["gif_effect"]
        if effect == "페이드":
            weight = "min(1,min(T/0.6,(5-T)/0.8))"
            prefix = f"[0:v][1:v]blend=all_expr='A*(1-({weight}))+B*({weight})'"
            foreground = "대표사진.png"
        else:
            assert effect in ["올라오기", "밀어내기"], "이 효과는 아직 렌더러 검증 전입니다"
            x = "-900*pow(max(0,1-t/0.8),3)" if effect == "밀어내기" else "0"
            y = "350*pow(max(0,1-t/0.8),3)" if effect == "올라오기" else "0"
            prefix = f"[1:v]format=rgba,fade=t=out:st=4.4:d=0.6:alpha=1[fg];[0:v][fg]overlay=x='{x}':y='{y}':format=auto:shortest=1"
            foreground = "썸네일_글자.png"
        graph = prefix + ",trim=duration=5,setpts=PTS-STARTPTS,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle"
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-framerate", "15", "-i", str(OUT / "썸네일_배경.png"), "-loop", "1", "-framerate", "15", "-i", str(OUT / foreground), "-filter_complex", graph, "-t", "5", "-r", "15", "-loop", "0", str(OUT / "움직이는썸네일.gif")], check=True, timeout=45)
        print("생성: 5초 반복 GIF. --check로 실제 프레임·재생시간을 검사하세요.")
        return
    if args.check:
        from PIL import Image
        png = Image.open(OUT / "대표사진.png").convert("RGB")
        assert png.size == (900, 900)
        logo_pixels = list(png.crop((270, 810, 310, 880)).get_flattened_data())
        assert logo_pixels.count((233, 144, 37)) > 100  # #E99025
        assert logo_pixels.count((36, 138, 118)) > 10  # #248A76
        gif = Image.open(OUT / "움직이는썸네일.gif")
        assert gif.size == (900, 900) and gif.n_frames >= 20 and gif.info.get("loop") == 0
        durations = []
        for index in range(gif.n_frames):
            gif.seek(index)
            durations.append(gif.info.get("duration", 0))
        assert 4800 <= sum(durations) <= 5200, sum(durations)
        if post["gif_effect"] in ["올라오기", "밀어내기"]:
            background = Image.open(OUT / "썸네일_배경.png").convert("RGB")
            positions = []
            for frame_number in [0, 6, 15]:
                gif.seek(frame_number)
                frame = gif.convert("RGB")
                coordinates = []
                for y in range(440, 800):
                    for x in range(900):
                        color = frame.getpixel((x, y))
                        if all(abs(a-b) <= 3 for a, b in zip(color, (233, 144, 37))) and max(abs(a-b) for a, b in zip(color, background.getpixel((x, y)))) > 40:
                            coordinates.append(y if post["gif_effect"] == "올라오기" else x)
                positions.append(min(coordinates) if coordinates else None)
            assert positions[0] is None and positions[1] is not None and positions[2] is not None
            if post["gif_effect"] == "올라오기":
                assert positions[1] > positions[2] + 25, "올라오기 효과의 이동 방향을 확인하세요"
            else:
                assert positions[1] < positions[2] - 25, "밀어내기 효과의 이동 방향을 확인하세요"
        assert "〔현장 사진 1〕" in (OUT / "편집기_붙여넣기.html").read_text(encoding="utf-8")
        assert (OUT / "편집기_붙여넣기.html").read_text(encoding="utf-8").startswith('<blockquote'), "상단 인용구 미반영"
        svg = (OUT / "썸네일_편집원본.svg").read_text(encoding="utf-8")
        assert f"data:image/png;base64,{logo}" in svg and svg.count(post["accent_color"]) == 4
        assert post["logo_star_color"] in svg and 'filter="url(#brand-colors)"' in svg
        print(f"PASS: 원본{len(originals)}장·로고 불변, 게시사진{len(post['photos'])}장·제외사진 미사용, 브랜드색2/15·30/배너순서/태그15/900px PNG·GIF {gif.n_frames}프레임·{sum(durations)}ms")
        return
    OUT.mkdir(exist_ok=True)
    fragments = []
    for b in post["blocks"]:
        value = html.escape(b.get("text", b.get("marker", ""))).replace("\n", "<br>")
        if b["type"] == "quote":
            fragments.append(f'<blockquote style="text-align:center;font-family:나눔명조;font-size:19px;font-style:italic;font-weight:normal;line-height:1.8;">{value}</blockquote>')
            continue
        if b.get("link"):
            value = f'<a href="{html.escape(b["link"], quote=True)}">{value}</a>'
        size = post["heading_size"] if b["type"] == "h" else post["body_size"]
        fragments.append(f'<p style="text-align:center;font-family:나눔고딕;font-size:{size}px;font-weight:normal;line-height:1.8;">{value}</p><p style="text-align:center;font-size:15px;font-weight:normal;"><br></p>')
    (OUT / "편집기_붙여넣기.html").write_text("".join(fragments), encoding="utf-8")
    (OUT / "본문.txt").write_text(post["title"] + "\n\n" + text, encoding="utf-8")
    tags = [" ".join("#" + t for t in post["tags"][i:i+3]) for i in range(0, 15, 3)]
    (OUT / "태그.txt").write_text("\n".join(tags), encoding="utf-8")
    (OUT / "태그_붙여넣기.html").write_text("".join(f'<p style="text-align:center;font-family:나눔고딕;font-size:15px;font-weight:normal;">{t}</p>' for t in tags), encoding="utf-8")
    photo = base64.b64encode((JOB / "01_원본사진" / post["cover"]).read_bytes()).decode()
    photo_mime = "image/png" if post["cover"].lower().endswith(".png") else "image/jpeg"
    font = base64.b64encode((ROOT / "assets/fonts/NanumSquareEB.ttf").read_bytes()).decode()
    # 원본 로고의 알파·형태·글자는 유지하고 SVG 필터로 두 브랜드색만 정규화한다.
    opening = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900">
<defs><style>@font-face{{font-family:CoverBold;src:url(data:font/ttf;base64,{font})}}text{{font-family:CoverBold,sans-serif}}</style>
<linearGradient id="edge"><stop stop-color="#d8ceb1"/><stop offset="1" stop-color="#d8ceb1" stop-opacity="0"/></linearGradient>
<linearGradient id="dark" x2="0" y2="1"><stop stop-opacity="0"/><stop offset="1" stop-opacity=".19"/></linearGradient>
<filter id="brand-colors" color-interpolation-filters="sRGB">
<feColorMatrix in="SourceGraphic" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 20 -20 0 0 0" result="orange-select"/>
<feComposite in="orange-select" in2="SourceAlpha" operator="in" result="orange-mask"/>
<feFlood flood-color="{post["accent_color"]}" result="orange"/><feComposite in="orange" in2="orange-mask" operator="in" result="orange-ink"/>
<feColorMatrix in="SourceGraphic" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -20 20 0 0 0" result="green-select"/>
<feComposite in="green-select" in2="SourceAlpha" operator="in" result="green-mask"/>
<feFlood flood-color="{post["logo_star_color"]}" result="green"/><feComposite in="green" in2="green-mask" operator="in" result="green-ink"/>
<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="orange-ink"/><feMergeNode in="green-ink"/></feMerge></filter></defs>
<image href="data:{photo_mime};base64,{photo}" width="900" height="900" preserveAspectRatio="xMidYMid slice"/>
<rect width="900" height="900" fill="url(#dark)"/>
<rect width="65" height="900" fill="url(#edge)"/><rect width="65" height="900" fill="url(#edge)" transform="translate(900 900) rotate(180)"/>
<rect width="65" height="900" fill="url(#edge)" transform="translate(900 0) rotate(90)"/><rect width="65" height="900" fill="url(#edge)" transform="translate(0 900) rotate(-90)"/>
<image id="brand" href="data:image/png;base64,{logo}" x="270" y="810" width="360" height="72" filter="url(#brand-colors)"/>'''
    lines = "".join(f'<text x="450" y="{565+i*100}" text-anchor="middle" font-size="78" fill="white" stroke="#242424" stroke-width="8" paint-order="stroke" stroke-linejoin="round">{html.escape(line)}</text>' for i, line in enumerate(post["thumbnail_lines"]))
    overlay = f'''<g id="headline">{lines}<path d="M170 710 Q440 692 755 714 M180 724 Q450 704 742 728" stroke="{post["accent_color"]}" stroke-width="8" stroke-linecap="round" fill="none"/>
<path d="m136 482 8 25 26-18-16 29 16 9-27 1-11 24 2-29-22-5 25-10z" fill="none" stroke="{post["accent_color"]}" stroke-width="5"/>
<path d="m770 638 12 17 14-3-9 12 7 13-16-5-12 10 2-19-11-8 15-1z" fill="none" stroke="{post["accent_color"]}" stroke-width="4"/></g>'''
    full = opening + overlay + "</svg>"
    base = opening + "</svg>"
    foreground_svg = opening.split('<image href=')[0] + overlay + "</svg>"
    (OUT / "썸네일_편집원본.svg").write_text(full, encoding="utf-8")
    (OUT / "썸네일_배경.svg").write_text(base, encoding="utf-8")
    (OUT / "썸네일_글자.svg").write_text(foreground_svg, encoding="utf-8")
    # ponytail: SVG 합성은 브라우저의 기본 렌더러를 사용한다. 문틀/유리 등 사진 픽셀을 재생성하지 않는다.
    page = '''<!doctype html><html lang="ko"><meta charset="utf-8"><title>금강이지스 섬네일 렌더</title><style>body{margin:0;background:#eee}#view{width:900px;height:900px}nav{padding:12px}button{padding:12px;margin:4px}</style><div id="view"></div><nav><button id="full">대표 PNG 내려받기</button><button id="base">배경 PNG 내려받기</button><button id="ink">글자 PNG 내려받기</button></nav><script>const art=ART; document.querySelector('#view').innerHTML=art.full;async function save(kind){const raw=art[kind];const img=new Image();img.src=URL.createObjectURL(new Blob([raw],{type:'image/svg+xml'}));await img.decode();const c=document.createElement('canvas');c.width=c.height=900;c.getContext('2d').drawImage(img,0,0);const a=document.createElement('a');a.download='금강이지스_명지_'+({full:'대표',base:'배경',ink:'글자'}[kind])+'.png';a.href=c.toDataURL('image/png');a.click();URL.revokeObjectURL(img.src)}document.querySelector('#full').onclick=()=>save('full');document.querySelector('#base').onclick=()=>save('base');document.querySelector('#ink').onclick=()=>save('ink');</script></html>'''.replace("ART", json.dumps({"full": full, "base": base, "ink": foreground_svg}, ensure_ascii=False))
    (OUT / "썸네일_렌더.html").write_text(page.replace("금강이지스_명지", post.get("download_prefix", "금강이지스_명지")), encoding="utf-8")
    print(f"생성: {OUT}; 원고 {len(text.replace(chr(10), ''))}자(공백 포함·줄바꿈 제외)")


if __name__ == "__main__":
    main()
