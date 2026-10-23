---
name: chihome-luxury-video-editor
description: >-
  Quy trình dựng và xuất video bất động sản cao cấp chuẩn 4K 10-bit HDR (60fps) độc quyền cho thương hiệu ChiHome (chihome.vn) tại The Opera, The Galleria, The Crest (The Metropole Thủ Thiêm), theo phong cách TikTok @thaitairealtor và @ban_va_cho_thue_can_ho. Kích hoạt skill này mỗi khi người dùng gửi thư mục clip thô (.MOV/.MP4) hoặc yêu cầu edit video căn hộ.
---

# ChiHome Luxury Video Editor (`chihome-luxury-video-editor`)

Skill này đóng gói toàn bộ quy trình chuẩn để kiểm tra clip thô, cắt bỏ đoạn thừa/phản chiếu, chèn chữ tiếng Việt phân tách rõ **Tiêu đề cố định (Header)** và **Phụ đề 1 dòng chạy theo cảnh (Subtitle)**, áp dụng **chuyển cảnh mượt mà theo tình huống (`Contextual xfade`)**, gắn logo thương hiệu **ChiHome (`chihome.vn`)** và xuất video **4K 10-bit HDR (`HEVC Main 10`, `59.94 fps`, `~75–80 Mbps`)** giữ nguyên 100% chất lượng gốc từ iPhone.

---

## 1. Quy trình 5 Bước Bắt Buộc Khi Nhận Thư Mục Clip Thô Mới

### Bước 1: Quét Metadata & Đồng bộ Tuyệt đối Tỷ lệ Khung hình (Aspect Ratio Separation)
- Kiểm tra toàn bộ file `.MOV` / `.MP4` trong thư mục nguồn bằng `ffmpeg -i` để đọc kích thước gốc và `displaymatrix: rotation`:
  - **Nhóm Dọc (`9:16`)**: Độ phân giải gốc `2160x3840` (`rotation = -90/90` hoặc `width < height`).
  - **Nhóm Ngang (`16:9`)**: Độ phân giải gốc `3840x2160` (`rotation = 0` và `width > height`).
- **QUY TẮC SỐ 1**: Tuyệt đối không ghép chung clip `9:16` và `16:9` trong cùng 1 video.

### Bước 2: Kiểm tra Hình ảnh Từng Giây & Cắt Bỏ Triệt Để Khúc Thừa (Visual Timeline Inspection)
- Trích xuất dải ảnh縮 (contact sheet) theo từng giây (`1s` hoặc `0.6s`) của các clip thô và dùng `read_file` để quan sát trực tiếp trước khi dựng:
  1. **Loại bỏ hoàn toàn** các clip bấm nhầm/quá ngắn (`< 2.0s`), clip tắt đèn tối, hoặc các take bị trùng góc nhưng vướng đồ đạc/vali trên sàn.
  2. **Cắt bỏ chính xác đến phần mười giây (`start`, `dur`)** các đoạn thừa trong clip:
     - Cắt bỏ các giây đầu/cuối có **bàn tay bật công tắc đèn**, **vách tường trắng**, **hộc tủ**, hoặc **khung cửa kính** trước khi bước ra ban công.
     - Nếu trong 1 clip lia máy có khoảnh khắc lướt qua cửa kính/gương bị dính **bóng phản chiếu người cầm điện thoại quay**, bắt buộc tách clip đó thành 2 phân đoạn sạch (trước và sau đoạn phản chiếu) để 100% khung hình chỉ có không gian căn hộ.

