# Jolla Browser Scroll Lab · v1.0

A self-contained set of browser scrolling tests for the **Jolla Phone 2026** and other Sailfish OS devices, designed to compare four browser environments:

1. Sailfish Browser (Gecko/EmbedLite)
2. Atlantic (WPE WebKit)
3. RooTitanium (Qt 6 / QtWebEngine)
4. Brave running via Android AppSupport

**No external dependencies**: no trackers, web fonts, external JavaScript, CDN images, browser extensions, build step, or server-side code.

## Quick start

Open `index.html`. The same URLs should be used in all four browsers. For easy cross-browser sharing, publish this folder via GitHub Pages (see below) or serve it from your PC on the local network.

- **Clean**: no diagnostic scripts or HUD at all on baseline and most tests. The JavaScript motion and JavaScript stress variants intentionally run JS.
- **Measured**: adds a small fixed HUD and a JavaScript `requestAnimationFrame` / scroll event / touchmove recorder. It **modifies the workload**, so always record clean runs too.

## Tests

| Group | Variants | Question |
| --- | --- | --- |
| 01 Basic HTML | 400 unstyled paragraphs / 210 styled text rows | Does trivially simple scrolling stutter? |
| 02 CSS effects | Control / Shadows / Filters / `translateZ(0)` | Do painting or compositor hints alter smoothness? |
| 03 Scroll layers | Control / Sticky header / Fixed overlay / Nested scroller | Does scroll-layer handling affect the behaviour? |
| 04 Local images | 12 / 100 / 50 large-display JPEGs | Does image-heavy painting or raster work change it? |
| 05 Animation | Static marker / CSS transform / JS rAF transform | Does continuous animation remain smooth while scrolling? |
| 06 Workload | 100 / 500 / 1,000 / 2,000 text rows / 500 + 4ms busy JS per rAF | At what load does visible scrolling degrade? |

**Important:** Do not interpret the JS measurements or the on-device application FPS overlay as proof of the number of distinct frames *displayed*. Different browsers may have different display refresh pacing or scroll-thread architectures. A camera recording is the display-side evidence.

## Recommended capture protocol

1. Keep phone orientation fixed, brightness fixed, refresh-rate settings unchanged, browser zoom at 100%, and disable power-saving modes. Note the Sailfish OS and browser version.
2. Open Test 01 **Absolute minimum, Clean** in all four browsers, each at the top of the document. Wait 2–3 seconds for the page to settle.
3. Record with a second device, ideally at **120 fps or 240 fps**, with focus/exposure locked if possible. Make sure the screen and your scrolling finger are visible. (The camera can itself have rolling-shutter or anti-flicker artefacts.)
4. For each recording: 3-second stationary view → slow finger drag → three quick flicks → allow deceleration → stationary view. Use similar swipe lengths; perfect manual repeatability is not possible.
5. Film all four browsers, then repeat in the reverse order to counter warm-up and thermal effects. Use the same content URL, clean versus clean.
6. If Test 01 is already broken in native browsers, run Test 05 (Static, CSS, JS), then Group 03. If only image-heavy or CSS-heavy pages misbehave, use 02 and 04 to isolate it. Use 06 last.
7. Repeat the most informative cases in **Measured** mode and in each browser tap `Start`, scroll for 15–25 seconds, `Stop`, `JSON`. Save downloaded files with the browser and test name.
8. Optionally include a second pass with on-device compositor FPS overlays disabled, since overlays may also affect performance.

Do **not** compare a Gecko forced 60-fps setting against other browsers at default 90 Hz without recording that variable. For the baseline, use Gecko `layout.frame_rate = -1` unless intentionally comparing overrides, and log every change. Restore your previous setting after testing.

## Serve locally

From this folder on a Linux PC:

```bash
python3 -m http.server 8765 --bind 0.0.0.0
```

Open `http://<PC-LAN-IP>:8765/` on the phone over the same Wi-Fi network. A local HTTP server avoids browser-specific restrictions around `file://` paths. You may need to allow port 8765 through the PC's firewall for LAN access; don't expose it to the public Internet.

### GitHub Pages

Create a public repo, upload the contents of this folder (not an enclosing parent directory), and use **Settings → Pages → Deploy from a branch → main / root**. Then open the generated `https://<username>.github.io/<repository>/` URL in each browser. Because all resources are relative, this works from a subpath. No Node/npm/build is needed. Check current GitHub Pages setup screens in case they change.

## JSON report fields

For every measured page, the exported report includes:

- Browser user agent and viewport dimensions/pixel ratio.
- Test variant and timestamp, recording duration.
- Every sampled `requestAnimationFrame` timestamp and document `scrollY` (up to 12,000 samples).
- p50/p95/p99 rAF callback intervals and counts above 22.2 and 33.3 ms.
- Captured scroll events (including inner scroll containers where present) and touchmove timing/position.
- Visibility-change events and whether the sample cap was reached.

These results are **approximate**, not a rendering pipeline tracer. `requestAnimationFrame` callbacks and `scroll` events do not reveal when the compositor presents buffers or when the physical screen refreshes. The HUD can create an additional composited layer. The JS animation tests necessarily have JS even in Clean mode.

The JSON file records the browser user-agent and viewport details, but not URLs visited outside the test, accounts, or precise location. Review it before sharing publicly.

## Project files

- `index.html` — suite launch page.
- `tests/*.html` — fully generated, individually openable test cases.
- `assets/lab.css` — common styling.
- `assets/measure.js` — the opt-in instrumentation.
- `assets/motion.js` — JS animation for one test.
- `assets/busy.js` — 4ms main-thread load for one test.
- `assets/image-*.jpg` — eight synthetic local images.
- `build.py` — recreates the test pages and landing page with Python 3.

For fair comparisons, don't edit test content between browser runs. When reporting issues to developers, include the exact test URL, mode (Clean/Measured), system version, browser version and video + any measured JSON.
