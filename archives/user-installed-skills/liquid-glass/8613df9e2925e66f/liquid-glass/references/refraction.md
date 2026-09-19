# Refraction: how it works, and how to port it

`assets/liquid-glass.directive.ts` is the reference implementation (Angular). Everything below is framework-agnostic — a port is a transcription of these formulas plus your framework's lifecycle hooks. Read it before changing constants; every one of them was fit against a reference render, not picked.

## The pipeline

Real glass bends what is behind it, most sharply near its edge. CSS has no such primitive, so the effect is built out of one that is adjacent: `feDisplacementMap` moves each pixel of an input by an offset read out of a second image.

Per element, once per size:

1. **Bake** a displacement map into a `<canvas>`: for every pixel, compute the refraction offset and encode it into the R (x) and G (y) channels around neutral. Export as a `data:` URL.
2. **Build an SVG filter** in a shared, hidden `<svg><defs>` on `document.body`:
   `feImage` (the baked map) → `feDisplacementMap` (`in="SourceGraphic"`, `in2="map"`, `xChannelSelector="R"`, `yChannelSelector="G"`) → `feGaussianBlur` (the frosting).
3. **Point the element at it**: `element.style.backdropFilter = 'url(#' + id + ')'`.

Because it is a *backdrop* filter, `SourceGraphic` is the live page behind the element. The library this ports from snapshots the page with html2canvas; using the backdrop instead means scrolling, theme switches, animation and content changes are tracked for free, with nothing to invalidate.

## The field

`GLASS_PRESET` mirrors the upstream shader's uniforms; distances are exponential falloff rates per pixel from the shape edge, intensities are in page-texture fraction units.

```
edgeIntensity 0.015   rimIntensity 0.028   baseIntensity 0.05
edgeDistance  0.5     rimDistance  1.7     baseDistance  0.2
cornerBoost   0.06    rippleEffect 0.26    blurRadius   2      warp false
```

For a pixel at normalized `(cx, cy)`, `distPx` CSS pixels inside the rounded-rect edge:

```
edgeFall = exp(-distPx * edgeDistance)
rimFall  = exp(-distPx * rimDistance)
baseFall = 1 - exp(-distPx * baseDistance)

total  = (warp ? baseFall * baseIntensity : 0)
       + edgeFall * edgeIntensity
       + rimFall  * rimIntensity

n      = normalize(cx - 0.5, cy - 0.5)               // normal in texcoord space
corner = exp(-(max(min(cx,1-cx), min(cy,1-cy)) * min(w,h)) * 0.3) * cornerBoost
ripple = sin((distPx / min(w,h)) * 25) * rippleEffect * rimFall

fx = ( n.x * (total + corner) - n.y * ripple) * pageW
fy = ( n.y * (total + corner) + n.x * ripple) * pageH
```

`distPx` is the signed distance to a rounded rectangle, clamped at the edge:

```
tx = |px - w/2| - (w/2 - r)
ty = |py - h/2| - (h/2 - r)
distPx = max(-(hypot(max(tx,0), max(ty,0)) + min(max(tx,ty),0) - r), 0)
```

Three things about this field are load-bearing:

- **`warp: false` by default.** Center distortion looks impressive on a demo tile and makes text under the middle of the panel unreadable. The base term is switched off entirely rather than tuned down.
- **`pageW`/`pageH` are the viewport**, not the element. The shader displaces in fractions of the page texture; the live equivalent of that texture is the viewport, so displacement is viewport-proportional. This is why the map must be rebuilt on window resize, not only on element resize.
- **The offsets peak in a 1–2 px band at the rim.** Everything that follows is about not losing that band.

## Encoding, and the bias nobody expects

`feDisplacementMap` decodes byte `b` as `scale * (b/255 - 0.5)`. The obvious neutral, 128, is **not** zero: `128/255 = 0.50196`, so a flat interior would drift by `scale/510` px. With `warp` off the middle of the panel is supposed to be perfectly undistorted, and that drift is exactly what you would notice.

So pre-subtract the decode bias:

```js
scale = max(maxAbs * 2, 1e-4)
bias  = scale * (128 / 255 - 0.5)
R = clampByte(255 * (0.5 + (dx - bias) / scale))
G = clampByte(255 * (0.5 + (dy - bias) / scale))
B = 128, A = 255
```

## Four constants that stop it looking wrong

| Constant | Value | Why |
|---|---|---|
| `SUPERSAMPLE` | 2 | The rim lives in 1–2 px. At 1× the browser resamples the map into a wide smear; 2× gives `feImage` enough source detail to keep the edge lens crisp. |
| `MAX_MAP_EDGE` | 1400 | Refraction is edge-local, so a wide topbar does not need a 2× map through its neutral middle. Let the factor fall below 1 for big surfaces (floor 0.25) to bound the per-pixel bake and the data-URL size. |
| `BLUR_STD_PER_RADIUS` | 0.35 | The upstream blur is a 13-tap page-texture kernel with no 1:1 SVG gaussian equivalent; this factor was fit so `blurRadius: 2` matches its frosting. |
| filter region margin | `scale/2 + 3·blurRadius·BLUR_STD_PER_RADIUS` | Edge pixels sample up to `scale/2` away plus the blur spread. A region that does not extend past the box clips the refraction to transparent **at the corners** — and since displacement is viewport-proportional, on a small element this margin can exceed the box, so a fixed 30% is wrong. Size it from the field. |

## Lifecycle: what a port must get right

- **Rebuild on element resize** (`ResizeObserver`) **and on window resize** — the latter changes `pageW`/`pageH` for every instance at once, so debounce it (~180 ms) or a drag-resize rebakes every map every frame. Coalesce bursts into one rebuild per animation frame.
- **Key the filter** on `[w, h, radius, pageW, pageH, config]` and share it: a list of same-size cards is the common case and wants one filter, not fifty. Refcount, and drop the node at zero.
- **Check `node.isConnected` before reusing** a cached filter. If the shared `<defs>` was ever detached, its `url(#id)` silently resolves to nothing and every panel goes blank.
- **Run outside your framework's change detection.** The observers fire constantly and touch no bound state.
- **Read the radius from computed style** (`borderTopLeftRadius`, resolving `%` against `min(w,h)`, clamped to `min(w,h)/2`) rather than taking it as an input — then the CSS stays the single source of shape.
- **Gate on engine, not `@supports`.** SVG-referenced backdrop filters render in Chromium only; Safari parses the declaration and paints nothing, so a feature query reports success. Check `navigator.userAgentData.brands` for Chromium/Chrome/Edge, falling back to `/Chrome\//` on the UA string. Where unsupported, do nothing at all — the stylesheet's `backdrop-filter: blur(3px) saturate(125%)` fallback stays in effect and the panel still looks like glass.
- **Clean up**: disconnect the observer, remove the window listener, cancel the pending frame and release the filter.

## Attribution

The field formulas are transcribed from `container.js` of [dashersw/liquid-glass-js](https://github.com/dashersw/liquid-glass-js) (MIT, © 2025 Armagan Amcalar). The notice at the top of `assets/liquid-glass.directive.ts` travels with any copy or port of them.