### Bước 3: Chuẩn Vùng An Toàn TikTok (TikTok iOS Safe Zone) & Phân Biệt TIÊU ĐỀ vs. PHỤ ĐỀ
1. **Tọa độ Vùng An Toàn Thực Tế Trên Màn Hình iPhone TikTok (`9:16` Vertical)**:
   - Khi phát video `9:16` trên màn hình iPhone `19.5:9`, TikTok tự động phóng nhẹ chiều dọc và **cắt bớt `~5.5%` mỗi bên mép trái/phải** (`11%` tổng chiều ngang), đồng thời thanh điều hướng trên cùng (`LIVE | Cộng đồng | Bạn bè | Đã follow | Đề xuất`) chiếm từ `0% – 11.5%` chiều cao, và phần thông tin dưới đáy (`📍 Vị trí`, tên kênh, caption, nút Chia sẻ) chiếm từ `70.5% – 92%` chiều cao.
   - Do đó, trên khung dọc `9:16` (`2160x3840`), bắt buộc áp dụng tọa độ Safe Zone:
     - **Giới hạn chiều ngang tự động (`Auto-Fit Safe Width = 72% * width`)**: Mọi dòng chữ Tiêu đề và Phụ đề tự động thu gọn cỡ chữ và khoảng cách ký tự nếu vượt quá `72%` chiều rộng video để không bao giờ bị mất chữ ở 2 mép trái/phải.
     - **Vị trí Tiêu đề (`top_y = 13.2% * height`)**: Nằm hoàn toàn bên dưới thanh `Bạn bè | Đã follow | Đề xuất` của TikTok.
     - **Vị trí Phụ đề (`base_sub_y = 62.0% * height`) & Logo ChiHome (`ly = 66.2% * height`)**: Nằm hoàn toàn phía trên thẻ vị trí `📍 The Metropole Thủ thiêm` và phần mô tả bài đăng của TikTok.
2. **TIÊU ĐỀ CỐ ĐỊNH CỦA KÊNH (Channel Signature Header — Thông tin dự án, số PN, View)**:
   - **Đồng bộ 1 màu sang trọng duy nhất** trên toàn khối Tiêu đề của 1 video (ví dụ: *Imperial Champagne Gold `#FFE294`* hoặc *Diamond Pearl White `#FFFFFF`*).
   - **Font chữ Tiêu đề Tối Giản, Hiện Đại, Dễ Đọc Tức Thì (`Lining Numerals 100%`)**:
     - Dùng **Montserrat Bold/SemiBold** (`Montserrat-Variable.ttf` weight `750`/`600`) hoặc **Manrope ExtraBold/SemiBold** (`Manrope-Variable.ttf` weight `800`/`600`), ở giữa có **đường kẻ chỉ Kim Cương (`Luxury Ornamental Hairline`)** đồng màu.
     - **TUYỆT ĐỐI KHÔNG** dùng các font Serif cổ điển có chữ số kiểu cũ (*Old-Style Numerals* như Cormorant Garamond, Playfair Display) khiến các chữ số `3PN`, `4PN` bị nhảy thụt thò lệch hàng. Mọi chữ cái và chữ số trong `3PN`, `4PN` phải thẳng hàng 100% trên cùng đường chân chữ (*baseline*) và đường đỉnh chữ (*cap-height*).
   - **Viền chữ & Đổ bóng Tiêu đề**: Dùng viền Đen Obsidian sắc nét (`~4.0px` ở 4K) + Hào quang bóng đổ sâu 2 tầng + Lớp Sương Mờ Thượng Lưu nhẹ ở đỉnh khung hình (`Top Soft Vignette`).
   - **Vị trí cố định**: Khối Tiêu đề và Logo ChiHome đứng yên 100% xuyên suốt toàn bộ video.
3. **PHỤ ĐỀ MIÊU TẢ CHẠY THEO CẢNH (Dynamic Scene Subtitle)**:
   - **Ngắn gọn, đắt giá, tinh tế (1 dòng duy nhất, 6–8 chữ)**: Ví dụ *"Tầm nhìn triệu đô hướng trọn cầu Ba Son"*, *"Phòng khách sofa da & bàn đá Marble"*, *"Phòng ngủ Master hệ kính kịch trần"*.
   - **Font chữ Phụ đề KHÁC HẲN Tiêu đề (Tối giản, không uốn lượn rối mắt, cực kỳ dễ đọc)**: Dùng **Be Vietnam Pro Medium** (`BeVietnamPro-Medium.ttf`) hoặc **Plus Jakarta Sans SemiBold** (`PlusJakartaSans-Variable.ttf` weight `600`). Không dùng font chữ nghiêng uốn lượn cầu kỳ gây khó đọc khi lướt nhanh trên điện thoại.
   - **Màu sắc Phụ đề KHÁC HẲN Tiêu đề và biến thiên theo từng cảnh**: Mỗi câu phụ đề đồng nhất 1 màu sang trọng và tự động đổi màu qua từng phân cảnh.
   - **Viền chữ Phụ đề KHÁC HẲN Tiêu đề**: Dùng viền Nâu Espresso / Xám Khói mảnh (`~2.0px` ở 4K) kèm bóng đổ sương mờ mềm mại, **TUYỆT ĐỐI KHÔNG** dùng khung hộp nền.

