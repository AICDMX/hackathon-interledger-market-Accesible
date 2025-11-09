# Design Doc

## Context
- Django marketplace app must feel native on mobile web while remaining accessible on low-bandwidth devices.
- Users are primarily buyers and sellers managing offers, wallets, and support conversations on the go.

## Goals
1. Make the first-time experience understandable in under 30 seconds with icon-forward navigation.
2. Keep every critical task within two taps from the home screen.
3. Maintain WCAG AA compliance, even when users zoom in or switch languages.

## Experience Pillars
- **Iconic Navigation**: Sticky bottom tabs plus oversized quick-action icons for Send, Receive, Scan, and History.
- **Card-Centric UI**: All marketplace data (offers, balances, activity) surfaces as rounded cards on a soft background.
- **Calm Feedback**: Use snackbars and inline validations; avoid disruptive modals except for destructive actions.
- **Offline Friendly**: Cache icons, typography, and the last known balance so the dash is still useful when offline.
- **Assistive Defaults**: Every critical control keeps a text label, focus halo, and optional haptic cue so screen readers and switch devices remain fast.

## Shared Design Tokens
Every visual decision lives in the token source of truth (`docs/tokens.md` once generated). No component may ship inline CSS; Tailwind utilities and CSS custom properties both pull from the same data.

| Group | Values | CSS Variable / Tailwind key | Usage Notes |
| --- | --- | --- | --- |
| Spacing | 4, 8, 12, 16, 24, 32, 48 px | `--space-1`…`--space-6` / `spacing: {2:0.5rem,3:0.75rem,4:1rem,6:1.5rem,8:2rem,12:3rem}` | Stack layouts with `gap` utilities, never ad-hoc padding. |
| Radii | 8 px inputs, 12 px cards, 20 px sheets, 999 px pills | `--radius-input`, `--radius-card`, `--radius-sheet`, `--radius-pill` | Keep shapes consistent between light/dark themes. |
| Typography | Heading 20/28 Semibold, Body 16/24 Regular, Caption 14/20 Regular | `--font-heading`, `--font-body`, `--font-caption`; Tailwind `fontSize.heading = ['1.25rem', '1.75rem']` etc. | Pairing includes weight + line-height; do not override per component. |
| Colours | `#0F172A` text, `#F5F5F0` background, `#0FBAB8` primary, `#FFB347` warning, `#1B2435` surface, `#E2E8F0` border, `#22C55E` success | `--color-text`, `--color-bg`, `--color-primary`, `--color-warning`, `--color-surface`, `--color-border`, `--color-success` | Derive subtle gradients (8%/16% overlays) from base tokens only. |
| Shadows | Card: `0 8px 24px rgba(15,23,42,.08)`; FAB: `0 12px 32px rgba(15,186,184,.45)`; Sheet: `0 20px 48px rgba(15,23,42,.15)` | `--shadow-card`, `--shadow-fab`, `--shadow-sheet` | Swap to 1 px border when `prefers-reduced-transparency` is on. |
| Motion | Default 200 ms ease-out, Fast 120 ms ease-in, Slow 320 ms ease | `--motion-default`, `--motion-fast`, `--motion-slow` | Wrap transitions in `@media (prefers-reduced-motion: reduce)` to zero durations. |

**Usage pattern:** Shared stylesheet exports the tokens and Tailwind config maps to them:
```css
:root {
  --color-primary: #0FBAB8;
  --space-4: 1rem;
}
.card {
  padding: var(--space-5);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}
```
Developers consume these via utility classes (`p-6`, `bg-surface`, `rounded-card`). Any new value must be added to the token file first so the system stays simple and modern.

## Key Flows
1. **Sign-In / Language Pick**: minimal form, phone-number first, language dropdown pinned to the top-right.
2. **Create Offer**: flow enters via floating action button, uses stacked sheets for details, previews the card before publishing.
3. **Wallet Actions**: two big buttons (Receive QR, Send) followed by transaction timeline and contextual help chip.
4. **Support**: list of contact methods with large icons; tapping opens chat/voice while keeping the background context.
5. **Notifications & Alerts**: toast stack that summarises actions (offer approved, payment received) with one-tap shortcuts to view details; never hijack the full viewport.

## Job States

See [job-states.md](job-states.md) for complete documentation of job state definitions and transitions.

## Component System
- **Tokens**: spacing (4/8/16 base), colours (off-white background, charcoal text, teal primary, amber warning), radii (12 px), and shadow presets.
- **Atoms**: icon button, chips, badges, toggles; each shares the same elevation and motion curves (200 ms ease-out).
- **Molecules**: balance card, offer card, transaction row, language selector, snackbar.
- **Layouts**: bottom tab shell with scrollable content, modal sheets for forms, responsive grid that collapses to single column on <480 px.

