---
title: 5.2. Key Concepts
linkTitle: 5.2. Key Concepts
weight: 2
description: Fantomas architecture, nodriver inheritance, native and XDO interaction methods, human emulation, and additional modules
---

## Overview

**Technology:** Python, nodriver, xdotool
**Location:** `lib/fantomas/` (pip-installable editable package)
**Role:** Custom anti-detection browser automation framework built on top of `nodriver`adding display-server-level method 

## Architecture

```
FantomasNoDriver
  └── launch_browser() → FantomasNoDriverBrowser
                              └── get() → FantomasNoDriverTab
                                            ├── Native methods : based on nodriver/CDP(xclick_native, xsend_native, ...)
                                            └── XDO methods : display-server method(xclick_xdo, xsend_xdo, ...)
```

Each layer wraps and extends the underlying `nodriver` object via `__getattr__` delegation, adding automation-specific methods.

## Inheritance from nodriver

Fantomas objects inherit from their `nodriver` counterparts. Each Fantomas class stores the original nodriver instance internally and delegates any unknown attribute access to it via `__getattr__`. This means **all native nodriver methods and properties are directly available** on Fantomas objects — you don't need to unwrap them.

### Browser-level (FantomasNoDriverBrowser → nodriver.Browser)

```python
browser = await fantomas.launch_browser()

# These are nodriver.Browser methods, called directly on the Fantomas object:
all_tabs = browser.tabs                          # List of open tabs
main = browser.main_tab                          # The main tab
await browser.grant_all_permissions()            # Grant all browser permissions
await browser.tile_windows()                     # Tile browser windows
await browser.wait(2)                            # Wait 2 seconds
browser.stop()                                   # Stop the browser
```

### Tab-level (FantomasNoDriverTab → nodriver.Tab)

```python
tab = await browser.get("https://example.com")

# DOM querying (nodriver methods)
element = await tab.query_selector("#my-element")
elements = await tab.query_selector_all(".items")
element = await tab.find("Some visible text")
elements = await tab.find_all("repeated text")
el = await tab.wait_for(selector="#loaded-element", timeout=10)

# Navigation (nodriver methods)
await tab.back()
await tab.forward()
await tab.reload()
current_url = tab.url

# JavaScript evaluation (nodriver methods)
result = await tab.evaluate("document.title")
data = await tab.js_dumps("window.appState")

# Window control (nodriver methods)
await tab.maximize()
await tab.minimize()
await tab.fullscreen()
await tab.set_window_size(left=0, top=0, width=1920, height=1080)
await tab.activate()
await tab.bring_to_front()

# Scrolling (nodriver methods)
await tab.scroll_down(amount=25)
await tab.scroll_up(amount=25)

# Screenshots & downloads (nodriver methods)
await tab.save_screenshot("capture.jpg", format="jpeg", full_page=True)
await tab.download_file("https://example.com/file.zip")
await tab.set_download_path("/tmp/downloads")

# Page content (nodriver methods)
html = await tab.get_content()
urls = await tab.get_all_urls(absolute=True)

# Storage (nodriver methods)
storage = await tab.get_local_storage()
await tab.set_local_storage({"key": "value"})

# Tab lifecycle (nodriver methods)
await tab.close()
```

### When to use nodriver methods vs Fantomas methods

Use **Fantomas `x*` methods** (`xclick_native`, `xsend_native`, etc.) when interacting with pages that have antibot detection — they add human-like emulation (cursor movement, keystroke delays, randomized sleeps).

Use **nodriver methods directly** for utility operations that don't need emulation: DOM querying, navigation, screenshots, JavaScript evaluation, window management, etc.

```python
# Combine both: use nodriver for queries, Fantomas for interactions
element = await tab.query_selector("#submit")       # nodriver: find the element
await tab.xclick_native(["#submit", 0], [0.5, 0.5]) # fantomas: click with emulation

html = await tab.get_content()                       # nodriver: get page HTML
await tab.save_screenshot("proof.jpg")               # nodriver: take screenshot
await tab.xsend_native(["#email", 0], [0.3, 0], "test@example.com")  # fantomas: type with emulation
```

## Native Methods (Browser-Level, Nodriver/CDP based)

See the [Fantomas API Reference]({{< relref "/docs/fantomas/fantomas-reference" >}}) for complete method signatures, parameters, and return types.

| Method | Description |
|---|---|
| `xclick_native(selector, sleep, proportion)` | Click element with optional cursor emulation |
| `xsend_native(selector, sleep, text)` | Type text with optional human-like keystroke delays |
| `xmove_native(selector)` | Move cursor along human-like path to element |
| `xsleep(time)` | Randomized sleep (+-0.5s jitter) |
| `xwaiter(selector, timeout, sleep)` | Wait for CSS selector with timeout |
| `xdetector(selector, sleep)` | Boolean check if element exists |
| `xscrape_attribute_in_iframe(iframe, selector, attr)` | Extract attribute from iframe element |
| `xscrape_html_in_iframe(iframe, selector)` | Extract outer HTML from iframe element |
| `xtemporary_zoom(value)` | Temporarily change page zoom |
| `xinject_js(command)` | Execute arbitrary JavaScript via CDP |
| `xupload_file(selector, path)` | File upload via DOM file input |
| `xselect_native(selector, sleep, value/text/index)` | Select dropdown option |

## XDO Methods (OS or display-server Level)

OS-level interaction via `xdotool` — harder for antibot systems to detect since events originate from the X11 window system rather than the browser's event loop.

| Method | Description |
|---|---|
| `xclick_xdo` | OS-level mouse click |
| `xsend_xdo` | OS-level text input with human-like delays |
| `xmove_xdo` | OS-level cursor movement |
| `xclick_iframe_xdo` | Click inside iframes at OS level |
| `xsend_iframe_xdo` | Type in iframe fields at OS level |
| `xmove_xdo_iframe` | Move cursor to iframe elements at OS level |

## Human Emulation

- **WindMouse Cursor Simulation:** Generates human-like cursor paths using a physics model with gravity, wind, momentum, and boundary avoidance (via numpy). See [Why Fantomas]({{< relref "/docs/fantomas/why-fantomas" >}}) for the anti-detection philosophy behind these choices.
- **Keystroke Emulation:** Randomized per-character delays (0.01s-0.7s range).
- **Cursor Visualization:** Debug overlay using a red square PNG (`feh`) and an in-browser JavaScript cursor follower.
- **Virtual Display:** Xvfb-based virtual display with configurable dimensions.

## Additional Modules

- **Identity Generation:** Fake identities via Faker (name, alias, birthday, postal code, password) with configurable language and age range.
- **Screen Management:** Virtual display lifecycle, screenshot capture via ImageMagick.
- **Geometry Helpers:** Viewport size, element coordinates/dimensions via CDP box model, including iframe element positioning.
- **Iframe Manager:** Recursive iframe document discovery in the DOM tree.