### Bước 4: Chuyển Cảnh Mượt Mà Theo Tình Huống (`Contextual xfade Transitions`)
- Không cắt ngang thô cứng (`hard cut`); sử dụng hàm `build_edited_video(...)` trong [edit_pipeline.py](/Users/apple/.gemini/antigravity/scratch/luxury-video-editor/edit_pipeline.py) để áp dụng bộ chuyển cảnh `xfade` tùy theo hướng lia máy và mạch không gian giữa 2 phòng:
  - `zoomin` (`0.55s`): Từ ngoài Ban công hút nhẹ vào không gian Phòng khách.
  - `smoothleft` / `smoothright` / `hblur` (`0.45s–0.50s`): Khi 2 cảnh nối tiếp nhau có cùng hướng lia máy ngang (`Pan-to-Pan Match Cut`).
  - `fade` / `dissolve` / `smoothup` (`0.50s–0.55s`): Khi chuyển êm ái giữa các Phòng ngủ hoặc không gian nội thất.
  - `circleopen` (`0.55s`): Khi mở từ phòng ngủ ấm áp sang không gian Phòng tắm đá Marble trắng sáng.
- Phụ đề của cảnh cũ tự động tắt trước điểm giao thoa chuyển cảnh và phụ đề của cảnh mới xuất hiện ngay khi vào cảnh mới.

### Bước 5: Thương hiệu ChiHome (`chihome.vn`) & Kiểm chứng Chất lượng 4K 10-bit HDR
- Luôn gắn logo chính thức `chiHome — your dream - your home` ([chihome-logo-video-ready.png](/Users/apple/.gemini/antigravity/scratch/luxury-video-editor/brand/chihome-logo-video-ready.png)) cố định ở chính giữa phía dưới (`bottom-center`).
- Xuất video bằng `hevc_videotoolbox -profile:v main10 -pix_fmt p010le -b:v 75M -color_primaries bt2020 -color_trc arib-std-b67 -colorspace bt2020nc -tag:v hvc1` ở `59.94 fps`.
- Sau khi xuất xong, luôn xóa toàn bộ file tạm trong `/tmp`, kiểm tra bằng `ffmpeg -i` và trích xuất bảng ảnh preview từng cảnh để xác nhận chất lượng hiển thị bằng `read_file`.

---

## 2. Cấu Trúc Thư Mục & Lệnh Thực Thi

- **Môi trường Python**: `/Users/apple/.gemini/antigravity/scratch/agent-reach/.venv/bin/python`
- **Script dựng phim chính (hỗ trợ `xfade` + Persistent Header + Dynamic 1-Line Subtitle)**:
  - Bản chính: `/Users/apple/.gemini/antigravity/scratch/luxury-video-editor/edit_pipeline.py`
  - Bản sao lưu trong Skill: `/Users/apple/.gemini/config/skills/chihome-luxury-video-editor/scripts/edit_pipeline.py`
- **Script quét tự động thư mục mới**:
  - `/Users/apple/.gemini/antigravity/scratch/luxury-video-editor/auto_edit_folder.py`
- **Thư mục Font Luxury Tối Giản**: `/Users/apple/.gemini/antigravity/scratch/luxury-video-editor/fonts/` (`Montserrat-Variable.ttf`, `Manrope-Variable.ttf`, `BeVietnamPro-Medium.ttf`, `BeVietnamPro-SemiBold.ttf`, `BeVietnamPro-Bold.ttf`, `PlusJakartaSans-Variable.ttf`)
- **Thư mục Nhạc nền BGM**: `/Users/apple/.gemini/antigravity/scratch/luxury-video-editor/bgm/`