## Shared UI Building Blocks
- **Icon Component**: SVG sprite loader that accepts `size` (`md` 48 px, `lg` 64 px) and `tone` (`primary`, `muted`, `warning`, `success`). Always renders with `<title>` for accessibility; inherits `currentColor`.
- **Primary Button**: 56 px tall pill, min width 96 px, icon optional. Uses `--color-primary` gradient background, `--shadow-card` for regular button, `--shadow-fab` when `variant="fab"`.
- **Card Shell**: uses `padding: var(--space-6)`, `gap: var(--space-4)`, `border-radius: var(--radius-card)`. Variants (balance, offer, support) only shift content slots; tokens stay identical.
- **Chip**: 36 px height, uppercase label, horizontal padding = `space-4`. Selected state uses `--color-primary` at 12% fill with full-colour text.
- **Snackbar / Banner**: full-width minus `space-4` margins, anchored above tab bar. Shares `--radius-card` and `--motion-fast` for entrance.
- **Empty/Error/Offline Templates**: reuse card shell plus icon component set to muted tone, CTA button below body copy. Strings live in localisation files so translations stay in sync.

## Mobile Layout Constraints
- **Safe Areas**: Account for 24 px top and 34 px bottom insets to avoid OS chrome; floating action button sits above the tab bar by 12 px.
- **Breakpoints**: 320–479 px = single column, 480–767 px = split header + content panes, ≥768 px = two-column card layout with persistent filters.
- **Performance Budget**: target ≤75 DOM nodes above the fold; defer secondary content (e.g., recommendations) with `loading="lazy"`.
- **Gestures**: horizontal swipes only on card lists; never conflict with Android back swipe areas (12 px edges stay gesture-free).

## Navigation Shell
- **Sticky Tabs**: 4-item bottom bar, 56 px tall, uses `safe-area-inset-bottom` padding. Labels use caption token; icons stay 32 px.
- **Floating Action Button**: anchored right, offset `space-5` from edges, floats 12 px above tabs. Defaults to icon-only; long-press surfaces tooltip card using shared tokens.
- **Safe-Area + Scroll**: content wrapper adds `padding-bottom = tab height + fab offset + space-4` so nothing hides behind navigation. Modals respect `--radius-sheet` and appear from bottom with `--motion-default`.
- **Gestures & States**: Tabs support double-tap to scroll to top, list swipes limited to horizontal card rows. Connectivity banner sits between hero card and rest of feed so navigation remains visible. FAB suppressed on screens with destructive actions (e.g., payment confirmation) to avoid accidental taps.

## Technical Notes
- Tailwind or CSS variables to centralise tokens so Django templates inherit consistent styles.
- Use SVG sprite for icons to keep downloads light and allow easy colour overrides.
- Prefer HTMX/alpine micro-interactions over heavy JS; keep bundle <150 KB gzip to stay fast on entry-level devices.
- Add Lighthouse mobile performance budget (LCP < 2.5 s on 4G, interaction ready < 200 ms).
- Instrument key interactions (offer publish, wallet send, support tap) with custom events so we can detect friction on small screens.
- Use CSS `prefers-reduced-motion` hooks to drop parallax/shadow animations for accessibility and avoid jank on low-end GPUs.
- Publish tokens via `tokens.css` and extend `tailwind.config.js` so templates only rely on shared utility classes; lint pipeline flags inline styles.
- Component partials live under `templates/components/` and consume tokens through `class` attributes, keeping markup clean and modern.

## Analytics & Accessibility Validation
- **Events**: `offer_publish`, `wallet_send`, `wallet_receive`, `support_start`, `language_switch`, `offline_mode`. Each payload includes `screen`, `latency_ms`, `device_width`, `language`.
- **Instrumentation Hooks**: Buttons/components expose `data-analytics-id`; HTMX actions fire `customEvent` for backend ingestion. Token adoption tracked via ESLint rule warning on inline styles.
- **Accessibility Tests**: axe-core + Pa11y run on key screens; automated check verifies contrast between tokens, focus order through tabs, and reduced-motion toggles. Manual scripts cover TalkBack + VoiceOver for navigation shell and wallet flow.
- **Research Cadence**: monthly low-end Android sessions to validate reachability; quarterly accessibility audits with external testers.

## Risks & Open Questions
- Need confirmation on primary accent colour for brand alignment.
- Content strategy for multilingual labels still pending—affects icon labels and card widths.
- Offline caching approach (Service Worker vs. Django caching headers) not decided.
- Wallet QR flows need security review (screen capture blocking? timed QR expiry?) before implementation.
- Requires decision on whether notifications arrive via push (service worker) or SMS; impacts backend investment.

## Next Steps
1. Finalise colour tokens with stakeholders.
2. Build icon component and tab shell in Django templates (or React component if using SPA for parts).
3. Prototype home dashboard and wallet views in Figma, then convert to Tailwind/CSS snippets.
4. Run accessibility review with screen readers plus contrast tooling before launch.
5. Document empty/error/offline states for every key flow and add them to the component library.
6. Add analytics instrumentation plan (event names, payload, retention) before coding so engineers can wire it once.
7. Validate gesture model with at least five users on low-end Android hardware to ensure the sticky tabs remain reachable.
8. Stand up token documentation page (Storybook or md doc) that auto-syncs with Tailwind config.
9. Wire analytics + accessibility checks into CI to keep regressions from landing.
