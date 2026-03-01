---
title: 5.1. Why Fantomas
linkTitle: 5.1. Why Fantomas
weight: 1
description: What Fantomas brings over raw browser automation, how it defeats antibot systems, and why Display-server-level interaction matters
---

## The Problem

Modern antibot systems don't just check if your browser fingerprint looks legitimate. They analyze **how you interact** with the page. Cursor trajectories, click timing, keystroke rhythm, event sequences — all of this is collected, sent to remote servers, and classified by machine learning models as human or bot.

A raw automation tool like nodriver gives you an undetected Chrome instance. That solves static detection (no `navigator.webdriver` flag, no chromedriver artifacts). Besides, uou can buy, forge or retrieve some fingerprint that you would inject via FingerprintManager. But the moment your script clicks a button — instant cursor teleportation, instant text injection, perfectly regular timing — the behavioral layer flags it as automated.

Fantomas exists to close that gap.

## What Fantomas Adds Over nodriver

### Human-Like Cursor Movement (WindMouse)

nodriver clicks are instantaneous: the cursor teleports from nowhere to the target element. Fantomas generates **physics-based curved trajectories** using the WindMouse algorithm — a model with gravity (attraction toward target), wind (random lateral noise), velocity limiting, and smooth deceleration near the destination.

Every movement starts from wherever the cursor was left after the previous action. The cursor has persistent state, just like a real user's hand on a mouse.

```
nodriver click:
  [0,0] ──────────────────────────► [500,300]  (instant teleport)

Fantomas click:
  [0,0] ~~╮  ╭~~~╮                             (curved, variable speed,
           ╰~~╯   ╰~~╮  ╭~╮                     natural deceleration
                      ╰~~╯ ╰──► [500,300]        near the target)
```

### Randomized Keystroke Timing

nodriver injects text as a single CDP call — the entire string appears instantly in the input field. Fantomas types character by character with random delays between 10ms and 700ms per keystroke, mimicking the natural rhythm of human typing.


### Identity Generation

Built-in fake identity creation (name, alias, birthdate, password) via Faker, with accent normalization and configurable locale/age range. Each automation run can use a unique, realistic identity without hardcoded data.

### Virtual Display Management

Native Xvfb lifecycle management with configurable resolution.

### Cursor Visualization for Debugging

A debug overlay (red square via `feh` + in-browser JavaScript cursor follower) lets you visually verify that your cursor paths look human. This is essential when tuning automation against a specific antibot — you can't fix what you can't see.

### Two Interaction Strategies

Fantomas provides two parallel sets of methods for every action:

- **Native methods** (`xclick_native`, `xsend_native`, ...) — interact through Chrome DevTools Protocol, same as nodriver, but with human emulation layered on top
- **XDO methods** (`xclick_xdo`, `xsend_xdo`, ...) — interact through the X11 display server via `xdotool`, bypassing the browser entirely

Both include WindMouse cursor paths and keystroke randomization. The difference is **where the event enters the system** — and that difference matters against advanced antibots. More on this below.

---

## CDP vs xdotool: Why the Delivery Mechanism Matters

See the [Fantomas Reference — XDO Methods]({{< relref "/docs/fantomas/fantomas-reference#fantomasnodrivertab--xdo-methods" >}}) for the xdotool API.

The question is simple: **can an antibot tell whether a click came from CDP or not ?**

### How CDP Dispatches Events

When Fantomas (or nodriver) calls `Input.dispatchMouseEvent` via the Chrome DevTools Protocol:

```
Your code → CDP WebSocket/Pipe → Browser process → RenderWidgetHost → Renderer
```

The event is created **synthetically inside Chrome's browser process** and injected directly into the renderer. It skips the platform input layer, the compositor's event processing, and the native event coalescing pipeline.

### How xdotool Dispatches Events

When Fantomas calls `xdotool` :

```
xdotool → X Server → Chrome X11 event loop →
  PlatformEventSource → WindowEventDispatcher → Compositor → Renderer
```

The event enters at the **operating system / display-server level** and traverses Chrome's entire native input pipeline — the exact same path that real hardware input follows.

### What Antibots Can Observe

At the JavaScript level (where antibot scripts run), both CDP and xdotool events have `event.isTrusted = true`. A basic `addEventListener('click', ...)` cannot tell them apart. But advanced antibots dig deeper:

**Event property completeness**

CDP-dispatched events can have subtle inconsistencies:
- `movementX` / `movementY` may be zero or incoherent with the actual position delta
- `screenX` / `screenY` may not match `clientX` / `clientY` + window offsets correctly
- `sourceCapabilities` may be null or missing

xdotool events get all these properties filled naturally by Chrome's platform layer, because the event goes through the same processing as real hardware input.

**Event sequence integrity**

A real mouse click produces a specific sequence: `pointerdown` → `mousedown` → `pointerup` → `mouseup` → `click`, with consistent coordinates and timestamps across all events. CDP requires you to dispatch each event manually and maintain coherence yourself. xdotool generates the full native sequence automatically.

**Compositor side effects**

Real mouse movement triggers CSS `:hover` state changes, cursor appearance updates, and `mouseenter`/`mouseleave` events through the compositor. CDP events may not trigger all these side effects in the same way, because they bypass the compositor's event processing. xdotool events go through the compositor like real input, producing all expected side effects.

**Event coalescing and timing**

Chrome's input pipeline coalesces rapid mouse movements — multiple hardware events arriving within a single frame are merged into fewer events with natural timing jitter. CDP events are dispatched discretely, one by one, without coalescing. This difference in temporal patterns is observable through careful timing analysis.

**Prototype hooking**

Sophisticated antibots override JavaScript prototypes (`EventTarget.prototype.addEventListener`, `Object.getOwnPropertyDescriptor`, etc.) before any page script runs. This lets them intercept and deeply analyze every event that reaches JavaScript — checking property completeness, timestamp coherence, and sequence patterns. Against these hooks, the completeness of xdotool events provides an advantage over CDP's synthetic events.

### Who Actually Detects This?

Not every antibot operates at this level. 

The advanced tier collects detailed telemetry — full mouse trajectories with sub-millisecond timing, keyboard sequences, event property snapshots — and classifies it server-side with ML models. At this level, the difference between a synthetically constructed CDP event and a naturally processed xdotool event can tip the classification. 


## Future-Proofing: Full Behavioral Emulation

Antibot detection is an arms race. Today's advanced systems analyze event properties and timing. Tomorrow's systems might examine:

- GPU-level rendering traces to verify that cursor movement triggered real compositing
- Sub-frame timing correlations between input events and paint cycles
- Cross-session behavioral fingerprinting (does this "user" always move the mouse the same way?)

The design philosophy behind Fantomas is to **emulate everything at the lowest possible level**. By operating at the OS/display-server layer rather than the browser API layer:

- Events are indistinguishable from real hardware input at every layer of the stack
- All side effects (compositor, hover states, focus changes, coalescing) happen naturally
- No synthetic event construction is needed — the OS/display-server does the work

This approach means Fantomas doesn't need to reverse-engineer each antibot's specific detection heuristics in terms of behavor. Instead, it produces input that is **structurally identical to real human input** from the operating system down. Whatever new behavioral check an antibot adds, if it relies on how events are processed through Chrome's native pipeline, xdotool events will pass — because they take that exact pipeline.

The tradeoff is real: xdotool requires Linux, X11, and a running display server (Xvfb in containers). This infrastructure is provided by the [Agent container]({{< relref "/docs/reference/architecture/agent-internals" >}}). 