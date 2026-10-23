#!/usr/bin/env python3
"""
Quy Trình Edit Video Bất Động Sản Cao Cấp — Thương Hiệu CHIHOME (www.chihome.vn)
Chuyên Căn Hộ Dịch Vụ Hạng Sang: The Opera, The Galleria, The Crest (The Metropole Thủ Thiêm)
Mô phỏng chính xác phong cách 2 kênh TikTok: @thaitairealtor & @ban_va_cho_thue_can_ho

Kiến trúc Thế Hệ Mới (Signature Header vs. Dynamic Subtitle + Contextual xfade Transitions):
1. PHÂN BIỆT RÕ RÀNG GIỮA TIÊU ĐỀ (HEADER) VÀ PHỤ ĐỀ CHẠY THEO CẢNH (SUBTITLE):
   - TIÊU ĐỀ (Header — Thông tin căn hộ):
     + Đồng bộ 1 màu thống nhất trên toàn bộ khối Tiêu đề của 1 video (tạo nhận diện thương hiệu kênh).
     + Sử dụng Font Serif Hoàng Gia cỡ lớn (Cormorant Garamond Bold / Playfair Display Bold) kết hợp
       Montserrat SemiBold, đường kẻ chỉ Kim Cương đồng màu, viền chữ Đen Obsidian dày sắc nét (4px ở 4K)
       kèm Hào quang Bóng đổ sâu và lớp Sương mờ Thượng lưu nhẹ ở đỉnh khung hình (Top Soft Vignette).
     + Giữ CỐ ĐỊNH xuyên suốt toàn bộ video (không bị trượt hay nhấp nháy khi chuyển cảnh).
   - PHỤ ĐỀ MIÊU TẢ (Dynamic Subtitle — Chữ chạy theo tình huống từng cảnh):
     + Sử dụng Font chữ KHÁC HẲN Tiêu đề (Plus Jakarta Sans Medium / Playfair Display Italic).
     + Sử dụng Màu sắc KHÁC HẲN Tiêu đề (đồng nhất 1 màu sang trọng trên mỗi câu phụ đề, biến thiên
       màu sắc qua từng clip và từng phân cảnh để không bị nhàm chán).
     + Sử dụng Viền chữ KHÁC HẲN Tiêu đề (viền Nâu Espresso / Xám Khói mảnh 2px ở 4K + bóng đổ sương mờ mềm).
     + Tự động xuất hiện/ẩn đi khớp theo từng phân cảnh (ẩn đi trong lúc chuyển cảnh và hiện lên khi vào cảnh mới).
2. CHUYỂN CẢNH MƯỢT MÀ THEO TÌNH HUỐNG (CONTEXTUAL XFADE TRANSITIONS):
   - Áp dụng bộ chuyển cảnh xfade (zoomin, smoothleft, smoothright, hblur, fade, smoothup, circleopen)
     tùy biến theo đúng hướng lia máy và không gian chuyển tiếp giữa 2 phòng.
3. GIỮ NGUYÊN 100% CHẤT LƯỢNG GỐC 4K 10-BIT HDR (HEVC Main 10, p010le, BT.2020 HLG, 59.94 fps, ~75-80 Mbps)
   và gắn Logo chính thức của thương hiệu chiHome ("chiHome — your dream - your home").
"""

