import base64
import mimetypes
from pathlib import Path

here = Path(__file__).parent
img_dir = here / "images"
video_dir = here / "videos"

mapping = {
    "__IMG_RAW_TRACE__": img_dir / "page1_img3.png",
    "__IMG_ARTIFACT_UNFILTERED__": img_dir / "page2_img1.png",
    "__IMG_ARTIFACT_FILTERED__": img_dir / "page2_img2.png",
    "__IMG_THETA_P1__": img_dir / "page1_img2.png",
    "__IMG_THETA_P2__": img_dir / "page1_img1.png",
    "__IMG_ERP__": img_dir / "page3_img1.png",
    "__IMG_SLICER__": img_dir / "slicer_targeting.png",
    "__IMG_GTEC__": img_dir / "bcicore8.jpg",
    "__IMG_TTL_TRIGGER__": img_dir / "ttl_trigger_pulse_train.png",
    "__VIDEO_2BACK__": video_dir / "2back_task.mp4",
}

html = (here / "poster_template.html").read_text(encoding="utf-8")

for token, path in mapping.items():
    mime, _ = mimetypes.guess_type(path.name)
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    uri = f"data:{mime};base64,{b64}"
    count = html.count(token)
    html = html.replace(token, uri)
    print(f"{token} -> {count} occurrence(s), {mime}, {path.stat().st_size:,} bytes source")

out_path = here / "lifu_poster.html"
out_path.write_text(html, encoding="utf-8")
print(f"Wrote {out_path} ({len(html):,} bytes)")
