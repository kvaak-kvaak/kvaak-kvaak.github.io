#!/usr/bin/env python3
"""Generate independent, offline-friendly Jolla browser scrolling diagnostic pages.
Requires Python 3 only (bundled JPEG assets were generated separately).
Each Clean page has zero diagnostic scripts and remains fully static, except where
JavaScript animation or main-thread load is explicitly the feature being tested.
"""
from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).parent
TESTS = ROOT / 'tests'
TESTS.mkdir(exist_ok=True)

GROUPS = [
 ('01', 'Baseline HTML', 'The baseline: no JavaScript, images, animation, fixed layers or effects.', [
  ('01-raw','Absolute minimum · unstyled HTML','400 plain paragraphs: no CSS file, no JavaScript, no images. Use this first.', 'raw',400),
  ('01-baseline','Numbered HTML · 210 rows', 'Just text, thin borders and position markers. Use this second.', 'baseline',210)]),
 ('02', 'CSS effects', 'Identical content and geometry. Only the CSS painting/compositing hint changes.', [
  ('02-effects-control','Control · no effects', '200 identical text blocks, no special effects.', 'effects-control',200),
  ('02-effects-shadows','Box shadows','Same 200 blocks with shadows.', 'effects-shadows',200),
  ('02-effects-filters','CSS filters','Same 200 blocks with contrast/saturation filters.', 'effects-filters',200),
  ('02-effects-transforms','Transform hints','Same blocks with translateZ(0) and will-change; layer creation is browser-dependent.', 'effects-transforms',200)]),
 ('03', 'Scroll layers', 'Isolate sticky/fixed overlays and independently scrolling elements.', [
  ('03-layers-control','Control · normal flow','180 ordinary blocks.', 'layers-control',180),
  ('03-layers-sticky','Sticky header','Same 180 blocks; page header remains at top.', 'layers-sticky',180),
  ('03-layers-fixed','Fixed label','Same 180 blocks; an additional small fixed-position box.', 'layers-fixed',180),
  ('03-layers-nested','Nested scroller','180 blocks inside a 64vh scrolling box. Scroll inside the blue boundary.', 'layers-nested',180)]),
 ('04', 'Images', 'Local JPEGs, eager-loaded. Allow them all to load before filming.', [
  ('04-images-12','12 images','Low image density. Images share 8 bundled assets.', 'images-12',12),
  ('04-images-100','100 images','High image density, same image dimensions.', 'images-100',100),
  ('04-images-50large','50 large display images','More visible raster pixels per card; same original JPEG dimensions.', 'images-50large',50)]),
 ('05', 'Animation + scrolling', 'The moving marker tests scheduling while the document scrolls underneath.', [
  ('05-motion-static','Static marker','Fixed marker with no animation: the control.', 'motion-static',200),
  ('05-motion-css','CSS transform animation','A CSS compositor-friendly transform moves the marker continuously.', 'motion-css',200),
  ('05-motion-js','JavaScript rAF animation','JavaScript updates the marker transform on every rAF callback.', 'motion-js',200)]),
 ('06', 'Controlled workload', 'Increasing DOM size, then explicit main-thread work; avoid jumping to maximum.', [
  ('06-stress-100','100 elements','Low-load control.', 'stress-100',100),
  ('06-stress-500','500 elements','Moderate DOM workload.', 'stress-500',500),
  ('06-stress-1000','1,000 elements','Large DOM workload.', 'stress-1000',1000),
  ('06-stress-2000','2,000 elements','Very large DOM workload.', 'stress-2000',2000),
  ('06-stress-js4','500 + 4 ms JS/rAF','500 elements plus a deliberately busy main thread (~4ms per animation frame).', 'stress-js4',500)])
]

