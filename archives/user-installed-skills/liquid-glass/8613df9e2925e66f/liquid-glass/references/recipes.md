# Recipes and pitfalls

Patterns that survived contact with a real app, and the failures that produced them. Everything here assumes `assets/liquid-glass.css` is linked and the page shell carries `liquid-glass-backdrop`.

## Recipes

### Card

```html
<article class="liquid-glass liquid-glass--hover" appLiquidGlass>…</article>
```

The hover modifier lifts 2 px and raises the tint from 6% to 11%. It does not touch the refraction — the map is size-keyed, and a hover that changed size would rebake it every time the pointer crossed the card.

### Circular control

Drive the diameter and the radius from one number, so every round control in a bar matches without a second constant to keep in sync:

```css
:root {
  --topbar-h: 3rem;
  --control-radius: calc(var(--topbar-h) / 2);
}
.control {
  width: var(--topbar-h);
  height: var(--topbar-h);
  border-radius: var(--control-radius);
}
```

The directive reads the computed radius, so a circle refracts around its whole rim with nothing extra declared.

### Colored glass (FAB, primary CTA)

Override the tint only — rule 2 in `SKILL.md`. The rim, the border and the refraction stay as they are:

```css
.fab {
  background: linear-gradient(155deg, rgba(79, 70, 229, 0.55), rgba(67, 56, 202, 0.42));
  border: 1px solid rgba(79, 70, 229, 0.5);
  box-shadow:
    0 12px 28px rgba(67, 56, 202, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}
```

Note the inset highlights are re-stated: replacing `box-shadow` wholesale drops the rim, and a colored panel without a rim reads as a flat button that happens to be translucent.

### Modal

```html
<div class="liquid-glass-scrim" role="dialog" aria-modal="true">
  <div class="liquid-glass liquid-glass--modal" appLiquidGlass>…</div>
</div>
```

### Dropdown

```html
<div class="liquid-glass-menu" role="menu">…</div>
```

No directive: a menu is short-lived and often re-rendered, and per-open map bakes are wasted work. Pair with your own entry animation; override `border-radius` after the class if the panel needs another.

### Section inside a glass panel

Nothing. No background, no border, no radius:

```css
.panel__header {
  display: flex;
  gap: 0.5rem;
  padding: 0.6rem 0.8rem;
  background: transparent;
  border: none;
}
```

Add `overflow: hidden` to the *panel* when a child would otherwise square off its rounded corners.

## Pitfalls

**A "not yet sent" or "disabled" state drawn with a dashed border.** It cuts a hard edge across the rim, and the panel stops reading as glass. Carry the state in a badge, in opacity, or in type weight instead.

**Nesting glass in glass.** Two rims and two tints stack; the inner panel reads darker than everything around it and the effect inverts — the thing you meant to raise looks sunken. One glass surface per stack. If a nested surface genuinely needs separation, use spacing.

**Reaching for more blur when the glass looks gray.** The cause is almost always rule 1: the backdrop is flat. More blur destroys the little variation that is left. Fix the backdrop.

**Text over the calm part of the mesh.** Glass is transparent, so contrast varies across the page. Check the labels that sit over the brightest glow, and switch to the menu or modal tier when a surface must be readable regardless of what lands behind it.

**A glass panel that scrolls with content behind it.** `backdrop-filter` samples what is behind the element *now*, so a card over a scrolling list shows the list sliding under it. This is correct and is most of the appeal — but it makes small text on top of a busy list unreadable. Use the menu tier for those.

**Transform or filter on an ancestor.** Either creates a containing block and can knock the backdrop sampling out of alignment, or clip it entirely. If a panel goes blank inside an animated parent, look up the tree before touching the glass.

**Chips built on the panel tier.** Twenty chips means twenty canvas bakes and twenty filter nodes for an effect nobody can see at that size. `liquid-glass-chip` exists for this.

**A radius off the scale.** Fine when deliberate — a surface meant to read as distinct can take a larger one — but the directive shapes the map from the *computed* radius, so the CSS and the refraction never disagree. Do not pass a radius to the directive.

**Only one theme checked.** The rim is white in both themes but the border flips (dark hairline on light, white on dark). A panel tuned in the dark and shipped without a light pass gets a border that is either invisible or a hard gray line.
