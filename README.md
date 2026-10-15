# Điều khiển màn hình e-ink bằng ESP32

Dự án cung cấp firmware mẫu cho ESP32 Wroom và màn hình e-ink giao tiếp SPI. Cấu hình hiện tại đã build và chạy với màn WFT0420CZ15 LW 4.2 inch (UC8176, 400 × 300, đen/trắng/đỏ). Tài liệu cũng ghi lại các điểm cần kiểm tra khi dùng những màn hình khác hiện có:

- Màn 2.9 inch E029A01
- Màn 2.13 inch kèm cáp chuyển FPC 24 pin sang 34 pin
- Màn 4.2 inch GDEH042Z96 (SSD1619)

**Không thể chọn chung driver chỉ dựa vào kích thước màn hoặc đầu nối SPI.** Hãy xác định đúng mã panel và controller theo nhãn sản phẩm hoặc datasheet trước khi đổi cấu hình firmware.

## 1. Đấu nối phần cứng

Firmware hiện tại sử dụng các chân ESP32 Wroom sau:

| Tín hiệu màn hình | GPIO ESP32 | Mô tả |
| --- | ---: | --- |
| CS | 5 | Chọn thiết bị |
| DC | 17 | Chọn dữ liệu/lệnh |
| RST | 16 | Reset |
| BUSY | 4 | Báo trạng thái bận |
| SCK / CLK | 18 | Xung SPI |
| MOSI / DIN | 23 | Dữ liệu từ ESP32 đến màn |
| GND | GND | Nối chung mass |
| MISO / DOUT | Không dùng | Firmware hiện tại chỉ ghi dữ liệu ra màn |

Khởi tạo SPI trong `src/main.cpp`:

```cpp
SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
```

Bảng trên là mapping giữa ESP32 và board adapter hiện dùng, **không phải sơ đồ chân FPC**. Khi đấu `VCC`, `GND`, `DIN`, `CLK`, `CS`, `DC`, `RST`, `BUSY`, hãy theo nhãn và sơ đồ của đúng panel/board adapter.

### An toàn nguồn và cáp FPC

- Cấp nguồn qua board điều khiển/adapter đúng theo thông số của board. Không tự đoán điện áp cấp cho panel rời.
- GPIO ESP32 dùng mức logic 3.3 V. Không nối tín hiệu logic 5 V trực tiếp vào panel; chỉ dùng adapter có chuyển mức phù hợp.
- Adapter FPC 24 pin sang 34 pin chỉ hoạt động nếu pinout, khoảng cách chân (pitch) và chiều tiếp điểm phù hợp với panel lẫn board điều khiển. Adapter **không** đổi điện áp, giao thức SPI hoặc loại controller. Kiểm tra sơ đồ chân ở cả hai đầu trước khi cắm.
- Tắt nguồn trước khi cắm/tháo FPC. Không ép đầu nối, cắm ngược cáp hoặc bẻ gập vùng hiển thị.
- Một số board điều khiển có chân bổ sung như `PWR`; chỉ đấu hoặc cấu hình theo tài liệu của đúng board đó.

## 2. Chọn panel và driver

| Panel | Thông tin cần xác nhận | Hướng dẫn chọn driver |
| --- | --- | --- |
| 2.9 inch E029A01 | Xác nhận mã panel, controller, độ phân giải và loại đơn sắc/màu. `E029A01` có thể là mã module chứ không phải mã controller. | Nếu datasheet xác nhận panel là `GDEH029A1` (128 × 296, đơn sắc, SSD1608/IL3820), GxEPD2 1.6.9 có class `GxEPD2_290` dùng với wrapper `GxEPD2_BW`. Nếu không trùng, chọn driver theo đúng biến thể đã xác nhận. |
| 2.13 inch | Xác định chính xác mã panel và controller. Các biến thể có thể khác độ phân giải (ví dụ 122 × 250 hoặc 104 × 212) và số plane màu. | Chọn class GxEPD2 và wrapper `GxEPD2_BW`/`GxEPD2_3C` theo đúng panel. Cáp chuyển 24→34 pin không xác định driver. |
| WFT0420CZ15 LW, 4.2 inch | UC8176; 400 × 300; đen/trắng/đỏ. | Firmware hiện tại dùng `GxEPD2_420c` trong GxEPD2 1.6.9 cùng wrapper `GxEPD2_3C`. Chương trình ghi hai plane bitmap đen và đỏ riêng. |
| GDEH042Z96, 4.2 inch | SSD1619; 400 × 300; dự án có driver riêng cho panel này. | Dùng `GxEPD2_420c_Z96` trong `lib/GDEH042Z96/`. Không thay bằng `GxEPD2_420c` chỉ vì cùng kích thước. Driver cục bộ không khai báo hỗ trợ partial refresh. |

Chỉ cấu hình WFT0420CZ15 LW trong `src/main.cpp` đã được build và kiểm tra với cấu hình dự án hiện tại. Các panel còn lại cần chọn driver và dữ liệu ảnh tương ứng, sau đó kiểm thử trên phần cứng thực tế.

Khi đổi panel, cần rà soát đồng thời:

1. `#include` của driver panel và class truyền vào `display(...)`.
2. Loại wrapper (`GxEPD2_BW` hoặc `GxEPD2_3C`) và các lời gọi trực tiếp driver nếu có.
3. Chiều rộng, chiều cao, số plane màu và kích thước các mảng bitmap.
4. Cực tính bit, padding theo hàng, hướng ảnh, mirror và chế độ refresh theo driver. Các cờ `invert`/`mirror_y` hiện tại được đặt cho WFT0420CZ15 LW, không mặc định đúng với panel khác.
5. Pinout adapter và các chân điều khiển bổ sung của board.

## 3. Chuẩn bị ảnh

Firmware hiện tại nạp `include/image_data.h` và cần **hai plane bitmap 400 × 300**:

- `image_black`: plane mực đen
- `image_red`: plane mực đỏ

Với cấu hình WFT hiện tại, mỗi plane dài 15.000 byte. Định dạng do converter của dự án tạo ra lưu pixel theo hàng, bit quan trọng nhất trước và bit `1` biểu thị có mực. Pixel trắng không được bật ở cả hai plane; pixel đen và đỏ không chồng lên nhau. Driver áp dụng cực tính bit và hướng ảnh khi ghi bitmap ra panel.

Converter và bộ kiểm thử hiện có trong thư mục [`tool/`](tool/). Mở PowerShell tại thư mục gốc repository, cài dependency rồi chạy converter. Mặc định header và hai PNG preview sẽ được tạo trong `include/`:

```powershell
python -m pip install -r tool\requirements-epd.txt
python tool\epd_image_converter.py "C:\duong-dan\photo.jpg" `
  --fit contain --red-mode strict
```

Có thể truyền `-o "C:\duong-dan\image_data.h"` để chọn vị trí header khác. Converter tạo thêm PNG ảnh đã chuẩn bị và PNG xem trước cạnh header đầu ra. Hãy kiểm tra các ảnh này trước khi nạp firmware. `--fit contain` giữ toàn bộ ảnh và thêm viền trắng khi cần; `--fit crop` lấp đầy màn nhưng có thể cắt mất mép; `--fit stretch` làm thay đổi tỷ lệ ảnh. Có thể xoay ảnh đầu vào trước khi chuyển bằng `--rotate cw`, `--rotate ccw` hoặc `--rotate 180`.

Một số tùy chọn hữu ích cho converter 4.2 inch hiện tại:

```powershell
# Tạo ảnh mẫu kiểm tra
python tool\epd_image_converter.py --demo

# Giữ sắc đỏ và viền khử răng cưa cho tranh/đồ họa
python tool\epd_image_converter.py "C:\duong-dan\artwork.jpg" `
  --fit contain --red-mode artwork --no-auto

# Ưu tiên chi tiết đen-trắng cho ảnh chụp
python tool\epd_image_converter.py "C:\duong-dan\photo.jpg" `
  --fit contain --red-mode off

# Tinh chỉnh độ sáng, ngưỡng đen hoặc nhận diện màu đỏ
python tool\epd_image_converter.py "C:\duong-dan\photo.jpg" `
  --brightness 1.15 --black-threshold 180 --red-min 100 --red-margin 40

# Chạy kiểm thử converter
python -m unittest discover -s tool -p "test_epd_image_converter.py"
```

Converter hiện cố định ở 400 × 300. **Không dùng trực tiếp ảnh do converter này tạo cho màn 2.9 inch hoặc 2.13 inch.** Các màn nhỏ cần converter được cấu hình theo đúng độ phân giải, số plane và cách đóng gói bitmap của driver; hãy cập nhật và kiểm thử luồng chuyển đổi trước khi sử dụng.

## 4. Build, nạp firmware và theo dõi

Cài PlatformIO và kết nối ESP32. Chạy các lệnh sau trong thư mục project; thay `COM9` bằng cổng serial thực tế của ESP32:

```powershell
pio run
pio run -t upload --upload-port COM9
pio device monitor --port COM9 --baud 115200
```

Nếu `pio` chưa có trong `PATH`, thử gọi PlatformIO được cài cho tài khoản Windows hiện tại:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run -t upload --upload-port COM9
```

Firmware mẫu vẽ ảnh khi khởi động, refresh màn hình rồi đưa panel vào chế độ ngủ. Ảnh vẫn hiển thị khi e-ink ngủ. Với luồng hiện tại, muốn đổi ảnh thì tạo lại `image_data.h`, build và nạp firmware mới; chương trình không truyền ảnh qua USB hoặc Wi-Fi.

## 5. Refresh và xử lý lỗi

- Quá trình refresh có thể làm màn nháy và mất vài giây. Không reset ESP32 hoặc ngắt nguồn khi màn đang refresh.
- Chỉ dùng partial refresh nếu đúng panel và driver có hỗ trợ. Driver GDEH042Z96 cục bộ hiện chỉ cấu hình full refresh.
- Nếu màn trắng hoặc BUSY chờ mãi, kiểm tra nguồn, mass chung, dây BUSY, chiều và pinout FPC, cùng driver đã chọn.
- Nếu ảnh nhiễu hoặc sai màu, kiểm tra mã panel, wrapper đơn sắc/màu, kích thước ảnh, thứ tự plane và cực tính bit.
- Nếu ảnh xoay hoặc lật, kiểm tra cách lắp panel, tùy chọn xoay khi chuyển ảnh và cờ hướng theo driver.
- Với lưu ý riêng về hướng hiển thị và BUSY của GDEH042Z96, xem [`lib/GDEH042Z96/README.md`](lib/GDEH042Z96/README.md).
