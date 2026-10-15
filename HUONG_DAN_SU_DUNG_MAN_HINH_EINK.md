# Hướng dẫn dùng các màn hình e-ink với ESP32

Tài liệu này hướng dẫn cách đấu nối và chọn cấu hình firmware cho các màn hình e-ink hiện có trong dự án:

- 2.9 inch E029A01
- 2.13 inch, dùng mạch chuyển FPC 24 pin sang 34 pin
- 4.2 inch WFT0420CZ15 LW, controller UC8176
- 4.2 inch GDEH042Z96, controller SSD1619

Các màn hình đều có thể được điều khiển qua SPI, nhưng **không dùng chung driver chỉ vì cùng giao tiếp hoặc cùng kích thước**. Cần xác định đúng mã panel, controller, độ phân giải và loại màu trước khi chọn driver và dữ liệu ảnh.

## 1. Đấu nối ESP32

Firmware hiện tại dùng các chân sau trên ESP32 Wroom:

| Tín hiệu | GPIO ESP32 | Ghi chú |
| --- | ---: | --- |
| CS | 5 | Chip Select |
| DC | 17 | Data / Command |
| RST | 16 | Reset |
| BUSY | 4 | Trạng thái bận |
| SCK / CLK | 18 | SPI Clock |
| MOSI / DIN | 23 | SPI dữ liệu từ ESP32 sang màn |
| GND | GND | Phải nối chung mass |
| MISO / DOUT | Không dùng | Các cấu hình hiện tại chỉ ghi dữ liệu ra màn |

Trong chương trình, các chân này được khởi tạo theo dạng:

```cpp
SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
```

Chân nguồn và tên chân trên adapter có thể khác nhau. Trước khi cấp nguồn, đối chiếu nhãn `VCC`, `GND`, `DIN`, `CLK`, `CS`, `DC`, `RST`, `BUSY` trên đúng board adapter và sơ đồ của nhà sản xuất. Không đấu theo thứ tự chân cáp FPC khi chưa có sơ đồ.

### Lưu ý điện áp và cáp

- Panel e-ink thường cần board điều khiển có mạch tạo áp riêng. Cấp nguồn theo hướng dẫn của board adapter, không cấp nguồn cho tấm panel trần theo suy đoán.
- ESP32 dùng mức logic 3.3 V. Không đưa tín hiệu 5 V trực tiếp vào chân logic của panel; chỉ dùng board ghi rõ có chuyển mức tương thích.
- Với module 2.13 inch, cáp chuyển **24 pin sang 34 pin chỉ chuyển tiếp các chân theo pinout tương ứng**; nó không tự chuyển đổi giao thức, điện áp hay controller. Kiểm tra số chân, pitch, chiều tiếp điểm và pinout của cả panel lẫn adapter trước khi cắm. Không ép hoặc cắm ngược cáp.
- Tắt nguồn trước khi cắm/tháo FPC. Không chạm hoặc bẻ gập vùng hoạt động của panel.

## 2. Chọn đúng driver và dữ liệu ảnh

| Màn hình | Thông tin cần xác nhận | Cấu hình trong dự án |
| --- | --- | --- |
| 2.9 inch E029A01 | Xác nhận chính xác mã in trên panel/PCB và controller trong datasheet. Nếu mã này tương ứng `GDEH029A1` (128 × 296, đen-trắng, SSD1608/IL3820), GxEPD2 1.6.9 có class `GxEPD2_290`. Nếu không trùng, phải chọn class cho đúng biến thể. | Loại đen-trắng dùng wrapper `GxEPD2_BW`; thay class và kích thước theo panel đã xác nhận. |
| 2.13 inch | Xác nhận mã panel và controller. Ví dụ trong các biến thể được GxEPD2 hỗ trợ có loại 122 × 250 và 104 × 212; một số panel màu có hai plane dữ liệu. | Dùng đúng class 2.13 inch của biến thể đó trong GxEPD2 1.6.9. Adapter 24→34 pin không quyết định class. |
| 4.2 inch WFT0420CZ15 LW | Dự án ghi nhận UC8176, 400 × 300, đen-trắng-đỏ. | Driver hiện tại là `GxEPD2_420c` trong GxEPD2 1.6.9, wrapper `GxEPD2_3C`. |
| 4.2 inch GDEH042Z96 | SSD1619, 400 × 300, hỗ trợ dữ liệu màu theo driver riêng của dự án. | Dùng driver cục bộ `GxEPD2_420c_Z96` trong `lib/GDEH042Z96/`, không thay bằng `GxEPD2_420c` chỉ vì cùng kích thước. Driver này không quảng bá partial refresh. |

`E029A01` có thể là mã sản phẩm của module thay vì tên controller. Vì vậy, chỉ dùng gợi ý `GxEPD2_290` khi datasheet hoặc nhãn xác nhận đúng panel `GDEH029A1`; không suy luận từ tên “2.9 inch”.

