---
title: 5.3. Reference
linkTitle: 5.3. Reference
weight: 3
description: Full API reference — FantomasNoDriver, browser, tab (native and XDO methods), Screen, Identity, and WindMouse cursor path
---

## Overview

Fantomas is a Python anti-detection browser automation library built on top of [nodriver](https://github.com/nicholasgriffin/nodriver). It provides two interaction strategies:

- **Native  methods** — browser-level events via Chrome DevTools Protocol and nodriver
- **XDO methods** — Display-server-level events via `xdotool`

Both strategies include human-like cursor movement (WindMouse physics model) and randomized keystroke delays. For a high-level overview of Fantomas' architecture and capabilities, see [Fantomas Overview]({{< relref "/docs/fantomas/overview" >}}).

## Architecture

```
FantomasNoDriver                  # Entry point, wraps nodriver
  └── launch_browser()
        → FantomasNoDriverBrowser  # Wraps nodriver Browser
              ├── get(url)
              │     → FantomasNoDriverTab  # Wraps nodriver Tab
              │           ├── Native CDP methods
              │           └── XDO methods
              ├── open_new_tab(url)
              ├── open_new_window(url)
              └── cookies (CookieJarMonkey)

Screen                             # Virtual display management (Xvfb)
Identity                           # Fake identity generation
```

Each layer delegates unknown attribute access to the underlying `nodriver` object via `__getattr__`, so all native `nodriver` methods remain available. See the [Key Concepts page](../overview/#inheritance-from-nodriver) for a full list of inherited methods and usage examples.

---

## Common Argument Types

Most Fantomas methods share a set of recurring parameter patterns. Understanding these conventions makes the entire API predictable.

### selector_list

A list of exactly **2 elements**: `[css_selector, index]`.

| Position | Type | Description |
|---|---|---|
| `0` | `str` | A standard CSS selector (e.g. `"#submit"`, `".item"`, `"input[type=email]"`) |
| `1` | `int` | Zero-based index selecting which match to target when multiple elements match the selector |

The selector is evaluated against the current DOM. If there are 5 elements matching `".item"`, passing `[".item", 2]` targets the **third** one.

```python
["#unique-button", 0]       # First (and likely only) match for an ID selector
[".card", 3]                # Fourth element with class "card"
["input[type=text]", 0]     # First text input on the page
```

### sleep_list

A list of exactly **2 elements**: `[sleep_before, sleep_after]`, both in **seconds**.

| Position | Type | Description |
|---|---|---|
| `0` | `float` | Duration to sleep **before** the action executes |
| `1` | `float` | Duration to sleep **after** the action completes |

Each value is passed through `xsleep()` internally, which applies randomized jitter (see [xsleep](#xsleepsleeping_time) for the exact behavior). This means the actual wait time is never exactly the value you pass — it is humanized.

```python
[0, 0]       # No delay before or after
[0.5, 0.5]   # ~0.15-0.6s before, ~0.15-0.6s after
[2, 1]       # ~1.5-2.5s before, ~0.5-1.5s after
```

### proportion_list

A list of exactly **2 elements**: `[x_ratio, y_ratio]`, both floats between `0.0` and `1.0`. Defaults to `[0.5, 0.5]` (center of the element).

| Position | Type | Description |
|---|---|---|
| `0` | `float` | Horizontal position within the element (`0.0` = left edge, `1.0` = right edge) |
| `1` | `float` | Vertical position within the element (`0.0` = top edge, `1.0` = bottom edge) |

The actual pixel coordinate is computed as:
- `click_x = element_x + x_ratio * element_width`
- `click_y = element_y + y_ratio * element_height`

```python
[0.5, 0.5]    # Center of the element (default)
[0.0, 0.0]    # Top-left corner
[1.0, 1.0]    # Bottom-right corner
[0.25, 0.75]  # 25% from left, 75% from top
```

This is useful for large clickable areas, sliders, or when you need to avoid clicking dead zones within an element.

### Other recurring parameters

| Parameter | Type | Description |
|---|---|---|
| `css_selector` | `str` | A plain CSS selector string (used by `xwaiter` and `xdetector` which don't need an index) |
| `timeout_delay` | `int` | Maximum wait time in seconds before giving up |
| `iframe_number` | `int` | Zero-based index of the target iframe on the page |
| `text` | `str` | The text string to type into an input element |
| `js_command` | `str` | JavaScript code to execute in the page context |
| `file_path` | `str` | Absolute filesystem path (e.g. for file uploads) |
| `targetted_attribute` | `str` | Name of an HTML attribute to read (e.g. `"href"`, `"data-id"`) |
| `value_zoom` | `float` | Page zoom factor (`1.0` = 100%, `0.5` = 50%) |

---

## FantomasNoDriver

Entry point. Configures and launches the browser.

### Constructor

```python
from fantomas import FantomasNoDriver

# With default settings
fantomas = FantomasNoDriver()

# With a config dict
fantomas = FantomasNoDriver(fantomas_params={
    "fantomas_emulate_movement": 1,
    "fantomas_show_cursor": 1,
    "fantomas_emulate_keyboard": 1,
    "fantomas_headless": False,
    "fantomas_lang": "en-US",
    "fantomas_browser_executable_path": "/bin/google-chrome",
    "fantomas_user_data_dir": "/tmp/uc_tbr34hha",
    "fantomas_browser_options": ["--no-sandbox", "--disable-gpu"]
})

# With a JSON config file path
fantomas = FantomasNoDriver(fantomas_params="/path/to/config.json")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `fantomas_emulate_movement` | `int` | `0` | Enable WindMouse cursor emulation (1/0) |
| `fantomas_show_cursor` | `int` | `0` | Show debug cursor overlay (1/0) |
| `fantomas_emulate_keyboard` | `int` | `0` | Enable human-like keystroke delays (1/0) |
| `fantomas_headless` | `bool` | `False` | Run Chrome in headless mode |
| `fantomas_lang` | `str` | `"en-US"` | Browser language |
| `fantomas_browser_executable_path` | `str` | `"/bin/google-chrome"` | Path to Chrome binary |
| `fantomas_user_data_dir` | `str` | `"/tmp/uc_tbr34hha"` | Chrome user data directory |
| `fantomas_browser_options` | `list` | `None` | Additional Chrome launch arguments |

### launch_browser()

Launches the browser and returns a `FantomasNoDriverBrowser` instance. Automatically kills any lingering Chrome processes before starting.

```python
browser = await fantomas.launch_browser()
```

---

## FantomasNoDriverBrowser

Wraps the `nodriver` Browser object with additional methods.

### get(url)

Navigates to a URL and returns a `FantomasNoDriverTab`.

```python
tab = await browser.get("https://example.com")
```

### open_new_tab(url)

Opens a URL in a new tab and returns a `FantomasNoDriverTab`.

```python
tab2 = await browser.open_new_tab("https://example.com/other")
# ... do work ...
await tab2.close()
```

### open_new_window(url)

Opens a URL in a new browser window and returns a `FantomasNoDriverTab`.

```python
tab3 = await browser.open_new_window("https://example.com/other")
# ... do work ...
await tab3.close()
```

### cookies

Cookie management with an enhanced `set_all()` method. Cookies are passed as plain dictionaries — no need to import `cdp.network.CookieParam`.

```python
# Set a single cookie
await browser.cookies.set_all([
    {"name": "session", "value": "abc123", "url": "https://example.com"}
])

# Set multiple cookies with extra options
await browser.cookies.set_all([
    {"name": "session", "value": "abc123", "domain": ".example.com", "path": "/"},
    {"name": "token", "value": "xyz789", "domain": ".example.com", "secure": True, "http_only": True}
])

# Get all cookies (inherited from nodriver)
all_cookies = await browser.cookies.get_all()
```

Available cookie fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | yes | Cookie name |
| `value` | `str` | yes | Cookie value |
| `url` | `str` | no | URL to associate the cookie with |
| `domain` | `str` | no | Cookie domain (e.g. `".example.com"`) |
| `path` | `str` | no | Cookie path (e.g. `"/"`) |
| `secure` | `bool` | no | HTTPS only |
| `http_only` | `bool` | no | Not accessible via JavaScript |
| `same_site` | `str` | no | SameSite policy (`"Strict"`, `"Lax"`, `"None"`) |
| `expires` | `float` | no | Expiration as Unix timestamp |

---

## FantomasNoDriverTab — Native Methods (based on nodriver/CDP)

These methods interact with the browser through the Chrome DevTools Protocol. The `selector_list` parameter is always `[css_selector, index]` where `index` selects which match to target (0 for the first). The `sleep_list` parameter is always `[sleep_before, sleep_after]` in seconds.

### xclick_native(selector_list, sleep_list, proportion_list)

Clicks an element. If cursor emulation is enabled, moves the cursor to the element first using a human-like path.

```python
# Click the first button matching "#submit"
await tab.xclick_native(["#submit", 0], [0.5, 0.5])

# Click with no delays
await tab.xclick_native(["#submit", 0], [0, 0])

# Click at a specific position within the element (25% from left, 75% from top)
await tab.xclick_native(["#large-area", 0], [0, 0], [0.25, 0.75])

# Click a checkbox
await tab.xclick_native(["#checkbox_test", 0], [0, 0])

# Click the second element matching ".item"
await tab.xclick_native([".item", 1], [0.2, 0.2])
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `selector_list` | `list` | required | `[css_selector, index]` |
| `sleep_list` | `list` | required | `[sleep_before, sleep_after]` in seconds |
| `proportion_list` | `list` | `[0.5, 0.5]` | Click position within the element `[x_ratio, y_ratio]` |

### xsend_native(selector_list, sleep_list, text)

Types text into an input element. Clicks the element first, then types. If `fantomas_emulate_keyboard=1`, types character by character with a random delay between **0.01s and 0.7s** per keystroke. If disabled, the entire text is sent at once via CDP.

```python
# Type into an input field
await tab.xsend_native(["#username", 0], [0.3, 0.3], "john_doe")

# Type into a password field with no delays
await tab.xsend_native(["#password", 0], [0, 0], "s3cureP@ss")

# Type into the third input matching ".field"
await tab.xsend_native([".field", 2], [0.5, 0.5], "some text")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `selector_list` | `list` | required | `[css_selector, index]` |
| `sleep_list` | `list` | required | `[sleep_before, sleep_after]` in seconds |
| `text` | `str` | `None` | Text to type |

### xmove_native(selector_list)

Moves the cursor to an element using a WindMouse human-like path via CDP mouse events. Returns the new cursor position `[x, y]`.

```python
# Move cursor to an element
new_position = await tab.xmove_native(["#target", 0])
```

### xsleep(sleeping_time)

Randomized sleep. Adds jitter of +/-0.5s around the target time. A value of `0` sleeps for exactly 0s. A value of `0.5` sleeps between 0.15s and 0.6s.

```python
await tab.xsleep(2)    # Sleeps between 1.5s and 2.5s
await tab.xsleep(0.5)  # Sleeps between 0.15s and 0.6s
await tab.xsleep(0)    # No sleep
```

### xwaiter(css_selector, timeout_delay, sleep_list)

Waits for an element matching the CSS selector to appear in the DOM, with a configurable timeout.

```python
# Wait up to 10 seconds for the element to appear
await tab.xwaiter(css_selector="#results", timeout_delay=10, sleep_list=[0, 0])

# Wait with surrounding delays
await tab.xwaiter(css_selector=".modal", timeout_delay=5, sleep_list=[1, 0.5])
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `css_selector` | `str` | required | CSS selector to wait for |
| `timeout_delay` | `int` | required | Max wait time in seconds |
| `sleep_list` | `list` | required | `[sleep_before, sleep_after]` in seconds |

### xdetector(css_selector, sleep_list)

Checks whether an element exists in the DOM. Returns `True` if found, `False` otherwise. Uses a 10-second internal timeout.

```python
# Check if a CAPTCHA is present
captcha_present = await tab.xdetector(css_selector="#captcha", sleep_list=[0, 0])
if captcha_present:
    print("CAPTCHA detected!")

# Check if a success message appeared
success = await tab.xdetector(css_selector=".success-message", sleep_list=[0.5, 0])
```

### xselect_native(selector_list, sleep_list, option_value, option_text, option_index)

Selects an option in a `<select>` dropdown. Exactly one of `option_value`, `option_text`, or `option_index` must be provided.

```python
# Select by value attribute
await tab.xselect_native(["#country", 0], [0, 0], option_value="be")

# Select by visible text
await tab.xselect_native(["#country", 0], [0, 0], option_text="Canada")

# Select by index (0-based, among <option> elements)
await tab.xselect_native(["#country", 0], [0, 0], option_index=1)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `selector_list` | `list` | required | `[css_selector, index]` |
| `sleep_list` | `list` | required | `[sleep_before, sleep_after]` in seconds |
| `option_value` | `str` | `None` | Match by `value` attribute |
| `option_text` | `str` | `None` | Match by visible text content |
| `option_index` | `int` | `None` | Match by position index |

### xinject_js(js_command)

Executes arbitrary JavaScript in the page and returns the result.

```python
# Evaluate an expression
result = await tab.xinject_js("1 + 1")
value = result[0].value  # 2

# Read a DOM property
title = await tab.xinject_js("document.title")
print(title[0].value)  # "My Page"

# Read an input value
val = await tab.xinject_js('document.querySelector("#email").value')
print(val[0].value)

# Trigger a DOM manipulation
await tab.xinject_js('document.body.style.backgroundColor = "red"')
```

### xupload_file(selector_list, file_path)

Uploads a file by setting the file path on an `<input type="file">` element via the DOM.

```python
await tab.xupload_file(['input[type="file"]', 0], "/home/user/document.pdf")

# Verify the upload
result = await tab.xinject_js('document.querySelector("input[type=file]").value')
print(result[0].value)  # "C:\fakepath\document.pdf"
```

### xtemporary_zoom(value_zoom)

Changes the page zoom level. Useful for fitting more content in the viewport or working with high-DPI pages.

```python
# Zoom out to 30%
await tab.xtemporary_zoom(0.3)

# Reset to normal
await tab.xtemporary_zoom(1)
```

### xscrape_attribute_in_iframe(iframe_number, selector_list, targetted_attribute)

Extracts an HTML attribute value from an element inside an iframe.

```python
# Get the "data-custom" attribute from the first element matching "#iframe_text" inside the first iframe
value = await tab.xscrape_attribute_in_iframe(
    iframe_number=0,
    selector_list=["#iframe_text", 0],
    targetted_attribute="data-custom"
)
print(value)  # "iframe_value"
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `iframe_number` | `int` | required | Index of the iframe (0-based) |
| `selector_list` | `list` | required | `[css_selector, index]` |
| `targetted_attribute` | `str` | required | Name of the attribute to read |

### xscrape_html_in_iframe(iframe_number, selector_list)

Extracts the outer HTML of an element inside an iframe.

```python
html = await tab.xscrape_html_in_iframe(
    iframe_number=0,
    selector_list=[".iframe_span", 0]
)
print(html)  # '<span class="iframe_span">Span in iframe</span>'
```

---

## FantomasNoDriverTab — XDO Methods

These methods use `xdotool` for OS-level mouse and keyboard interaction. Events originate from the X11 window system, making them harder for antibot systems to detect. Requires a running X11 display (real or virtual via Xvfb).

### xclick_xdo(selector_list, sleep_list, proportion_list)

Clicks an element using OS-level mouse events.

```python
await tab.xclick_xdo(["#submit-btn", 0], [0.5, 0.5])

# Click at a specific position within the element
await tab.xclick_xdo(["#large-area", 0], [0, 0], [0.25, 0.75])
```

### xsend_xdo(selector_list, sleep_list, text, proportion_list)

Types text into an element using OS-level keyboard events. Clicks the element first, then types character by character with random delays.

```python
await tab.xsend_xdo(["#search", 0], [0.3, 0.3], "search query")
```

### xmove_xdo(selector_list)

Moves the OS-level cursor to an element using a WindMouse human-like path.

```python
await tab.xmove_xdo(["#target-element", 0])
print(tab.cursor_position)  # [x, y]
```

### xclick_iframe_xdo(iframe_number, selector_list, sleep_list, proportion_list)

Clicks an element inside an iframe using OS-level mouse events.

```python
await tab.xclick_iframe_xdo(
    iframe_number=0,
    selector_list=["#iframe_btn", 0],
    sleep_list=[0, 0]
)
```

### xsend_iframe_xdo(iframe_number, selector_list, sleep_list, text, proportion_list)

Types text into an element inside an iframe using OS-level keyboard events.

```python
await tab.xsend_iframe_xdo(
    iframe_number=0,
    selector_list=["#iframe_input", 0],
    sleep_list=[0, 0],
    text="hello from xdo"
)
```

### xmove_xdo_iframe(selector_list, iframe_number)

Moves the OS-level cursor to an element inside an iframe.

```python
await tab.xmove_xdo_iframe(["#iframe_move_target", 0], iframe_number=0)
```

---

## Screen

Manages a virtual display via Xvfb (X virtual framebuffer). Required for headless environments or when running without a physical display. In a project, Screen is typically initialized in the [Agent Context]({{< relref "/docs/setting-up-project/python-files#ctx_agent_contextpy--the-agent-context" >}}).

### Constructor

```python
from fantomas import Screen

# Default: 1200x800, visible
screen = Screen()

# Custom configuration
screen = Screen(screen_params={
    "screen_visible": 0,
    "screen_height": 1920,
    "screen_width": 1080
})

# From JSON config file
screen = Screen(screen_params="/path/to/config.json")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `screen_visible` | `int` | `1` | Show virtual display window (1/0) |
| `screen_height` | `int` | `1200` | Display height in pixels |
| `screen_width` | `int` | `800` | Display width in pixels |

### launch_screen()

Starts the virtual display.

```python
screen = Screen(screen_params={"screen_visible": 0, "screen_height": 1920, "screen_width": 1080})
screen.launch_screen()
```

### screenshot_screen()

Captures a screenshot of the entire virtual display using ImageMagick. Returns a `BytesIO` object containing a PNG image.

```python
image_bytes = screen.screenshot_screen()

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(image_bytes.read())
```

### stop_screen()

Stops the virtual display.

```python
screen.stop_screen()
```

---

## Identity

Generates fake identities using the [Faker](https://faker.readthedocs.io/) library. Names are cleaned (accents removed, hyphens/apostrophes stripped).

### Constructor

```python
from fantomas import Identity

# Default: French locale, age 18-80
identity = Identity()

# Custom configuration
identity = Identity(identity_params={
    "language": "en_US",
    "min_year": 25,
    "max_year": 45,
    "min_len_password": 16,
    "max_len_password": 20,
    "enable_special_character_password": 0
})
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `language` | `str` | `"fr_FR"` | Faker locale |
| `min_year` | `int` | `18` | Minimum age |
| `max_year` | `int` | `80` | Maximum age |
| `min_len_password` | `int` | `12` | Minimum password length |
| `max_len_password` | `int` | `14` | Maximum password length |
| `enable_special_character_password` | `int` | `1` | Strip special characters from password (1/0) |

### launch_identity_creation()

Generates and returns a fake identity dictionary.

```python
identity = Identity(identity_params={"language": "en_US", "min_year": 25, "max_year": 40})
data = identity.launch_identity_creation()

print(data)
# {
#     "first_name": "John",
#     "name": "Smith",
#     "alias": "johnsmith10001",
#     "birth_day": 15,
#     "birth_month": 3,
#     "birth_year": 1988,
#     "password": "xK7mRt2pLqNw"
# }
```

---

## Mouse Position

Fantomas tracks the cursor position across actions. Each tab maintains a `cursor_position` attribute (`[x, y]`) that **persists between calls** — every move or click updates it, and the next action starts its movement from wherever the cursor was left.

### How it works

1. **Initial position**: When a tab is created, the cursor starts at `[0, 0]` (top-left corner of the viewport).

2. **Every movement-based action updates the position**: After `xclick_native`, `xmove_native`, `xclick_xdo`, `xmove_xdo`, etc., `cursor_position` is updated to the target element's coordinates.

3. **The next action starts from the previous position**: When you call `xclick_native` on element B after clicking element A, the WindMouse path is computed **from A's position to B's position** — not from `[0, 0]`.

```python
# cursor_position starts at [0, 0]

await tab.xclick_native(["#button-a", 0], [0, 0])
# cursor_position is now ~[200, 150] (wherever #button-a is)

await tab.xclick_native(["#button-b", 0], [0, 0])
# WindMouse path goes from [200, 150] → #button-b's position
# cursor_position is now ~[800, 400]

await tab.xmove_native(["#logo", 0])
# WindMouse path goes from [800, 400] → #logo's position
```


### Native vs XDO behavior

- **Native methods** (`xclick_native`, `xmove_native`, `xsend_native`): Only generate WindMouse movement paths when `fantomas_emulate_movement=1`. If disabled, the action still occurs (click/type happens) but without a realistic movement path. The cursor position is still updated regardless.

- **XDO methods** (`xclick_xdo`, `xmove_xdo`, `xsend_xdo`): Always perform OS-level cursor movement through the WindMouse path, regardless of the `fantomas_emulate_movement` setting.

For both strategies, the position state is shared — switching between native and XDO methods within the same tab continues from the last known position.

### Path generation: WindMouse algorithm

Every movement path is computed by the `VirtualCursorPath` class using a physics-based WindMouse model. It takes the tab's current `cursor_position` as the starting point and the target element's coordinates as the destination, then generates a curved, human-like trajectory constrained within the viewport.

The algorithm uses four internal physics parameters:
- **Gravity** (`G_0=5`): Attraction force toward the target — increases as the cursor gets closer
- **Wind** (`W_0=10`): Random lateral force (Wiener process noise) — creates natural-looking curves
- **Max velocity** (`M_0=15`): Speed cap preventing unrealistically fast jumps
- **Distance threshold** (`D_0=30`): Below this distance, wind force is reduced for a smooth approach to the target

All coordinates are clamped to stay within viewport bounds, preventing the cursor from "escaping" the screen.

```python
from fantomas import VirtualCursorPath

# Standalone usage (called internally by all move/click methods)
path = VirtualCursorPath().get_virtual_cursor_path(
    current_position=[0, 0],
    desired_position=[500, 300],
    viewport_width=1920,
    viewport_height=1080
)

# path[0] = list of x coordinates
# path[1] = list of y coordinates
print(f"Path has {len(path[0])} steps")
```