PHRASES = [
 'The quick brown fox crosses the street while the display follows a long page of ordinary text.',
 'Count the numbered rows and watch their movement relative to the thin horizontal registration marks.',
 'This paragraph repeats predictably; it does not fetch data, animate, use a web font, or run analytics.',
 'A smooth presentation moves by nearly equal visual distances at nearly equal time intervals.',
 'If the counter stays high but the page steps in jumps, frame production may differ from frame presentation.',
 'Keep the same zoom level, orientation and swipe pattern when comparing browser engines.',
]

def rows(count):
    result = []
    for i in range(1,count+1):
        phrase = PHRASES[(i-1)%len(PHRASES)]
        result.append('<section class="scroll-row"><h2>Row {0:04d} <span aria-hidden="true">·</span> {1}</h2><p>{2}</p><div class="marker-line">REFERENCE · {0:04d} · ━━━ ┊ ━━━ ┊ ━━━ ┊ ━━━</div></section><div class="ruler" aria-hidden="true"></div>'.format(i, ('A','B','C','D')[(i-1)%4],escape(phrase)))
    return '\n'.join(result)


def image_rows(count):
    return '\n'.join('<section class="image-row"><h2>Image {0:03d} / {1:03d}</h2><img src="../assets/image-{2:02d}.jpg" width="1200" height="800" alt="Locally generated geometric image {2}" loading="eager" decoding="async"><div class="marker-line">IMAGE REFERENCE · {0:03d}</div></section><div class="ruler" aria-hidden="true"></div>'.format(i,count,(i-1)%8+1) for i in range(1,count+1))


def content_for(kind,count):
    if kind=='raw':
        return '\n'.join('<p>Line {:04d} — A plain HTML document, without scripts, effects, assets or animations. Scrolling should move at a steady rate.</p>'.format(i) for i in range(1,count+1))
    if kind.startswith('images'):
        return image_rows(count)
    if kind == 'layers-nested':
        return '<div class="zone-label">Scroll inside the blue bordered area (separate scroll container)</div><div class="nested-zone" id="nested-scroller" tabindex="0">{}</div><div class="zone-label">Body scroll continues below</div>{}'.format(rows(count),rows(20))
    return rows(count)


def bodyclass(kind):
    cl=[]
    if kind.startswith('effects-'):
        cl.append('effect-'+kind.split('-',1)[1])
    if kind.startswith('layers-'):
        cl.append('layer-'+kind.split('-',1)[1])
    if kind == 'images-50large':cl.append('image-large')
    if kind.startswith('motion-'):cl.append(kind)
    return ' '.join(cl)


