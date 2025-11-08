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

## Key Flows
1. **Sign-In / Language Pick**: minimal form, phone-number first, language dropdown pinned to the top-right.
2. **Create Offer**: flow enters via floating action button, uses stacked sheets for details, previews the card before publishing.
3. **Wallet Actions**: two big buttons (Receive QR, Send) followed by transaction timeline and contextual help chip.
4. **Support**: list of contact methods with large icons; tapping opens chat/voice while keeping the background context.
5. **Notifications & Alerts**: toast stack that summarises actions (offer approved, payment received) with one-tap shortcuts to view details; never hijack the full viewport.

## Component System
- **Tokens**: spacing (4/8/16 base), colours (off-white background, charcoal text, teal primary, amber warning), radii (12 px), and shadow presets.
- **Atoms**: icon button, chips, badges, toggles; each shares the same elevation and motion curves (200 ms ease-out).
- **Molecules**: balance card, offer card, transaction row, language selector, snackbar.
- **Layouts**: bottom tab shell with scrollable content, modal sheets for forms, responsive grid that collapses to single column on <480 px.

## Mobile Layout Constraints
- **Safe Areas**: Account for 24 px top and 34 px bottom insets to avoid OS chrome; floating action button sits above the tab bar by 12 px.
- **Breakpoints**: 320–479 px = single column, 480–767 px = split header + content panes, ≥768 px = two-column card layout with persistent filters.
- **Performance Budget**: target ≤75 DOM nodes above the fold; defer secondary content (e.g., recommendations) with `loading="lazy"`.
- **Gestures**: horizontal swipes only on card lists; never conflict with Android back swipe areas (12 px edges stay gesture-free).

## Technical Notes
- Tailwind or CSS variables to centralise tokens so Django templates inherit consistent styles.
- Use SVG sprite for icons to keep downloads light and allow easy colour overrides.
- Prefer HTMX/alpine micro-interactions over heavy JS; keep bundle <150 KB gzip to stay fast on entry-level devices.
- Add Lighthouse mobile performance budget (LCP < 2.5 s on 4G, interaction ready < 200 ms).
- Instrument key interactions (offer publish, wallet send, support tap) with custom events so we can detect friction on small screens.
- Use CSS `prefers-reduced-motion` hooks to drop parallax/shadow animations for accessibility and avoid jank on low-end GPUs.

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
