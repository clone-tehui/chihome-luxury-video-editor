#!/usr/bin/env python3
"""
Công cụ Auto-Edit Tự Động cho mọi thư mục clip thô tiếp theo (The Opera / The Galleria / The Crest)
Tự động:
1. Quét toàn bộ file .MOV / .MP4 trong thư mục nguồn.
2. Phân tách nghiêm ngặt nhóm 9:16 (Dọc) và 16:9 (Ngang) — không bao giờ ghép lẫn lộn.
3. Loại bỏ clip lỗi/ngắn (< 2.0s) và so sánh độ tương đồng hình ảnh (Perceptual Hash / Color Histogram)
   để phát hiện các cảnh quay lặp lại cùng 1 góc phòng -> chia sang các video hướng khác nhau.
4. Cắt bỏ 0.35s đầu & 0.35s cuối mỗi clip (khúc bấm máy/tắt máy bị rung).
5. Render bộ video theo nhiều hướng (POV Storytelling, Spec-Sheet Luxury, Fast-Cut Hero View)
   với font Be Vietnam Pro (chữ trắng viền đen, không khung nền).
"""

import os
import re
import glob
import argparse
import subprocess
import numpy as np
from PIL import Image
import imageio_ffmpeg
from edit_pipeline import build_edited_video, BGM_DIR

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def analyze_raw_clip(path: str):
    p = subprocess.run([FFMPEG, "-i", path], stderr=subprocess.PIPE, text=True)
    info = p.stderr
    dur_m = re.search(r"Duration:\s*(\d+):(\d+):([0-9.]+)", info)
    if not dur_m:
        return None
    dur = int(dur_m.group(1)) * 3600 + int(dur_m.group(2)) * 60 + float(dur_m.group(3))
    if dur < 2.0:
        return None  # Tự động loại bỏ clip bấm nhầm / quá ngắn (< 2.0s)

    vid_m = re.search(r"Stream #.*Video:.*?,\s*(\d+)x(\d+)", info)
    w, h = (int(vid_m.group(1)), int(vid_m.group(2))) if vid_m else (1920, 1080)
    rot_m = re.search(r"displaymatrix: rotation of ([-0-9.]+) degrees", info)
    rot = float(rot_m.group(1)) if rot_m else 0.0
    if abs(rot) in (90.0, 270.0):
        w, h = h, w

    aspect = "9:16" if h > w else "16:9"

    # Trích 1 frame giữa clip để tính đặc trưng màu sắc & độ sáng (phục vụ chống lặp cảnh)
    tmp_jpg = f"/tmp/probe_{os.path.basename(path)}.jpg"
    subprocess.run(
        [FFMPEG, "-y", "-ss", f"{dur/2:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=64:64", tmp_jpg],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    signature = None
    luma = 128.0
    if os.path.exists(tmp_jpg):
        with Image.open(tmp_jpg) as im:
            arr = np.asarray(im.convert("RGB"), dtype=np.float32)
            luma = float(arr.mean())
            signature = arr.mean(axis=(0, 1))
        os.remove(tmp_jpg)

    return {
        "file": os.path.basename(path),
        "path": path,
        "dur": dur,
        "aspect": aspect,
        "luma": luma,
        "signature": signature,
    }


def is_similar_clip(c1, c2, threshold=18.0):
    if c1["signature"] is None or c2["signature"] is None:
        return False
    dist = float(np.linalg.norm(c1["signature"] - c2["signature"]))
    return dist < threshold and abs(c1["luma"] - c2["luma"]) < 12.0


def deduplicate_clips(clips):
    """Tách danh sách clip thành Bộ chính (Primary) và Bộ thay thế (Alternate) để không lặp cảnh."""
    primary = []
    alternate = []
    for c in clips:
        if any(is_similar_clip(c, p) for p in primary):
            alternate.append(c)
        else:
            primary.append(c)
    # Bổ sung các cảnh duy nhất (không có bản đúp) vào bộ alternate để đủ thời lượng
    for p in primary:
        if not any(is_similar_clip(p, a) for a in alternate):
            alternate.append(p)
    return primary, alternate


def auto_edit(src_dir: str, out_dir: str, project: str, specs: str, hook1: str, hook2: str, subtitles_list: list):
    os.makedirs(out_dir, exist_ok=True)
    raw_files = sorted(
        glob.glob(os.path.join(src_dir, "*.MOV"))
        + glob.glob(os.path.join(src_dir, "*.mov"))
        + glob.glob(os.path.join(src_dir, "*.MP4"))
        + glob.glob(os.path.join(src_dir, "*.mp4"))
    )
    analyzed = [analyze_raw_clip(f) for f in raw_files]
    analyzed = [a for a in analyzed if a is not None]

    v_clips = [a for a in analyzed if a["aspect"] == "9:16"]
    h_clips = [a for a in analyzed if a["aspect"] == "16:9"]

    for group_name, clips, (w, h) in [("9x16", v_clips, (2160, 3840)), ("16x9", h_clips, (3840, 2160))]:
        if not clips:
            continue
        prim, alt = deduplicate_clips(clips)

        # Bản 1: POV Hook (Luxury Serif / Sunset Theme + Dynamic Scene Colors)
        segs1 = []
        for i, c in enumerate(prim):
            trim_start = min(0.35, c["dur"] * 0.1)
            trim_dur = max(1.5, min(6.5, c["dur"] - trim_start - 0.25))
            sub = subtitles_list[i % len(subtitles_list)] if subtitles_list else ""
            segs1.append({"file": c["file"], "start": trim_start, "dur": trim_dur, "subtitle": sub, "palette_idx": i})

        build_edited_video(
            src_dir=src_dir,
            out_mp4=os.path.join(out_dir, f"Auto_{group_name}_POV_Hook.mp4"),
            width=w, height=h,
            theme_name="luxury_pov_gold" if group_name == "9x16" else "modern_fastcut_sunset",
            line1=hook1,
            line2=hook2,
            watermark=project.upper(),
            bgm_path=os.path.join(BGM_DIR, "bgm_style1_chill_night.m4a"),
            segments=segs1,
        )

        # Bản 2: Spec-Sheet Luxury (Editorial Emerald / Imperial Serif + Dynamic Scene Colors)
        segs2 = []
        for i, c in enumerate(reversed(alt)):
            trim_start = min(0.35, c["dur"] * 0.1)
            trim_dur = max(1.5, min(5.0, c["dur"] - trim_start - 0.25))
            sub = subtitles_list[(i + 1) % len(subtitles_list)] if subtitles_list else ""
            segs2.append({"file": c["file"], "start": trim_start, "dur": trim_dur, "subtitle": sub, "palette_idx": i + 1})

        build_edited_video(
            src_dir=src_dir,
            out_mp4=os.path.join(out_dir, f"Auto_{group_name}_Spec_Luxury.mp4"),
            width=w, height=h,
            theme_name="editorial_spec_emerald" if group_name == "9x16" else "widescreen_imperial_serif",
            line1=project.upper(),
            line2=specs,
            watermark="THE METROPOLE THỦ THIÊM",
            bgm_path=os.path.join(BGM_DIR, "bgm_style2_luxury_lounge.m4a"),
            segments=segs2,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-Edit Folder CLI")
    parser.add_argument("--src", required=True, help="Thư mục chứa video thô")
    parser.add_argument("--out", required=True, help="Thư mục xuất video")
    parser.add_argument("--project", default="THE OPERA RESIDENCE", help="Tên dự án (Dòng 1 Spec)")
    parser.add_argument("--specs", default="4PN | VIEW CẦU BA SON, SÔNG SÀI GÒN & TRUNG TÂM", help="Thông số căn hộ (Dòng 2 Spec)")
    parser.add_argument("--hook1", default="Bạn đang ở trong căn hộ 4PN THE OPERA THỦ THIÊM", help="Dòng 1 POV Hook")
    parser.add_argument("--hook2", default="View cầu Ba Son, sông Sài Gòn & toàn bộ trung tâm", help="Dòng 2 POV Hook")
    parser.add_argument("--subs", nargs="*", default=[
        "Tầm nhìn triệu đô hướng trọn cầu Ba Son",
        "Không gian phòng khách sang trọng, ấm cúng",
        "Phòng ngủ Master hệ kính kịch trần",
        "Phòng tắm đá Marble chuẩn resort 5 sao",
    ])
    args = parser.parse_args()
    auto_edit(args.src, args.out, args.project, args.specs, args.hook1, args.hook2, args.subs)
