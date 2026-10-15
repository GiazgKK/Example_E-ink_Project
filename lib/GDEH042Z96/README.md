# GDEH042Z96 / SSD1619 driver

Vendored from fffonion/GxEPD2 commit `4f3f531`, the panel-specific contribution
at https://github.com/ZinggJM/GxEPD2/pull/47. Original copyright notices and
GPL-3.0 license are retained. Upstream GxEPD2 1.6.9 does not include this panel.

The include path is adapted for a project-local PlatformIO library. A small BUSY
wrapper exposes timeout failures to the application instead of reporting a false
successful refresh. The upstream
panel enum is only metadata; register programming is specific to GDEH042Z96.
The SPI pins, 400 x 300 logical coordinates, and monochrome GxEPD2_BW interface
are preserved. Photo mode calls the two-plane driver directly for black/white/red output. Monochrome mode passes no red plane, clearing it.

Full refresh only; no partial-refresh capability is advertised. Validate physical
orientation and BUSY timing on the actual board before deployment. The upstream
contribution notes that some panel assemblies need `display.mirror(true)`;
this project does not silently change the existing orientation.
