---
name: chihome-luxury-video-editor
description: >-
  Quy trình dựng và xuất video bất động sản cao cấp chuẩn 4K 10-bit HDR (60fps) độc quyền cho thương hiệu ChiHome (chihome.vn) tại The Opera, The Galleria, The Crest (The Metropole Thủ Thiêm), theo phong cách TikTok @thaitairealtor và @ban_va_cho_thue_can_ho. Kích hoạt skill này mỗi khi người dùng gửi thư mục clip thô (.MOV/.MP4) hoặc yêu cầu edit video căn hộ.
---

# ChiHome Luxury Video Editor (`chihome-luxury-video-editor`)

Quy trình tự động kiểm tra clip thô, cắt bỏ đoạn thừa/bóng phản chiếu, chèn chữ tiếng Việt, lồng nhạc nền sang trọng, gắn logo thương hiệu **ChiHome (`chihome.vn`)** và xuất video **4K 10-bit HDR (`HEVC Main 10`, `59.94 fps`, `~75–80 Mbps`)** giữ nguyên 100% chất lượng gốc từ iPhone.

## Quy trình chuẩn
1. **Phân tách tuyệt đối tỷ lệ khung hình**: Nhóm dọc `9:16` (`2160x3840`) và nhóm ngang `16:9` (`3840x2160`).
2. **Kiểm tra từng giây & cắt bỏ đoạn thừa**: Loại bỏ clip `< 2.0s`, cắt bỏ giây đầu/cuối vướng tay bật công tắc đèn hoặc phản chiếu trong gương/kính.
3. **Thương hiệu ChiHome & Xuất 4K 10-bit HDR**: Gắn logo `chiHome — your dream - your home` và xuất bằng `hevc_videotoolbox -profile:v main10 -pix_fmt p010le -b:v 75M -tag:v hvc1`.
