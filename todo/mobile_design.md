# Mobile Design Direction

## Purpose
- Deliver a focused mobile-first experience for the Django marketplace.
- Communicate trust quickly through clean typography and roomy layouts.
- Prioritise touch targets and iconography so navigation feels effortless.

## Visual System
- **Icons**: extra-large (56–64 px) outline icons with subtle duotone fills; keep sets consistent per section.
- **Typography**: two-weight system (Semibold headings, Regular body) at 18–22 px to maintain readability on small screens.
- **Spacing**: 16 px base grid, double padding (32 px) around cards to keep the interface airy.
- **Palette**: dark text on off-white backgrounds with two accent colours (teal for calls to action, amber for alerts) for clear contrast.
- **Cards**: rounded corners (12 px) with soft drop shadows for depth without clutter.

## Interaction Patterns
- One-handed navigation with sticky bottom tab bar (Home, Explore, Wallet, Support).
- Floating action button for the primary task (e.g., "Create Offer"), using the teal accent and an icon-only label.
- Swipe gestures for secondary actions (e.g., archive, favourite) to keep the main view uncluttered.
- Inline confirmations and snackbar messages rather than modal dialogs to avoid interrupting flow.

## Key Screens
1. **Home Dashboard**: hero card with current balance, quick-access icon row (Send, Receive, Scan, History), and a list of recent activity cards.
2. **Offer Explorer**: stacked cards with large marketplace icons and quick filters as chips; emphasise category icons over text to speed scanning.
3. **Wallet**: big QR/pay buttons, transaction timeline, and a prominent "Add Funds" card.
4. **Support & Accessibility**: simple list with icon tiles for chat, voice call, and knowledge base; include a quick language toggle.

## Accessibility Guardrails
- Minimum 4.5:1 contrast for text, 3:1 for large icon buttons.
- Touch areas ≥ 48 px with generous spacing to prevent accidental taps.
- Provide text labels beneath every icon; rely on colour only as a supporting cue.
- Keep animated elements under 200 ms and provide reduced-motion support via CSS media queries.

## Implementation Checklist
- [ ] Build a shared Tailwind (or CSS) token file for spacing, colours, and radii.
- [ ] Create an icon component that enforces size and colour rules.
- [ ] Implement the sticky tab bar plus floating action button wrapper.
- [ ] Design reusable card and chip components that mirror the spacing/typography standards.
- [ ] Add accessibility tests (contrast, keyboard navigation, screen-reader labels) to CI.
- [ ] Draft empty, error, and offline states for each key screen so engineers have references beyond the “happy path”.
- [ ] Define analytics events for offer publish, wallet send/receive, and support taps before implementation.
- [ ] Document safe-area behaviour, gesture affordances, and breakpoints in the design system site.
- [ ] Produce lightweight prototypes (12 fps GIF or Lottie) for key micro-interactions to communicate intent without relying on lengthy specs.

## Workstreams & Owners
- **Design System (Avery)**: finalise tokens, iconography, and card/chip components; deliver inspected Figma frames by Friday.
- **Navigation & Shell (Leo)**: spike on sticky tab bar + FAB wrapper in Django templates with Tailwind utilities; capture open issues.
- **Wallet Experience (Imani)**: validate QR display flow, add state chart for QR expiry + offline view.
- **Support & Accessibility (Mina)**: verify translation lengths with pseudo-loc, run screen-reader scripts, and feed defects into Jira.

## Research & Validation
- Schedule 5 remote usability sessions on low-end Android to observe reachability of FAB + bottom tabs.
- Capture latency metrics (LCP, TTI) on throttled 4G using Lighthouse mobile config; attach screenshots to design doc.
- Confirm brand accent colour and typography license coverage with stakeholder steering committee.
- Decide on push vs. SMS notifications by outlining backend + cost implications, then bring to next product review.

## Dependencies / Risks
- Waiting on localisation strings for Tagalog + Swahili before shipping Support screen.
- Security review needed for wallet QR share flow (prevents screenshots? auto-expire?).
- Service worker approach must be aligned with engineering team; offline caching plan is currently unassigned.