import os
import shutil
import argparse
import subprocess
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = "/Users/apple/.gemini/antigravity/scratch/luxury-video-editor"
FONT_DIR = os.path.join(BASE_DIR, "fonts")
BGM_DIR = os.path.join(BASE_DIR, "bgm")
LOGO_PATH = os.path.join(BASE_DIR, "brand", "chihome-logo-video-ready.png")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def load_luxury_font(filename: str, size: int, weight: int = 600) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(FONT_DIR, "BeVietnamPro-SemiBold.ttf")
    font = ImageFont.truetype(path, size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        pass
    return font


def draw_tracked_uniform_line(
    canvas: Image.Image,
    center_x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color=(255, 255, 255, 255),
    tracking_px: float = 3.0,
    word_space_extra: float = 4.0,
    stroke_width: int = 3,
    stroke_fill=(10, 14, 20, 235),
    shadow_offset=(0, 6),
    shadow_blur: int = 14,
    glow_alpha: int = 190,
    max_width: int = None,
    font_filename: str = None,
    font_weight: int = 600,
) -> int:
    """
    Vẽ 1 dòng chữ đồng nhất 1 màu sang trọng với:
    - Tự động co giãn cỡ chữ & khoảng cách (Auto-Fit Safe Width) để KHÔNG BAO GIỜ bị tràn lề
      khi đăng lên màn hình iPhone 19.5:9 của TikTok (vốn tự crop ~5.5% mỗi bên trái/phải).
    - Giãn cách ký tự (tracking_px) & giãn cách từ (word_space_extra) vừa vặn, tinh tế.
    - Viền chữ (stroke_width, stroke_fill) & đổ bóng 2 tầng tùy chỉnh riêng cho Header vs Subtitle.
    """
    if not text:
        return 0

    clean_text = text.replace("{", "").replace("}", "")
    chars = list(clean_text)
    n = len(chars)
    if n == 0:
        return 0

    w_canvas, h_canvas = canvas.size
    is_vert = h_canvas > w_canvas
    if max_width is None:
        # Trên TikTok dọc (9:16), màn hình iPhone crop ~5.5% mỗi bên -> giới hạn chữ trong 72% chiều ngang
        max_width = int(w_canvas * (0.72 if is_vert else 0.82))

    def compute_advances(f_obj, trk, w_extra):
        advs = []
        for i, ch in enumerate(chars):
            if i < n - 1:
                base_adv = f_obj.getlength(ch + chars[i + 1]) - f_obj.getlength(chars[i + 1])
            else:
                base_adv = f_obj.getlength(ch)
            extra = trk if i < n - 1 else 0.0
            if ch == " " and i < n - 1:
                extra += w_extra
            advs.append(base_adv + extra)
        return advs

    advances = compute_advances(font, tracking_px, word_space_extra)
    total_w = sum(advances)

    # Nếu tổng chiều ngang vượt quá vùng an toàn TikTok (max_width), tự động thu nhỏ font & tracking
    if total_w > max_width and total_w > 0:
        ratio = (max_width / total_w) * 0.97
        tracking_px = max(0.8, tracking_px * ratio)
        word_space_extra = max(1.5, word_space_extra * ratio)
        if font_filename:
            new_size = max(18, int(font.size * ratio))
            font = load_luxury_font(font_filename, new_size, font_weight)
        advances = compute_advances(font, tracking_px, word_space_extra)
        total_w = sum(advances)

    start_x = center_x - (total_w / 2.0)

    # Lớp 1: Hào quang bóng đổ khuếch tán rộng (Ambient Luxury Shadow)
    ambient_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    a_draw = ImageDraw.Draw(ambient_layer)
    cur_x = start_x
    for ch, adv in zip(chars, advances):
        if ch != " ":
            a_draw.text(
                (cur_x + shadow_offset[0], y + shadow_offset[1]),
                ch,
                font=font,
                fill=(0, 0, 0, glow_alpha),
                stroke_width=stroke_width + 3,
                stroke_fill=(0, 0, 0, glow_alpha),
            )
        cur_x += adv
    if shadow_blur > 0:
        ambient_layer = ambient_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas.alpha_composite(ambient_layer)

    # Lớp 2: Bóng đổ sát chân chữ (Contact Shadow)
    contact_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(contact_layer)
    cur_x = start_x
    for ch, adv in zip(chars, advances):
        if ch != " ":
            c_draw.text(
                (cur_x, y + max(2, shadow_offset[1] // 2)),
                ch,
                font=font,
                fill=(0, 0, 0, min(230, glow_alpha + 20)),
                stroke_width=stroke_width + 1,
                stroke_fill=(0, 0, 0, min(230, glow_alpha + 20)),
            )
        cur_x += adv
    contact_layer = contact_layer.filter(ImageFilter.GaussianBlur(radius=max(2, shadow_blur // 3)))
    canvas.alpha_composite(contact_layer)

    # Lớp 3: Chữ chính sắc nét + Viền chữ riêng biệt
    draw = ImageDraw.Draw(canvas)
    cur_x = start_x
    for ch, adv in zip(chars, advances):
        if ch != " ":
            draw.text(
                (cur_x, y),
                ch,
                font=font,
                fill=fill_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
        cur_x += adv

    ascent, descent = font.getmetrics()
    return ascent + descent


def draw_luxury_divider(canvas: Image.Image, center_x: int, y: int, half_len: int, color: tuple, scale: float):
    """
    Vẽ đường kẻ chỉ mảnh trang trí (Luxury Ornamental Hairline + Viên kim cương ở tâm)
    đồng bộ màu với Tiêu đề, giúp tách biệt Dòng 1 và Dòng 2 sang trọng, nổi bật.
    """
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    line_h = max(2, int(1.5 * scale))
    gap_center = int(18 * scale)

    # Bóng mờ nhẹ dưới đường kẻ chỉ
    draw.line(
        [(center_x - half_len, y + int(2 * scale)), (center_x - gap_center, y + int(2 * scale))],
        fill=(0, 0, 0, 140),
        width=line_h + 2,
    )
    draw.line(
        [(center_x + gap_center, y + int(2 * scale)), (center_x + half_len, y + int(2 * scale))],
        fill=(0, 0, 0, 140),
        width=line_h + 2,
    )

    # Đường chỉ chính
    draw.line([(center_x - half_len, y), (center_x - gap_center, y)], fill=color, width=line_h)
    draw.line([(center_x + gap_center, y), (center_x + half_len, y)], fill=color, width=line_h)

    r = int(5.5 * scale)
    diamond = [
        (center_x, y - r),
        (center_x + r, y),
        (center_x, y + r),
        (center_x - r, y),
    ]
    draw.polygon(diamond, fill=color, outline=(10, 12, 16, 200))
    canvas.alpha_composite(layer)


# =========================================================================
# CẤU HÌNH PHÂN BIỆT RÕ RÀNG: TIÊU ĐỀ (HEADER) VS. PHỤ ĐỀ (SUBTITLE)
# =========================================================================
# Mỗi theme quy định:
# 1. HEADER: 1 Màu đồng nhất sang trọng + Font Hiện Đại Tối Giản (Montserrat / Manrope) thẳng hàng 100%
#            các chữ số (3PN, 4PN không bao giờ bị nhảy lệch dòng) + Viền Obsidian dày sắc nét (4px ở 4K)
# 2. SUBTITLE: Font chữ KHÁC HẲN Header (Be Vietnam Pro Medium / Plus Jakarta Sans) dễ đọc tức thì +
#              Viền chữ mảnh mềm (2px ở 4K màu Nâu Espresso / Xám Khói) +
#              Bảng màu Phụ đề KHÁC HẲN màu Header và biến thiên theo từng cảnh!
VIDEO_STYLE_THEMES = {
    # Theme 1: Tiêu đề Vàng Champagne Hoàng Gia (Montserrat Bold/SemiBold — Tối giản, sang trọng, chữ số 3PN/4PN thẳng tắp)
    #          Phụ đề Font Be Vietnam Pro Medium (Thanh thoát, dễ nhìn dễ đọc) đổi màu Trắng Ngọc Trai / Xanh Ngọc / Kem Ngà
    "imperial_gold_header": {
        "h1_file": "Montserrat-Variable.ttf",
        "h1_weight": 750,
        "h1_size_v": 28.5,
        "h1_size_h": 34.0,
        "h1_track": 3.0,
        "h2_file": "Montserrat-Variable.ttf",
        "h2_weight": 600,
        "h2_size_v": 17.5,
        "h2_size_h": 20.5,
        "h2_track": 1.8,
        "header_color": (255, 226, 148, 255),        # Đồng bộ 1 màu Vàng Champagne Hoàng Gia
        "header_stroke_w": 2.0,                      # ~4.0px ở 4K (Sắc nét, nổi bật)
        "header_stroke_color": (10, 12, 16, 245),    # Đen Obsidian đậm
        # Phụ đề: Font Be Vietnam Pro Medium (Khác biệt rõ với Montserrat In Hoa của Tiêu đề, cực kỳ dễ đọc)
        "sub_file": "BeVietnamPro-Medium.ttf",
        "sub_weight": 500,
        "sub_size_v": 20.5,
        "sub_size_h": 23.0,
        "sub_track": 1.2,
        "sub_stroke_w": 1.0,                         # ~2.0px ở 4K (Viền mảnh thanh thoát, khác hẳn Header)
        "sub_stroke_color": (22, 26, 32, 205),       # Xám Khói Đậm mềm mại
        "sub_colors": [
            (255, 255, 255, 255),                    # Cảnh 1: Trắng Ngọc Trai Tinh Khiết
            (212, 252, 236, 255),                    # Cảnh 2: Xanh Ngọc Bích ChiHome Nhạt
            (255, 246, 224, 255),                    # Cảnh 3: Trắng Kem Ngà Ấm
            (220, 244, 255, 255),                    # Cảnh 4: Xanh Băng Pha Lê
            (255, 236, 226, 255),                    # Cảnh 5: Hồng Champagne Nhạt
        ],
    },
    # Theme 2: Tiêu đề Trắng Kim Cương (Manrope ExtraBold/SemiBold — Kiến trúc tối giản Châu Âu, 3PN/4PN thẳng tắp)
    #          Phụ đề Font Plus Jakarta Sans SemiBold đổi màu Vàng Champagne / Hổ Phách / Ngọc Lục Bảo
    "diamond_white_header": {
        "h1_file": "Manrope-Variable.ttf",
        "h1_weight": 800,
        "h1_size_v": 29.0,
        "h1_size_h": 34.5,
        "h1_track": 3.0,
        "h2_file": "Manrope-Variable.ttf",
        "h2_weight": 600,
        "h2_size_v": 17.5,
        "h2_size_h": 20.5,
        "h2_track": 1.8,
        "header_color": (255, 255, 255, 255),        # Đồng bộ 1 màu Trắng Kim Cương
        "header_stroke_w": 2.0,                      # ~4.0px ở 4K
        "header_stroke_color": (8, 12, 18, 245),     # Đen Obsidian đậm
        # Phụ đề: Font Plus Jakarta Sans SemiBold (Hiện đại, gọn gàng, không uốn lượn rối mắt, khác hẳn Header)
        "sub_file": "PlusJakartaSans-Variable.ttf",
        "sub_weight": 600,
        "sub_size_v": 21.0,
        "sub_size_h": 23.5,
        "sub_track": 1.2,
        "sub_stroke_w": 1.0,                         # ~2.0px ở 4K (Viền mảnh Nâu Espresso)
        "sub_stroke_color": (28, 18, 10, 210),
        "sub_colors": [
            (255, 228, 150, 255),                    # Cảnh 1: Vàng Champagne Sáng
            (204, 250, 232, 255),                    # Cảnh 2: Xanh Ngọc Lục Bảo Nhạt
            (255, 216, 132, 255),                    # Cảnh 3: Vàng Hổ Phách Nhạt
            (218, 243, 255, 255),                    # Cảnh 4: Xanh Pha Lê Tuyết
            (255, 238, 186, 255),                    # Cảnh 5: Vàng Kem Ánh Kim
            (255, 228, 210, 255),                    # Cảnh 6: Hồng Đào Champagne
            (255, 222, 140, 255),                    # Cảnh 7: Vàng Hoàng Gia
        ],
    },
    # Theme 3 (Cho bản 16:9 Ngang): Tiêu đề Vàng Hoàng Gia (Montserrat) + Phụ đề Be Vietnam Pro Thanh Lịch
    "widescreen_imperial_serif": {
        "h1_file": "Montserrat-Variable.ttf",
        "h1_weight": 750,
        "h1_size_v": 28.5,
        "h1_size_h": 34.0,
        "h1_track": 3.4,
        "h2_file": "Montserrat-Variable.ttf",
        "h2_weight": 600,
        "h2_size_v": 17.5,
        "h2_size_h": 20.5,
        "h2_track": 2.4,
        "header_color": (255, 226, 148, 255),
        "header_stroke_w": 2.0,
        "header_stroke_color": (10, 10, 12, 245),
        "sub_file": "BeVietnamPro-Medium.ttf",
        "sub_weight": 500,
        "sub_size_v": 20.5,
        "sub_size_h": 23.0,
        "sub_track": 1.5,
        "sub_stroke_w": 1.0,
        "sub_stroke_color": (24, 28, 34, 205),
        "sub_colors": [
            (255, 255, 255, 255),
            (214, 252, 236, 255),
            (255, 244, 216, 255),
            (220, 244, 255, 255),
            (255, 236, 224, 255),
        ],
    },
    # Theme 4 (Cho bản 16:9 Fast-Cut): Tiêu đề Kem Ngọc Trai Ấm (Manrope) + Phụ đề Plus Jakarta Sans Đa Sắc
    "modern_fastcut_sunset": {
        "h1_file": "Manrope-Variable.ttf",
        "h1_weight": 800,
        "h1_size_v": 29.0,
        "h1_size_h": 34.5,
        "h1_track": 3.2,
        "h2_file": "Manrope-Variable.ttf",
        "h2_weight": 600,
        "h2_size_v": 17.5,
        "h2_size_h": 20.5,
        "h2_track": 2.2,
        "header_color": (255, 250, 240, 255),
        "header_stroke_w": 2.0,
        "header_stroke_color": (10, 12, 16, 245),
        "sub_file": "PlusJakartaSans-Variable.ttf",
        "sub_weight": 600,
        "sub_size_v": 21.0,
        "sub_size_h": 23.5,
        "sub_track": 1.4,
        "sub_stroke_w": 1.0,
        "sub_stroke_color": (28, 18, 10, 210),
        "sub_colors": [
            (255, 228, 150, 255),
            (204, 250, 232, 255),
            (255, 216, 132, 255),
            (218, 243, 255, 255),
            (255, 238, 186, 255),
        ],
    },
}
# Tương thích tên theme cũ
VIDEO_STYLE_THEMES["luxury_pov_gold"] = VIDEO_STYLE_THEMES["imperial_gold_header"]
VIDEO_STYLE_THEMES["editorial_spec_emerald"] = VIDEO_STYLE_THEMES["diamond_white_header"]


def create_master_header_logo_png(
    out_path: str,
    width: int,
    height: int,
    theme_name: str,
    line1: str,
    line2: str,
    logo_path: str = LOGO_PATH,
):
    """
    Tạo Lớp Phủ Cố Định (Master Persistent Overlay PNG 4K) chuẩn Vùng An Toàn TikTok (TikTok Safe Zone):
    - Trên khung dọc 9:16, dịch khối Tiêu đề xuống y = 13.2% chiều cao (nằm hoàn toàn bên dưới thanh
      'LIVE | Cộng đồng | Bạn bè | Đã follow | Đề xuất' của TikTok).
    - Tự động giới hạn chiều ngang chữ trong 72% bề rộng khung hình (tránh bị crop 2 mép trái/phải
      trên màn hình iPhone 19.5:9).
    - Đưa Logo chiHome và Phụ đề lên vùng an toàn (trên thẻ vị trí '📍 The Metropole Thủ thiêm' của TikTok).
    """
    is_vertical = height > width
    scale = (width / 1080.0) if is_vertical else (width / 1920.0)
    theme = VIDEO_STYLE_THEMES.get(theme_name, VIDEO_STYLE_THEMES["imperial_gold_header"])

    # Tạo lớp Vignette chuyển sắc tự nhiên ở đỉnh và đáy
    grad = np.zeros((height, width, 4), dtype=np.uint8)
    top_vh = int(height * (0.24 if is_vertical else 0.22))
    for y in range(top_vh):
        alpha = int(90 * ((1.0 - (y / float(top_vh))) ** 1.6))
        grad[y, :, 3] = alpha

    bot_vh = int(height * (0.26 if is_vertical else 0.25))
    for y in range(height - bot_vh, height):
        t = (y - (height - bot_vh)) / float(bot_vh)
        alpha = int(80 * (t ** 1.6))
        grad[y, :, 3] = alpha

    canvas = Image.fromarray(grad, mode="RGBA")
    cx = width // 2

    f1_size = int((theme["h1_size_v"] if is_vertical else theme["h1_size_h"]) * scale)
    f2_size = int((theme["h2_size_v"] if is_vertical else theme["h2_size_h"]) * scale)
    f1 = load_luxury_font(theme["h1_file"], f1_size, theme["h1_weight"])
    f2 = load_luxury_font(theme["h2_file"], f2_size, theme["h2_weight"])

    # Dịch xuống 13.2% chiều cao trên bản dọc 9:16 để không chạm thanh tab trên cùng của TikTok
    top_y = int(height * (0.072 if is_vertical else 0.052))
    h_color = theme["header_color"]
    h_stroke_w = max(2, int(theme["header_stroke_w"] * scale))
    h_stroke_c = theme["header_stroke_color"]
    safe_max_w = int(width * (0.72 if is_vertical else 0.82))

    # Dòng 1 Tiêu đề (Vừa vặn trong vùng an toàn TikTok)
    h1_height = draw_tracked_uniform_line(
        canvas,
        center_x=cx,
        y=top_y,
        text=line1.upper(),
        font=f1,
        fill_color=h_color,
        tracking_px=theme["h1_track"] * scale,
        word_space_extra=4.0 * scale,
        stroke_width=h_stroke_w,
        stroke_fill=h_stroke_c,
        shadow_offset=(0, int(3.5 * scale)),
        shadow_blur=int(8 * scale),
        glow_alpha=205,
        max_width=safe_max_w,
        font_filename=theme["h1_file"],
        font_weight=theme["h1_weight"],
    )

    # Đường kẻ chỉ Kim Cương đồng bộ màu Tiêu đề
    divider_y = top_y + int(h1_height * 1.02) + int(8 * scale)
    draw_luxury_divider(
        canvas,
        center_x=cx,
        y=divider_y,
        half_len=int((165 if is_vertical else 220) * scale),
        color=(h_color[0], h_color[1], h_color[2], 220),
        scale=scale,
    )

    # Dòng 2 Tiêu đề (Thu gọn khoảng cách & kích thước để nằm gọn 100% trong khung TikTok)
    line2_y = divider_y + int(16 * scale)
    draw_tracked_uniform_line(
        canvas,
        center_x=cx,
        y=line2_y,
        text=line2.upper(),
        font=f2,
        fill_color=h_color,
        tracking_px=theme["h2_track"] * scale,
        word_space_extra=3.5 * scale,
        stroke_width=max(2, h_stroke_w - 1),
        stroke_fill=h_stroke_c,
        shadow_offset=(0, int(3 * scale)),
        shadow_blur=int(6 * scale),
        glow_alpha=190,
        max_width=safe_max_w,
        font_filename=theme["h2_file"],
        font_weight=theme["h2_weight"],
    )

    # Gắn Logo chính thức chiHome ("your dream - your home") ở vùng an toàn
    if logo_path and os.path.exists(logo_path):
        logo_im = Image.open(logo_path).convert("RGBA")
        target_logo_w = int((195 if is_vertical else 245) * scale)
        target_logo_h = int(logo_im.height * target_logo_w / logo_im.width)
        logo_resized = logo_im.resize((target_logo_w, target_logo_h), Image.Resampling.LANCZOS)
        lx = (width - target_logo_w) // 2
        # Trên bản dọc 9:16, đặt ở 66.2% (ngay phía trên thẻ vị trí & caption TikTok)
        ly = int(height * (0.662 if is_vertical else 0.882))
        canvas.paste(logo_resized, (lx, ly), logo_resized)

    canvas.save(out_path, "PNG")


def create_scene_subtitle_png(
    out_path: str,
    width: int,
    height: int,
    theme_name: str,
    subtitle: str,
    scene_index: int = 0,
):
    """
    Tạo Lớp Phủ Phụ Đề Động (Dynamic Scene Subtitle PNG 4K) chuẩn Vùng An Toàn TikTok:
    - Đặt ở y = 62.0% chiều cao trên bản dọc 9:16 (hoàn toàn phía trên thẻ vị trí '📍 The Metropole Thủ thiêm')
    - Tự động co giãn để nằm gọn trong 72% chiều ngang khung hình.
    """
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if not subtitle:
        canvas.save(out_path, "PNG")
        return

    cx = width // 2
    is_vertical = height > width
    scale = (width / 1080.0) if is_vertical else (width / 1920.0)
    theme = VIDEO_STYLE_THEMES.get(theme_name, VIDEO_STYLE_THEMES["imperial_gold_header"])

    sub_colors = theme["sub_colors"]
    sub_color = sub_colors[scene_index % len(sub_colors)]

    sub_size = int((theme["sub_size_v"] if is_vertical else theme["sub_size_h"]) * scale)
    f_sub = load_luxury_font(theme["sub_file"], sub_size, theme["sub_weight"])
    sub_stroke_w = max(2, int(theme["sub_stroke_w"] * scale))
    sub_stroke_c = theme["sub_stroke_color"]
    safe_max_w = int(width * (0.72 if is_vertical else 0.82))

    sub_lines = [s.strip() for s in subtitle.split("\n") if s.strip()]
    ascent, descent = f_sub.getmetrics()
    line_step = int((ascent + descent) * 1.72)

    if len(sub_lines) == 1:
        base_sub_y = int(height * (0.620 if is_vertical else 0.785))
    else:
        base_sub_y = int(height * (0.585 if is_vertical else 0.730))

    for idx, s_line in enumerate(sub_lines):
        cur_y = base_sub_y + idx * line_step
        draw_tracked_uniform_line(
            canvas,
            center_x=cx,
            y=cur_y,
            text=s_line,
            font=f_sub,
            fill_color=sub_color,
            tracking_px=theme["sub_track"] * scale,
            word_space_extra=3.8 * scale,
            stroke_width=sub_stroke_w,
            stroke_fill=sub_stroke_c,
            shadow_offset=(0, int(3 * scale)),
            shadow_blur=int(6 * scale),
            glow_alpha=170,
            max_width=safe_max_w,
            font_filename=theme["sub_file"],
            font_weight=theme["sub_weight"],
        )

    canvas.save(out_path, "PNG")


def build_edited_video(
    src_dir: str,
    out_mp4: str,
    width: int,
    height: int,
    theme_name: str,
    line1: str,
    line2: str,
    watermark: str,
    bgm_path: str,
    segments: list,
):
    """
    Quy trình dựng video 4K 10-bit HDR với:
    1. Chuyển cảnh mượt mà theo tình huống (Contextual xfade: zoomin, smoothleft, smoothright, hblur, fade, circleopen)
    2. Tiêu đề (Header) & Logo ChiHome giữ cố định xuyên suốt toàn bộ video
    3. Phụ đề (Subtitle) có Font, Màu sắc và Viền chữ riêng biệt, tự động xuất hiện theo từng phân cảnh.
    """
    work_dir = f"/tmp/build_{os.path.basename(out_mp4)}"
    os.makedirs(work_dir, exist_ok=True)

    # Danh sách hiệu ứng chuyển cảnh mặc định theo mạch không gian nếu phân cảnh chưa chỉ định
    default_transitions = ["smoothleft", "fade", "smoothright", "hblur", "smoothup", "circleopen"]

    try:
        valid_segs = []
        for seg in segments:
            mov_path = os.path.join(src_dir, seg["file"])
            if os.path.exists(mov_path):
                s_copy = dict(seg)
                s_copy["path"] = mov_path
                valid_segs.append(s_copy)

        if not valid_segs:
            return

        # 1. Tạo Master Header + Logo PNG cố định
        master_png = os.path.join(work_dir, "master_header_logo.png")
        create_master_header_logo_png(
            master_png,
            width=width,
            height=height,
            theme_name=theme_name,
            line1=line1,
            line2=line2,
            logo_path=LOGO_PATH,
        )

        # 2. Tạo các file Subtitle PNG riêng cho từng phân cảnh
        sub_pngs = []
        for i, seg in enumerate(valid_segs):
            sp = os.path.join(work_dir, f"sub_{i:02d}.png")
            create_scene_subtitle_png(
                sp,
                width=width,
                height=height,
                theme_name=theme_name,
                subtitle=seg.get("subtitle", ""),
                scene_index=seg.get("palette_idx", i),
            )
            sub_pngs.append(sp)

        # 3. Xây dựng Filtergraph FFmpeg kết hợp:
        #    - Chuỗi xfade mượt mà giữa các clip gốc 4K 10-bit HDR ở 59.94 fps
        #    - Lớp phủ Master Header + Logo cố định xuyên suốt
        #    - Các lớp phủ Subtitle xuất hiện chuẩn xác trong khung giờ của từng cảnh (ẩn đi lúc giao thoa chuyển cảnh)
        cmd = [FFMPEG, "-y"]
        for seg in valid_segs:
            cmd.extend(["-ss", f"{seg['start']:.2f}", "-t", f"{seg['dur']:.2f}", "-i", seg["path"]])

        n = len(valid_segs)
        # Input index `n` là master_png, `n + 1 + i` là sub_pngs[i]
        cmd.extend(["-i", master_png])
        for sp in sub_pngs:
            cmd.extend(["-i", sp])

        fc_parts = []
        for i in range(n):
            fc_parts.append(f"[{i}:v]fps=60000/1001,settb=AVTB,format=yuv420p10le[v{i}]")

        # Tính toán offset chuyển cảnh xfade và khung thời gian hiển thị của từng Subtitle
        scene_windows = []
        if n == 1:
            curr_v = "[v0]"
            total_dur = valid_segs[0]["dur"]
            scene_windows.append((0.15, max(0.2, total_dur - 0.15)))
        else:
            accum_offset = 0.0
            prev_label = "[v0]"
            seg_starts = [0.0]
            trans_durs = []

            for i in range(n - 1):
                t_dur = float(valid_segs[i].get("trans_dur", 0.55))
                t_type = valid_segs[i].get(
                    "transition",
                    default_transitions[i % len(default_transitions)],
                )
                trans_durs.append(t_dur)
                offset = accum_offset + valid_segs[i]["dur"] - t_dur
                out_label = f"[vx{i+1}]"
                fc_parts.append(
                    f"{prev_label}[v{i+1}]xfade=transition={t_type}:duration={t_dur:.2f}:offset={offset:.2f}{out_label}"
                )
                prev_label = out_label
                accum_offset = offset
                seg_starts.append(offset)

            curr_v = prev_label
            total_dur = accum_offset + valid_segs[-1]["dur"]

            for i in range(n):
                st = seg_starts[i] + (0.20 if i == 0 else trans_durs[i - 1] + 0.12)
                if i < n - 1:
                    en = seg_starts[i + 1] - 0.08
                else:
                    en = total_dur - 0.20
                if en <= st:
                    en = st + 0.5
                scene_windows.append((st, en))

        # Overlay Master Header + Logo cố định xuyên suốt toàn bộ video
        fc_parts.append(f"{curr_v}[{n}:v]overlay=0:0:format=yuv420p10[vhdr]")
        last_ov = "[vhdr]"

        # Overlay từng Subtitle theo đúng khung thời gian của từng cảnh
        for i in range(n):
            st, en = scene_windows[i]
            sub_idx = n + 1 + i
            next_ov = f"[vsub{i}]" if i < n - 1 else "[vpre]"
            fc_parts.append(
                f"{last_ov}[{sub_idx}:v]overlay=0:0:format=yuv420p10:enable='between(t,{st:.2f},{en:.2f})'{next_ov}"
            )
            last_ov = next_ov

        fc_parts.append(f"{last_ov}format=p010le[vout]")
        filter_complex = ";".join(fc_parts)

        merged_no_audio = os.path.join(work_dir, "merged.mp4")
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-an",
            "-c:v", "hevc_videotoolbox",
            "-profile:v", "main10",
            "-pix_fmt", "p010le",
            "-b:v", "75M",
            "-color_primaries", "bt2020",
            "-color_trc", "arib-std-b67",
            "-colorspace", "bt2020nc",
            "-tag:v", "hvc1",
            merged_no_audio,
        ])
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if bgm_path and os.path.exists(bgm_path):
            fade_out_st = max(0.5, total_dur - 1.8)
            subprocess.run(
                [
                    FFMPEG, "-y",
                    "-display_rotation:v:0", "0",
                    "-i", merged_no_audio,
                    "-stream_loop", "-1", "-i", bgm_path,
                    "-t", f"{total_dur:.2f}",
                    "-filter_complex", f"[1:a]afade=t=in:st=0:d=1.0,afade=t=out:st={fade_out_st:.2f}:d=1.8,volume=0.90[aout]",
                    "-map", "0:v:0",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-tag:v", "hvc1",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    out_mp4,
                ],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            shutil.move(merged_no_audio, out_mp4)

        print(f"✅ Xuất 4K HDR 10-bit (kèm xfade mượt) thành công: {out_mp4} ({width}x{height}, {total_dur:.1f}s, {os.path.getsize(out_mp4)/1024/1024:.1f} MB)")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def run_opera_3pn_suite(src_dir: str, out_dir: str):
    """
    Bộ 2 Video 4K 10-bit HDR (2160x3840, 59.94 fps) cho căn:
    THE OPERA RESIDENCE — 3 PHÒNG NGỦ | VIEW CẦU BA SON & TRUNG TÂM THÀNH PHỐ
    - Tách biệt hoàn toàn Font, Màu sắc (đồng nhất) và Viền chữ giữa Tiêu đề (Header) và Phụ đề (Subtitle).
    - Chuyển cảnh xfade mượt mà tùy biến theo từng tình huống chuyển phòng.
    """
    os.makedirs(out_dir, exist_ok=True)

    # =========================================================================
    # VIDEO 1 (DỌC 9:16 4K UHD - 2160x3840):
    # - Tiêu đề (Header): Đồng bộ 1 màu Vàng Champagne Hoàng Gia (Cormorant Garamond Bold + Montserrat)
    # - Phụ đề (Subtitle): Font Plus Jakarta Sans thanh lịch, viền mảnh, đổi màu qua từng cảnh
    # - Chuyển cảnh (Transitions): zoomin (Ban công -> Phòng khách) -> smoothright -> fade -> circleopen
    # =========================================================================
    v1_segments = [
        {
            "file": "IMG_7409.MOV",
            "start": 2.80,
            "dur": 5.90,
            "palette_idx": 0,
            "transition": "zoomin",       # Hút nhẹ từ ngoài ban công vào không gian phòng khách
            "trans_dur": 0.55,
            "subtitle": "Tầm nhìn triệu đô hướng trọn cầu Ba Son",
        },
        {
            "file": "IMG_7413.MOV",
            "start": 0.15,
            "dur": 2.75,
            "palette_idx": 1,
            "transition": "smoothright",  # Lướt mượt theo chiều lia máy vào phòng ngủ Master
            "trans_dur": 0.50,
            "subtitle": "Phòng khách sofa da & bàn đá Marble",
        },
        {
            "file": "IMG_7410.MOV",
            "start": 0.35,
            "dur": 4.70,
            "palette_idx": 2,
            "transition": "fade",         # Hòa cảnh êm ái sang không gian tủ áo kính LED
            "trans_dur": 0.55,
            "subtitle": "Phòng ngủ Master ôm trọn ánh đèn đô thị",
        },
        {
            "file": "IMG_7417.MOV",
            "start": 3.30,
            "dur": 5.20,
            "palette_idx": 3,
            "transition": "circleopen",   # Mở bừng không gian sang phòng tắm đá Marble trắng
            "trans_dur": 0.55,
            "subtitle": "Hệ tủ kính đen tích hợp đèn LED tinh tế",
        },
        {
            "file": "IMG_7411.MOV",
            "start": 2.25,
            "dur": 5.50,
            "palette_idx": 4,
            "subtitle": "Phòng tắm Master chuẩn resort 5 sao",
        },
    ]
    build_edited_video(
        src_dir=src_dir,
        out_mp4=os.path.join(out_dir, "01_9x16_POV_Trai_Nghiem_Dem_The_Opera_3PN.mp4"),
        width=2160,
        height=3840,
        theme_name="imperial_gold_header",
        line1="THE OPERA RESIDENCE",
        line2="3 PHÒNG NGỦ  |  VIEW CẦU BA SON & TRUNG TÂM THÀNH PHỐ",
        watermark="chiHome",
        bgm_path=os.path.join(BGM_DIR, "bgm_style1_chill_night.m4a"),
        segments=v1_segments,
    )

    # =========================================================================
    # VIDEO 2 (DỌC 9:16 4K UHD - 2160x3840):
    # - Tiêu đề (Header): Đồng bộ 1 màu Trắng Kim Cương (Cormorant Garamond Bold + Montserrat)
    # - Phụ đề (Subtitle): Font Playfair Display Italic (chữ nghiêng điện ảnh), viền Nâu Espresso mảnh,
    #                      đổi màu Vàng Champagne / Ngọc Lục Bảo / Hổ Phách / Xanh Pha Lê theo từng cảnh
    # - Chuyển cảnh (Transitions): smoothleft -> hblur -> smoothright -> fade -> smoothup -> dissolve
    # =========================================================================
    v2_segments = [
        {
            "file": "IMG_7409.MOV",
            "start": 4.20,
            "dur": 4.60,
            "palette_idx": 0,
            "transition": "smoothleft",   # Lia mượt từ cầu Ba Son vào phòng khách
            "trans_dur": 0.50,
            "subtitle": "Trực diện cầu Ba Son & trung tâm Quận 1",
        },
        {
            "file": "IMG_7413.MOV",
            "start": 0.15,
            "dur": 2.65,
            "palette_idx": 1,
            "transition": "hblur",        # Lướt nhanh hiện đại từ Sofa sang góc Smart TV
            "trans_dur": 0.45,
            "subtitle": "Không gian phòng khách sang trọng, ấm cúng",
        },
        {
            "file": "IMG_7413.MOV",
            "start": 5.05,
            "dur": 2.25,
            "palette_idx": 2,
            "transition": "smoothright",  # Chuyển mượt vào phòng ngủ Master
            "trans_dur": 0.50,
            "subtitle": "Góc giải trí hiện đại, tiện nghi",
        },
        {
            "file": "IMG_7410.MOV",
            "start": 0.50,
            "dur": 4.30,
            "palette_idx": 3,
            "transition": "fade",         # Chuyển êm sang phòng ngủ thứ 2
            "trans_dur": 0.50,
            "subtitle": "Phòng ngủ Master hệ kính kịch trần",
        },
        {
            "file": "IMG_7416.MOV",
            "start": 3.20,
            "dur": 3.25,
            "palette_idx": 4,
            "transition": "smoothup",     # Chuyển mượt sang phòng ngủ thứ 3
            "trans_dur": 0.50,
            "subtitle": "Phòng ngủ thứ hai ngắm trọn thành phố về đêm",
        },
        {
            "file": "IMG_7418.MOV",
            "start": 2.40,
            "dur": 3.40,
            "palette_idx": 5,
            "transition": "dissolve",     # Hòa cảnh sang phòng tắm đá Marble
            "trans_dur": 0.55,
            "subtitle": "Phòng ngủ thứ ba riêng tư, thanh lịch",
        },
        {
            "file": "IMG_7411.MOV",
            "start": 5.20,
            "dur": 5.40,
            "palette_idx": 6,
            "subtitle": "Phòng tắm đá Marble chuẩn khách sạn 5 sao",
        },
    ]
    build_edited_video(
        src_dir=src_dir,
        out_mp4=os.path.join(out_dir, "02_9x16_Spec_Luxury_The_Opera_3PN.mp4"),
        width=2160,
        height=3840,
        theme_name="diamond_white_header",
        line1="THE OPERA — CĂN HỘ 3PN",
        line2="THỦ THIÊM  |  VIEW TRỰC DIỆN CẦU BA SON & TRUNG TÂM",
        watermark="chiHome",
        bgm_path=os.path.join(BGM_DIR, "bgm_style3_cinematic_pov.m4a"),
        segments=v2_segments,
    )


def run_opera_4pn_suite(src_dir: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    dir1_segments = [
        {
            "file": "IMG_6874.MOV",
            "start": 0.35,
            "dur": 4.30,
            "palette_idx": 0,
            "transition": "smoothleft",
            "trans_dur": 0.50,
            "subtitle": "Tầm nhìn triệu đô bao trọn sông Sài Gòn",
        },
        {
            "file": "IMG_6872.MOV",
            "start": 0.30,
            "dur": 4.40,
            "palette_idx": 1,
            "transition": "zoomin",
            "trans_dur": 0.55,
            "subtitle": "Trực diện cầu Ba Son & tòa tháp Marina",
        },
        {
            "file": "IMG_6868.MOV",
            "start": 0.20,
            "dur": 5.70,
            "palette_idx": 2,
            "transition": "fade",
            "trans_dur": 0.55,
            "subtitle": "Phòng tắm 5 sao với bồn tắm nằm thư giãn",
        },
        {
            "file": "IMG_6864.MOV",
            "start": 0.25,
            "dur": 3.30,
            "palette_idx": 3,
            "transition": "smoothright",
            "trans_dur": 0.50,
            "subtitle": "Không gian phòng ngủ Master sang trọng",
        },
        {
            "file": "IMG_6866.MOV",
            "start": 0.20,
            "dur": 3.50,
            "palette_idx": 4,
            "subtitle": "Góc bàn trà kính vô cực bên giường ngủ",
        },
    ]
    build_edited_video(
        src_dir=src_dir,
        out_mp4=os.path.join(out_dir, "01_9x16_POV_Trai_Nghiem_Dem_The_Opera_4PN.mp4"),
        width=2160,
        height=3840,
        theme_name="imperial_gold_header",
        line1="THE OPERA RESIDENCE",
        line2="CĂN HỘ 4PN  |  VIEW CẦU BA SON, SÔNG SÀI GÒN & TRUNG TÂM",
        watermark="chiHome",
        bgm_path=os.path.join(BGM_DIR, "bgm_style1_chill_night.m4a"),
        segments=dir1_segments,
    )

    dir2_segments = [
        {
            "file": "IMG_6873.MOV",
            "start": 1.20,
            "dur": 4.40,
            "palette_idx": 0,
            "transition": "zoomin",
            "trans_dur": 0.55,
            "subtitle": "Tầm view triệu đô trực diện cầu Ba Son",
        },
        {
            "file": "IMG_6867.MOV",
            "start": 0.35,
            "dur": 6.40,
            "palette_idx": 1,
            "transition": "circleopen",
            "trans_dur": 0.55,
            "subtitle": "Phòng ngủ Master hệ kính kịch trần",
        },
        {
            "file": "IMG_6868.MOV",
            "start": 0.15,
            "dur": 2.40,
            "palette_idx": 2,
            "transition": "smoothleft",
            "trans_dur": 0.50,
            "subtitle": "Phòng tắm đá Marble chuẩn resort 5 sao",
        },
        {
            "file": "IMG_6874.MOV",
            "start": 0.80,
            "dur": 3.90,
            "palette_idx": 3,
            "subtitle": "Tầm nhìn Panorama bao trọn trung tâm Quận 1",
        },
    ]
    build_edited_video(
        src_dir=src_dir,
        out_mp4=os.path.join(out_dir, "02_9x16_Spec_Luxury_The_Opera_4PN.mp4"),
        width=2160,
        height=3840,
        theme_name="diamond_white_header",
        line1="THE OPERA — CĂN HỘ 4PN",
        line2="THỦ THIÊM  |  VIEW CẦU BA SON & TRUNG TÂM QUẬN 1",
        watermark="chiHome",
        bgm_path=os.path.join(BGM_DIR, "bgm_style3_cinematic_pov.m4a"),
        segments=dir2_segments,
    )

    # =========================================================================
    # HƯỚNG 3 (NGANG 16:9 4K UHD - 3840x2160): Widescreen Spec Tour
    # - Tiêu đề: Đồng bộ 1 màu Vàng Hoàng Gia (Cormorant Garamond Bold + Montserrat)
    # - Phụ đề: Font Plus Jakarta Sans Medium (1 dòng ngắn gọn, viền mảnh, đổi màu theo cảnh)
    # - Chuyển cảnh: smoothleft -> zoomin -> fade -> circleopen
    # =========================================================================
    dir3_segments = [
        {
            "file": "IMG_6871.MOV",
            "start": 0.40,
            "dur": 6.80,
            "palette_idx": 0,
            "transition": "smoothleft",
            "trans_dur": 0.55,
            "subtitle": "Bước ra ban công ngắm trọn sông Sài Gòn & Quận 1",
        },
        {
            "file": "IMG_6869.MOV",
            "start": 1.20,
            "dur": 5.20,
            "palette_idx": 1,
            "transition": "zoomin",
            "trans_dur": 0.55,
            "subtitle": "Trực diện cầu Ba Son & tòa tháp Marina về đêm",
        },
        {
            "file": "IMG_6857.MOV",
            "start": 0.25,
            "dur": 3.90,
            "palette_idx": 2,
            "transition": "fade",
            "trans_dur": 0.50,
            "subtitle": "Phòng ngủ Master với bàn trà kính vô cực",
        },
        {
            "file": "IMG_6859.MOV",
            "start": 0.30,
            "dur": 5.20,
            "palette_idx": 3,
            "transition": "circleopen",
            "trans_dur": 0.55,
            "subtitle": "Không gian nghỉ dưỡng 5 sao tại ChiHome",
        },
        {
            "file": "IMG_6860.MOV",
            "start": 0.20,
            "dur": 3.60,
            "palette_idx": 4,
            "subtitle": "Phòng tắm Master bồn tắm nằm & tủ gương đôi",
        },
    ]
    build_edited_video(
        src_dir=src_dir,
        out_mp4=os.path.join(out_dir, "03_16x9_Widescreen_Spec_Tour_The_Opera_4PN.mp4"),
        width=3840,
        height=2160,
        theme_name="widescreen_imperial_serif",
        line1="THE OPERA RESIDENCE",
        line2="CĂN HỘ 4PN  |  VIEW CẦU BA SON, SÔNG SÀI GÒN & TRUNG TÂM",
        watermark="chiHome",
        bgm_path=os.path.join(BGM_DIR, "bgm_style2_luxury_lounge.m4a"),
        segments=dir3_segments,
    )

    # =========================================================================
    # HƯỚNG 4 (NGANG 16:9 4K UHD - 3840x2160): Fast-Cut Hero View
    # - Tiêu đề: Đồng bộ 1 màu Trắng Kem Ngọc Trai (Montserrat Bold + Montserrat SemiBold)
    # - Phụ đề: Font Playfair Display Italic (chữ nghiêng điện ảnh, 1 dòng ngắn gọn, đổi màu theo cảnh)
    # - Chuyển cảnh: zoomin -> circleopen -> smoothright -> hblur
    # =========================================================================
    dir4_segments = [
        {
            "file": "IMG_6869.MOV",
            "start": 2.20,
            "dur": 4.50,
            "palette_idx": 0,
            "transition": "zoomin",
            "trans_dur": 0.55,
            "subtitle": "Tầm view triệu đô trực diện cầu Ba Son",
        },
        {
            "file": "IMG_6858.MOV",
            "start": 0.30,
            "dur": 4.10,
            "palette_idx": 1,
            "transition": "circleopen",
            "trans_dur": 0.55,
            "subtitle": "Phòng ngủ Master ngập tràn ánh đèn đô thị",
        },
        {
            "file": "IMG_6860.MOV",
            "start": 0.30,
            "dur": 3.40,
            "palette_idx": 2,
            "transition": "smoothright",
            "trans_dur": 0.50,
            "subtitle": "Phòng tắm chuẩn resort 5 sao giữa lòng Thủ Thiêm",
        },
        {
            "file": "IMG_6863.MOV",
            "start": 0.30,
            "dur": 4.30,
            "palette_idx": 3,
            "transition": "hblur",
            "trans_dur": 0.50,
            "subtitle": "Mọi góc phòng đều hướng trọn ra sông Sài Gòn",
        },
        {
            "file": "IMG_6870.MOV",
            "start": 0.40,
            "dur": 5.80,
            "palette_idx": 4,
            "subtitle": "Toàn cảnh trung tâm Quận 1 nhìn từ ban công",
        },
    ]
    build_edited_video(
        src_dir=src_dir,
        out_mp4=os.path.join(out_dir, "04_16x9_FastCut_HeroView_The_Opera_4PN.mp4"),
        width=3840,
        height=2160,
        theme_name="modern_fastcut_sunset",
        line1="THE OPERA — CĂN HỘ 4PN THỦ THIÊM",
        line2="VIEW TRỰC DIỆN CẦU BA SON, SÔNG SÀI GÒN & TRUNG TÂM",
        watermark="chiHome",
        bgm_path=os.path.join(BGM_DIR, "bgm_style4_upbeat_tour.m4a"),
        segments=dir4_segments,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChiHome 4K HDR Luxury Real Estate Video Editor Pipeline")
    parser.add_argument(
        "--suite",
        choices=["4pn", "3pn"],
        default="3pn",
        help="Chọn bộ kịch bản căn hộ (4pn hoặc 3pn)",
    )
    parser.add_argument(
        "--src",
        default=None,
        help="Thư mục chứa các file video thô (.MOV / .MP4)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Thư mục xuất các video 4K HDR đã edit hoàn chỉnh",
    )
    args = parser.parse_args()
    if args.suite == "3pn":
        src = args.src or "/Users/apple/Downloads/Thư mục mới với các mục 2"
        out = args.out or "/Users/apple/Downloads/Video_Da_Edit_The_Opera_3PN"
        run_opera_3pn_suite(src, out)
    else:
        src = args.src or "/Users/apple/Downloads/Thư mục mới với các mục"
        out = args.out or "/Users/apple/Downloads/Video_Da_Edit_The_Opera_4PN"
        run_opera_4pn_suite(src, out)
