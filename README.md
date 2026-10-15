# Hiển thị ảnh WFT0420CZ15 LW 4.2 inch

ESP32 Wroom, Arduino/PlatformIO, 400×300, trắng/đen/đỏ. Màn hình WFT0420CZ15 LW
dùng controller UC8176; firmware dùng driver `GxEPD2_420c` trong GxEPD2 1.6.9.
Giữ nguyên module SPI 24 pin và các chân ESP32 đã đấu như bảng dưới.

| Chân màn hình | GPIO ESP32 |
| --- | --- |
| CS | 5 |
| DC | 17 |
| RST | 16 |
| BUSY | 4 |
| CLK / SCK | 18 |
| DIN / MOSI | 23 |
| GND | GND |

Cấp nguồn theo yêu cầu của board adapter màn hình. Không dùng MISO.

## Chuyển ảnh

Mở PowerShell tại `D:\FileFromMacOS\Self_learning\Tool`:

```powershell
python -m pip install -r requirements-epd.txt
python epd_image_converter.py "D:\anh\photo.jpg"
```

Công cụ tự ghi `include/image_data.h` trong project này và
`include/image_data_preview.png` để xem trước. Header có hai mảng `PROGMEM`
`image_black` và `image_red`, mỗi mảng 15.000 byte. Một bit bằng 1 nghĩa là
có mực ở lớp tương ứng; trắng là 0 ở cả hai lớp. Bit cao nhất là pixel bên trái,
dữ liệu đi theo hàng từ trên xuống. Hai lớp không chồng mực.

Mặc định giữ tỉ lệ ảnh và thêm nền trắng (`--fit contain`). Có thể cắt ảnh cho
đầy màn hình (`--fit crop`) hoặc kéo giãn (`--fit stretch`). Đọc EXIF để xoay ảnh
đúng chiều; vùng trong suốt được ghép lên nền trắng.

Để giữ toàn bộ ảnh Wukong, luôn dùng file gốc đầy đủ với `--fit contain`.
Ảnh 1200×675 được thu xuống khoảng 400×225 và thêm nền trắng trên/dưới;
400×300 là độ phân giải cố định của màn hình. Không dùng `crop` nếu cần giữ
đủ chữ và hai mép ảnh. Ảnh nguồn đã bị cắt không thể khôi phục bằng resize.

Với ảnh có chữ đỏ trên nền trắng:

```powershell
python epd_image_converter.py "D:\anh\wukong.jpg" --fit contain --red-mode artwork --no-auto
```

`artwork` giữ đỏ sẫm và viền chữ đỏ nhạt; `strict` dùng cho ảnh chụp để hạn chế
da/cam bị nhận thành đỏ. Hai chế độ dùng sắc độ HSV gần đỏ, ngưỡng `--red-min`
mặc định 70. `--red-margin` áp dụng cho `legacy`. Màn hình chỉ có một màu mực
đỏ, không thể tái hiện mọi sắc độ đỏ của ảnh gốc.

Công cụ còn tạo `image_data_prepared.png` là ảnh đã thu vừa màn hình trước
chuyển màu. So sánh file này với `image_data_preview.png` để xác định lỗi
thu ảnh hay lỗi chọn màu. Màu PNG là RGB hiển thị trên máy tính, không phải
mô phỏng chính xác màu mực vật lý của e-ink.

```powershell
python epd_image_converter.py "D:\anh\photo.jpg" --fit crop --dither
python epd_image_converter.py "D:\anh\photo.jpg" --black-threshold 180 --red-min 100 --red-margin 40
python epd_image_converter.py --demo
python epd_image_converter.py "D:\anh\photo.jpg" -o "D:\output\image_data.h"
python -m unittest test_epd_image_converter.py
```

Mặc định bật `--auto` và `--dither`: nâng vùng tối, cân điểm trắng, tăng nét nhẹ
và giữ chi tiết bằng chấm đen/trắng. `--red-mode strict` chỉ nhận đỏ bão hòa,
hạn chế biến da/nâu thành đỏ. Với poster Wukong hoặc ảnh chân dung tối:

```powershell
python epd_image_converter.py "D:\anh\wukong.jpg" --red-mode off
python epd_image_converter.py "D:\anh\wukong.jpg" --red-mode strict --brightness 1.15
```

`--brightness` từ 0.5 đến 2.0, tăng để sáng hơn. `--red-mode off` ưu tiên chi
tiết đen/trắng; `legacy` dùng cách nhận đỏ cũ. Để dùng cách chuyển cũ:
`--no-auto --no-dither --red-mode legacy`. PNG xem trước thể hiện dữ liệu pixel,
không mô phỏng chính xác màu mực và ánh sáng trên màn hình thật.

`--dither` dùng chấm đen/trắng cho vùng xám. Khi dùng `--no-dither`, ngưỡng đen mặc định 160;
tăng ngưỡng để ảnh đen hơn. Pixel được chọn đỏ khi R >= red-min và
R - max(G, B) >= red-margin. Đây là chuyển màu theo ngưỡng, nên các màu khác
sẽ thành đen/trắng; PNG xem trước cho biết kết quả chính xác của việc chuyển đổi.
Nếu dùng `-o`, cần đặt header kết quả vào `include/image_data.h` trước khi build.

## Build và nạp

Mở terminal ở thư mục project này:

```powershell
pio run
pio run -t upload --upload-port COM9
pio device monitor --port COM9 --baud 115200
```

Thay COM9 bằng cổng ESP32 thực tế. Nếu `pio` chưa có trong PATH:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run -t upload --upload-port COM9
```

Firmware hiển thị ảnh một lần khi khởi động rồi đưa màn hình vào ngủ.
Đổi ảnh bằng cách chạy converter, build và nạp lại firmware. Đây là luồng ảnh
nhúng trong firmware, không truyền ảnh trực tiếp qua USB/Wi-Fi.
Đã kèm ảnh mẫu để build ngay. Refresh toàn màn hình mất khoảng 16 giây,
có thể nháy trong quá trình cập nhật. Ảnh vẫn lưu trên e-ink khi màn hình ngủ.

Hai lớp màu được gửi trực tiếp qua `display.epd2.writeImage(...)`.
`invert=true` khớp quy ước bit của converter, `mirror_y=true` giữ hướng ảnh
đang dùng, `pgm=true` đọc ảnh từ flash; sau đó `refresh(false)`.
