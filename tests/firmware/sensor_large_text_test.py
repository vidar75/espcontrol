"""Compile the production sensor driver and check the Large Text option.

Large Text moves a Home Assistant text state from the small bottom label into
the value label, hides the icon, and picks a title font from the card width.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

from generate_media_lifecycle_integration import definition

root = Path(__file__).resolve().parents[2]
headers = root / "components/espcontrol"
source = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <functional>
#include <map>
#include <string>
#include <vector>
struct lv_obj_t;
void lv_label_set_text(lv_obj_t *, const char *) {}
#include "i18n_generated.h"
#include "button_grid_config_parser.h"
#include "display_color.h"
#include "button_grid_style.h"
struct lv_font_t { int id; };
constexpr int LV_PART_MAIN = 0, LV_STATE_DEFAULT = 0, LV_STATE_CHECKED = 1;
constexpr int LV_OBJ_FLAG_HIDDEN = 1, LV_OBJ_FLAG_CLICKABLE = 2, LV_OBJ_FLAG_SCROLLABLE = 4;
constexpr int LV_ALIGN_TOP_LEFT = 0, LV_ALIGN_CENTER = 1;
constexpr int LV_TEXT_ALIGN_AUTO = 0, LV_TEXT_ALIGN_CENTER = 1;
constexpr int LV_LABEL_LONG_WRAP = 0, LV_LABEL_LONG_DOT = 1;
using lv_style_selector_t = int;
struct lv_obj_t {
  int flags = LV_OBJ_FLAG_SCROLLABLE;
  int align = LV_ALIGN_TOP_LEFT;
  int text_align = LV_TEXT_ALIGN_AUTO;
  int long_mode = LV_LABEL_LONG_WRAP;
  int width = 0;
  bool wrapped = false;
  const lv_font_t *font = nullptr;
  std::string content;
};
struct BtnSlot {
  lv_obj_t *btn = nullptr, *icon_lbl = nullptr, *sensor_container = nullptr;
  lv_obj_t *sensor_lbl = nullptr, *unit_lbl = nullptr, *text_lbl = nullptr;
  ParsedCfg *config = nullptr;
};
struct DisplayProfile {
  struct {
    const lv_font_t *sensor = nullptr, *media_title = nullptr, *media_control_title = nullptr;
  } fonts;
  struct { const lv_font_t *font = nullptr; int unit_offset_percent = -10; } large_numbers;
};
uint32_t lv_color_hex(uint32_t rgb) { return rgb; }
int lv_pct(int value) { return 1000 + value; }
void lv_obj_set_style_bg_color(lv_obj_t *, uint32_t, int) {}
void lv_obj_add_flag(lv_obj_t *obj, int flag) { obj->flags |= flag; }
void lv_obj_clear_flag(lv_obj_t *obj, int flag) { obj->flags &= ~flag; }
void lv_obj_set_width(lv_obj_t *obj, int width) { obj->width = width; }
void lv_label_set_long_mode(lv_obj_t *obj, int mode) { obj->long_mode = mode; }
void lv_obj_set_style_text_font(lv_obj_t *obj, const lv_font_t *font, int) { obj->font = font; }
void lv_obj_set_style_translate_y(lv_obj_t *, int, int) {}
void lv_obj_align(lv_obj_t *obj, int align, int, int) { obj->align = align; }
void lv_obj_set_style_text_align(lv_obj_t *obj, int align, int) { obj->text_align = align; }
void lv_label_set_display_text(lv_obj_t *label, const char *text) {
  label->content = text;
  label->wrapped = false;
}
void set_wrapped_button_label_text(lv_obj_t *label, const std::string &text) {
  label->content = text;
  label->wrapped = true;
}
void setup_toggle_visual(BtnSlot &, const ParsedCfg &) {}
const char *find_icon(const char *name) { return name; }
void set_card_disabled_state(lv_obj_t *, bool) {}
uint32_t current_grid_sensor_surface_color() { return 0; }
uint32_t current_grid_sensor_color() { return 0; }
void apply_sensor_active_color(lv_obj_t *, bool, esphome::StringRef, uint32_t,
                               uint32_t, bool, bool, bool) {}
bool large_number_square_card_layout(int, int) { return false; }
bool card_large_numbers_active_for_layout(const ParsedCfg &, int, int) { return false; }
void apply_large_sensor_number_style(const BtnSlot &, const lv_font_t *, int) {}
std::map<std::string, std::function<void(esphome::StringRef)>> subscriptions;
void ha_subscribe_state(const std::string &entity, std::function<void(esphome::StringRef)> callback) {
  subscriptions[entity] = callback;
}
void subscribe_friendly_name(lv_obj_t *, const std::string &) {}
void subscribe_sensor_icon_state(lv_obj_t *, lv_obj_t *, const ParsedCfg &, bool) {}
struct TimeSensorCtx { lv_obj_t *sensor_lbl = nullptr, *unit_lbl = nullptr; };
template <typename T> T *grid_delete_with_owner(lv_obj_t *, T *ptr) { return ptr; }
template <typename T> T *grid_track_runtime_allocation(lv_obj_t *, T *ptr) { return ptr; }
void subscribe_time_sensor_value(TimeSensorCtx *, const std::string &, const std::string &, int) {}
void subscribe_sensor_value(lv_obj_t *, const std::string &, int, lv_obj_t *, const std::string &,
                            lv_obj_t *, bool, uint32_t, bool, uint32_t) {}
namespace espcontrol::cards {
void sensor_driver_register_local_value(BtnSlot &, const ParsedCfg &) {}
}
'''

groups = (
    ("button_grid_display.h", "", (
        "display_sensor_font", "display_large_sensor_font",
        "display_large_sensor_unit_offset_percent", "display_media_title_font",
        "display_media_control_title_font",
    )),
    ("button_grid_subscriptions.h", "", ("subscribe_sensor_text_card_value",)),
    ("button_grid_sensor_driver.h", "espcontrol::cards", (
        "sensor_driver_matches", "sensor_driver_is_local", "sensor_driver_is_text",
        "sensor_driver_apply_background", "sensor_driver_setup_visual",
        "sensor_driver_refresh_layout", "sensor_driver_bind_data",
    )),
)
for filename, namespace, names in groups:
    text = (headers / filename).read_text()
    if namespace:
        source += "\nnamespace " + namespace + " {\n"
    for name in names:
        line, code = definition(text, name)
        source += f'\n#line {line} "{filename}"\n{code}\n'
    if namespace:
        source += "\n}\n"

source += r'''
#line 1 "sensor_large_text_cases"
struct Card {
  lv_obj_t btn, icon, container, value, unit, label;
  BtnSlot slot{&btn, &icon, &container, &value, &unit, &label, nullptr};
};

espcontrol::cards::Context sensor_context() {
  espcontrol::cards::Context context;
  context.runtime.driver = espcontrol::card_runtime::CardDriverId::SENSOR;
  context.runtime.type = espcontrol::card_runtime::CardTypeId::SENSOR;
  return context;
}

ParsedCfg text_sensor(const std::string &options) {
  ParsedCfg config;
  config.type = "sensor";
  config.sensor = "sensor.ukedag";
  config.precision = "text";
  config.options = options;
  return config;
}

void feed(const char *state) {
  subscriptions.at("sensor.ukedag")(esphome::StringRef(state, std::strlen(state)));
}

int main() {
  const lv_font_t sensor_font{1}, title_font{2}, control_title_font{3};
  DisplayProfile display;
  display.fonts.sensor = &sensor_font;
  display.fonts.media_title = &title_font;
  display.fonts.media_control_title = &control_title_font;
  const CardPalette palette{};
  const auto context = sensor_context();

  {
    // Default text sensor: icon stays, the state goes in the bottom label.
    Card card;
    const ParsedCfg config = text_sensor("");
    assert(!sensor_large_text_enabled(config));
    assert(espcontrol::cards::sensor_driver_setup_visual(card.slot, config, context, palette));
    assert(!(card.icon.flags & LV_OBJ_FLAG_HIDDEN));
    assert(card.container.flags & LV_OBJ_FLAG_HIDDEN);
    assert(card.container.align == LV_ALIGN_TOP_LEFT);
    assert(espcontrol::cards::sensor_driver_bind_data(card.slot, config, context, palette, 2));
    feed("onsdag");
    assert(card.label.content == "Onsdag" && card.label.wrapped);
    assert(card.value.content.empty());
  }
  {
    // Large Text on a Wide card: icon hidden, state in the value label with
    // the large title font, bottom label left empty.
    Card card;
    card.container.flags = LV_OBJ_FLAG_HIDDEN | LV_OBJ_FLAG_SCROLLABLE;
    const ParsedCfg config = text_sensor("large_text");
    assert(sensor_large_text_enabled(config));
    assert(espcontrol::cards::sensor_driver_setup_visual(card.slot, config, context, palette));
    assert(card.icon.flags & LV_OBJ_FLAG_HIDDEN);
    assert(!(card.container.flags & LV_OBJ_FLAG_HIDDEN));
    assert(card.value.long_mode == LV_LABEL_LONG_DOT);
    assert(card.value.content == "--" && card.unit.content.empty() && card.label.content.empty());
    // Centred, and no scrollbar: unit hidden, container not scrollable.
    assert(card.container.align == LV_ALIGN_CENTER);
    assert(card.value.text_align == LV_TEXT_ALIGN_CENTER);
    assert(card.unit.flags & LV_OBJ_FLAG_HIDDEN);
    assert(card.label.flags & LV_OBJ_FLAG_HIDDEN);
    assert(!(card.container.flags & LV_OBJ_FLAG_SCROLLABLE));
    assert(espcontrol::cards::sensor_driver_refresh_layout(card.slot, config, context, display, 1, 2));
    assert(card.value.font == &control_title_font);
    assert(card.container.align == LV_ALIGN_CENTER);
    assert(espcontrol::cards::sensor_driver_bind_data(card.slot, config, context, palette, 2));
    feed("onsdag");
    assert(card.value.content == "Onsdag" && !card.value.wrapped);
    assert(card.label.content.empty());
  }
  {
    // A Single card keeps the smaller title font.
    Card card;
    const ParsedCfg config = text_sensor("large_text");
    espcontrol::cards::sensor_driver_setup_visual(card.slot, config, context, palette);
    espcontrol::cards::sensor_driver_refresh_layout(card.slot, config, context, display, 1, 1);
    assert(card.value.font == &title_font);
  }
  {
    // The flag means nothing outside Text mode or for local sensors.
    ParsedCfg numeric = text_sensor("large_text");
    numeric.precision = "";
    assert(!sensor_large_text_enabled(numeric));
    ParsedCfg local = text_sensor("large_text");
    local.sensor = "local";
    assert(!sensor_large_text_enabled(local));
    assert(sensor_card_options_normalized("large_text,active_color", "text") == "active_color,large_text");
    assert(sensor_card_options_normalized("large_text", "").empty());
  }
}
'''

with tempfile.TemporaryDirectory(prefix="sensor-large-text-") as directory:
    cpp = Path(directory) / "test.cpp"
    binary = Path(directory) / "test"
    cpp.write_text(source)
    subprocess.run([sys.argv[1] if len(sys.argv) > 1 else "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-I" + str(root / "tests/firmware/stubs"), "-I" + str(headers), str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("Sensor Large Text checks passed: centred value label, no scrollbar, font by card width, text-mode only.")
