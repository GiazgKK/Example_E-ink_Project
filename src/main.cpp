#include <Arduino.h>
#include <SPI.h>
#include <GxEPD2_3C.h>
#include <epd3c/GxEPD2_420c.h>
#include "image_data.h"

#define EPD_CS 5
#define EPD_DC 17
#define EPD_RST 16
#define EPD_BUSY 4
#define EPD_SCK 18
#define EPD_MOSI 23

constexpr uint16_t IMAGE_WIDTH = 400;
constexpr uint16_t IMAGE_HEIGHT = 300;
constexpr size_t IMAGE_BITMAP_SIZE = IMAGE_WIDTH * IMAGE_HEIGHT / 8;
static_assert(sizeof(image_black) == IMAGE_BITMAP_SIZE, "Invalid black bitmap size");
static_assert(sizeof(image_red) == IMAGE_BITMAP_SIZE, "Invalid red bitmap size");

GxEPD2_3C<GxEPD2_420c, GxEPD2_420c::HEIGHT>
    display(GxEPD2_420c(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

void setup()
{
    Serial.begin(115200);
    SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
    display.init(115200, true, 20, false);
    // Restore the ESP32's custom SPI routing after the driver's SPI.begin().
    SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);

    Serial.println("Rendering 400x300 e-paper image...");
    // The input was rotated clockwise before conversion so it reads upright
    // when this panel is mounted in portrait orientation.
    // The converter stores ink as 1; invert for the UC8176 panel convention.
    display.epd2.writeImage(image_black, image_red, 0, 0,
                            IMAGE_WIDTH, IMAGE_HEIGHT, true, true, true);
    display.epd2.refresh(false);
    display.epd2.hibernate();
    Serial.println("Image displayed. Panel is sleeping.");
}

void loop()
{
    delay(1000);
}