Trong `src/main.cpp`, chương trình hiện chọn WFT0420CZ15 LW 4.2 inch. Khi đổi màn:

1. Thay các `#include` cho driver panel và loại wrapper (`GxEPD2_BW` hoặc `GxEPD2_3C`) nếu cần.
2. Thay class panel trong khai báo `display(...)`.
3. Cập nhật `IMAGE_WIDTH`, `IMAGE_HEIGHT` và kiểm tra kích thước mảng ảnh theo độ phân giải panel.
4. Đối chiếu cờ đảo bit, lật dọc/ngang và thứ tự plane với driver cụ thể. Giá trị `invert`/`mirror_y` hiện tại là cấu hình của ảnh WFT, không mặc định đúng cho các panel khác.
5. Giữ SPI pin mapping nếu vẫn dùng cùng GPIO và board adapter; nếu board có chân điều khiển bổ sung như `PWR`, phải cấu hình theo tài liệu board.

Không dùng `image_data.h` 400 × 300 hiện tại trực tiếp cho màn 2.9 hoặc 2.13 inch. Ảnh phải được chuyển đúng độ phân giải, hướng và định dạng của panel. Bộ chuyển ảnh đang dùng trong dự án được cấu hình cho ảnh 400 × 300; cần cấu hình hoặc cập nhật bộ chuyển đổi cho kích thước nhỏ hơn trước khi tạo header mới.

Với ảnh bitmap đóng gói theo hàng, kích thước một plane thường tính theo:

```text
bytes_per_row = ceil(width / 8)
bytes_per_plane = bytes_per_row * height
```

Một số driver hoặc công cụ có quy ước bit, padding hàng, đảo bit hoặc thứ tự plane riêng. Theo quy ước hiện tại của ảnh WFT, mỗi pixel có mực được lưu là bit 1; ảnh đỏ và ảnh đen nằm ở hai mảng riêng, vùng trắng không có bit ở cả hai mảng. Không áp dụng mặc định này cho dữ liệu từ công cụ khác.

## 3. Tạo ảnh, build và nạp firmware

Quy trình ảnh hiện tại trong dự án:

1. Dùng công cụ chuyển ảnh của dự án để tạo `include/image_data.h`.
2. Xem ảnh PNG preview do công cụ tạo ra, kiểm tra ảnh không bị cắt, xoay sai hoặc nhận nhầm màu.
3. Đảm bảo kích thước và số plane khớp với panel đã chọn; ảnh preview 400 × 300 hiện tại dành cho panel 4.2 inch.
4. Build và nạp firmware bằng PlatformIO:

```powershell
pio run
pio run -t upload --upload-port COM9
pio device monitor --port COM9 --baud 115200
```

Thay `COM9` bằng cổng COM của ESP32. Firmware mẫu hiển thị ảnh khi khởi động, sau đó đưa panel vào chế độ ngủ. Ảnh vẫn giữ trên e-ink sau khi ngủ; muốn thay ảnh theo luồng hiện tại thì tạo lại header, build và nạp firmware mới.

Khi refresh, e-ink có thể nháy và cần vài giây đến lâu hơn tùy panel. Không ngắt nguồn hoặc reset ESP32 giữa lúc panel đang refresh. Chỉ gọi partial refresh nếu driver và panel cụ thể hỗ trợ; nếu không chắc, dùng full refresh.

## 4. Kiểm tra khi không hiển thị đúng

- **Không có phản hồi / BUSY chờ quá lâu:** kiểm tra nguồn, GND chung, chân BUSY và chiều cáp; xác nhận driver đúng controller.
- **Màn trắng hoặc ảnh nhiễu:** kiểm tra thứ tự chân adapter 24→34, `CS/DC/RST`, class panel và điện áp logic.
- **Ảnh bị lật hoặc xoay:** kiểm tra hướng lắp panel, hướng ảnh đầu vào, rotation và cờ mirror trong lời gọi vẽ ảnh.
- **Đen-trắng đúng nhưng màu sai:** xác nhận panel có đúng biến thể màu hay không, loại wrapper `GxEPD2_3C`, hai plane ảnh và cực tính bit.
- **Build báo sai kích thước ảnh:** cập nhật độ rộng/cao và độ dài mảng; mỗi plane không nhất thiết có cùng số byte nếu công cụ không padding hàng theo cách driver yêu cầu.
- **GDEH042Z96 không chạy với driver chuẩn:** dùng driver cục bộ `GxEPD2_420c_Z96`; README trong `lib/GDEH042Z96/` ghi rõ các giới hạn và lưu ý về hướng hiển thị/BUSY.

Khi đổi panel, chỉ thay panel trong cấu hình sau khi đã xác nhận mã chính xác. Nếu thông tin controller hoặc pinout chưa rõ, tra datasheet/module adapter thay vì thử đổi driver hoặc đảo cáp khi đang cấp nguồn.
