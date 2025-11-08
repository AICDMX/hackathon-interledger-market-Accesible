# Priority Checklist (Must Ship) - Minimal Accessible Marketplace

## Critical First Steps
- [ ] Verify language support is working properly
- [ ] Investigate spoken language accessibility support
- [ ] Ensure all pages meet WCAG accessibility standards
- [ ] Test with screen readers and keyboard navigation

## Must Ship Features

### 1. Post & Submit Loop (Core Marketplace)
- [ ] Funders can create work briefs with:
  - Title
  - Description
  - Target language/dialect selection
  - Deliverable type(s) - text/video/audio/image (multiple allowed)
  - Budget (display only, no payment processing)
- [ ] Creators can browse briefs
  - Filter by language
  - Filter by deliverable type
  - View job details
- [ ] Creators can upload submissions (file + note)
  - File upload for all content types (text/video/audio/image)
  - Note field for additional context
  - Multiple submissions allowed until one is accepted
- [ ] File upload handling and storage
- [ ] Funders can review submissions
  - View uploaded files
  - Accept or reject submissions
  - See submission status

### 2. Basic User Profiles
- [ ] User registration with role selection (funder/creator/both)
- [ ] User login/logout
- [ ] Minimal profile page showing:
  - Name/username
  - Native languages
  - Preferred language
  - Role (funder/creator/both)
- [ ] Profile editing (update languages, preferred language)
- [ ] Profile visibility (public profiles for trust)

### 3. Job Status & Workflow
- [ ] Status tracker per brief: `Open ? In Review ? Accepted/Rejected`
- [ ] Job listing page (browse all jobs)
- [ ] My posted jobs page (for funders)
- [ ] My submissions page (for creators)
- [ ] Job detail page with:
  - Full job information
  - List of submissions
  - Accept/reject actions (for funders)
  - Submit button (for creators)

### 4. Accessibility (Critical)
- [ ] All forms have proper labels and ARIA attributes
- [ ] Keyboard navigation works throughout
- [ ] Screen reader compatibility
- [ ] High contrast mode support
- [ ] Focus indicators on all interactive elements
- [ ] Skip to main content links
- [ ] Alt text for all images
- [ ] Semantic HTML5 elements
- [ ] Error messages are accessible
- [ ] Language switcher is accessible

## First Jobs Content
- [ ] Written Languages:
  - [ ] Nahuatl content examples
- [ ] Voice in languages (if time permits):
  - [ ] Otomi audio samples
  - [ ] Nahuatl audio samples
  - [ ] Mazahua audio samples
  - [ ] Quechua audio samples

## Testing & Demo Prep
- [ ] End-to-end testing of complete flow:
  - Funder posts brief ? Creator submits ? Funder accepts/rejects
- [ ] Accessibility testing (WCAG compliance)
- [ ] Demo data seeding with native language content
- [ ] Demo script/rehearsal
- [ ] Bug fixes and polish