def testpage(slug,title,description,kind,count,measured):
    label='MEASURED · rAF/scroll/touch logging' if measured else 'CLEAN · minimal instrumentation'
    motion = ''
    if kind.startswith('motion-'):
        motion='<div class="motion-track" aria-label="Motion marker"><div class="caption">MOTION MARKER · {}</div><div class="line"></div><div class="dot" id="motion-dot"></div></div>'.format(escape(kind))
    scripts=''
    # The rAF animation and explicit JS busy-load scripts only appear on those controlled test variants.
    if kind=='motion-js':scripts+='\n<script src="../assets/motion.js"></script>'
    if kind=='stress-js4':scripts+='\n<script src="../assets/busy.js"></script>'
    if measured:
        scripts+='\n<script>window.LAB_TEST={};</script>\n<script src="../assets/measure.js"></script>'.format(json.dumps(dict(id=slug,name=title,kind=kind,mode='measured'),separators=(',',':')))
    note = ('No JavaScript or instrumentation is running on this page.' if not measured and kind not in ('motion-js','stress-js4') else
            ('This is a measured run; the HUD adds its own fixed overlay and JavaScript overhead.' if measured else 'This test intentionally uses JavaScript. There is no diagnostic recorder.'))
    other=slug+('' if measured else '-measured')+'.html'
    if measured:other=slug+'.html'
    footer='<div class="test-foot"><strong>{}</strong><p>{}</p><a href="../index.html">All tests</a><a href="{}">Switch to {} mode</a></div>'.format(escape(label),escape(note),escape(other),'clean' if measured else 'measured')
    if kind=='raw':
        # Avoid even loading the stylesheet or changing browser defaults in the clean run.
        extra_head='<link rel="stylesheet" href="../assets/lab.css">' if measured else ''
        raw_scripts=scripts
        return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Absolute minimum scroll test</title>{}</head><body><h1>Absolute minimum: 400 paragraphs</h1><p>Clean mode has no CSS or JavaScript. Measured mode loads the diagnostic HUD.</p><p><a href="../index.html">Back to tests</a> · <a href="{}">Other mode</a></p>{}{}</body></html>'.format(extra_head,other,content_for(kind,count),raw_scripts)
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>{title} — Jolla Scroll Lab</title><link rel="stylesheet" href="../assets/lab.css"></head>
<body class="{bodyclass}"><header class="test-head"><div class="inner"><div class="kicker">Jolla Browser Scroll Lab · {slug}</div><h1>{title}</h1><p>{description}</p><span class="meta">{label}</span></div></header>
<main class="test-body">{content}</main>{motion}{footer}{scripts}
</body></html>'''.format(title=escape(title),bodyclass=bodyclass(kind),slug=slug,description=escape(description),label=label,content=content_for(kind,count),motion=motion,footer=footer,scripts=scripts)


def index():
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>Jolla Browser Scroll Lab</title><link rel="stylesheet" href="assets/lab.css"></head><body><div class="home-shell"><header class="hero"><h1>Browser Scroll Lab</h1><p>Small, reproducible test pages for investigating visually jerky scrolling on Sailfish OS and comparing it with Android AppSupport. No external scripts, fonts or trackers.</p></header><div class="callout"><strong>Start with the “Absolute minimum” Test 01 — Clean</strong> in all four browsers. Film it at the same zoom and orientation. Then repeat with other tests. <strong>Clean</strong> means no diagnostics script; <strong>Measured</strong> adds a recorder HUD that itself can affect performance.</div><p class="smallprint">For the recordings, compare Sailfish Browser (Gecko), Atlantic (WPE WebKit), RooTitanium (QtWebEngine) and Android Brave. Use a second camera to capture visible motion and on-device FPS overlays. Do not interpret rAF callbacks as presented display frames.</p>']
    for num,heading,desc,variants in GROUPS:
        parts.append('<section class="group"><h2>{} — {}</h2><p>{}</p>'.format(num,escape(heading),escape(desc)))
        for slug,title,description,kind,count in variants:
            parts.append('<div class="variant"><div><strong>{}</strong><span class="description">{}</span></div><div class="actions"><a class="primary" href="tests/{}.html">Clean</a><a href="tests/{}-measured.html">Measured</a></div></div>'.format(escape(title),escape(description),slug,slug))
        parts.append('</section>')
    parts.append('<section class="group"><h2>Recording protocol</h2><p>One camera, same physical phone, fixed screen brightness and browser zoom. Record a 3-second still view, a slow sustained drag, three flicks and deceleration, then another still view. Repeat twice per browser, reversing order. Compare clean runs first.</p><p>Measured mode: tap Start, perform the gestures for 15–25 seconds, then Stop and export JSON. An Android file-download restriction may prevent saving; the report can also be viewed in the expandable text field.</p></section><p class="smallprint">v1.0 · This is a browser-level diagnostic, not a GPU or Wayland frame-presentation tracer. All content is bundled and works without an internet connection once hosted or copied locally.</p></div></body></html>')
    return '\n'.join(parts)

for group in GROUPS:
    for slug,title,description,kind,count in group[3]:
        for measured in (False,True):
            path=TESTS/(slug+('-measured' if measured else '')+'.html')
            path.write_text(testpage(slug,title,description,kind,count,measured),encoding='utf-8')
(ROOT/'index.html').write_text(index(),encoding='utf-8')
print('Generated',len(list(TESTS.glob('*.html'))),'test pages')
