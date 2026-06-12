# Demo Upgrade Plan

## What I need from you

### 1. Profile photos (6-10 images)
Headshots or photos for each demo user. Doesn't need to be real people — stock photos, AI-generated, or illustrations all work. These make the user profiles and application cards feel alive instead of blank avatars.

**How I'll use them:** Set as `profile_image` on each demo user so they show up on applications, submissions, and the browse page.

**Files needed:**
- `maria.jpg` — María Santos (Nahuatl creator)
- `carlos.jpg` — Carlos Hernández (Otomí creator)
- `ana.jpg` — Ana Quispe (Quechua creator)
- `luis.jpg` — Luis Gómez (Tsotsil creator)
- `rosa.jpg` — Rosa Chan (Maya creator)
- `juan.jpg` — Juan López (Mixteco creator)
- `roberto.jpg` — Roberto Martínez (funder)
- `miguel.jpg` — Miguel Torres (both)
- `sofia.jpg` — Sofia Morales (both)

### 2. A few profile audio clips (optional but high-impact)
Short (~10-15 second) audio intros from 2-3 "creators" introducing themselves in Spanish or a native language. Even just one or two would demonstrate the core accessibility feature — that users with limited written language can present themselves through voice.

**How I'll use them:** Set as `profile_audio` on user profiles and auto-filled into job applications.

### 3. Sample submission files (optional)
Any real-world examples of the kind of work creators would submit:
- A short audio recording of someone speaking in an indigenous language
- A hand-drawn or digital illustration (for the art jobs)
- A short text translation sample

**How I'll use them:** Attach to demo submissions so the review flow shows real deliverables instead of empty cards.

---

## What I can do right now (no assets needed)

### Users — Make them feel like real people
- Add `profile_note` bios for every user (personalized, realistic intros about their background, skills, and why they're on the platform)
- Add a second funder account representing an NGO ("Voces Vivas Foundation") to show multiple organizations using the platform
- Add a community organization funder ("Clínica Comunitaria Esperanza") for the health-related jobs

### Jobs — Create a lived-in marketplace
Right now all 26 jobs are from one funder. I'll:
- Spread jobs across 3 funders so it looks like a real marketplace
- Add realistic job descriptions with context (who's requesting, why, for what community)
- Create jobs at every lifecycle stage with matching activity:
  - **Recruiting** jobs with real applications from creators (with profile notes)
  - **Selecting** jobs where funder is choosing between applicants
  - **Submitting** jobs with in-progress draft submissions
  - **Reviewing** jobs with completed submissions ready for funder review (with text_content filled in)
  - **Complete** jobs with accepted submissions and realistic deliverable text
- Reduce total job count to ~12-15 high-quality ones instead of 26 generic ones

### Submissions — Show the full workflow
- Create text submissions with actual translation content (realistic Nahuatl/Otomí/Quechua translations or plausible placeholder text)
- Add submission notes from creators explaining their work
- Mix of accepted, pending, and draft submissions so every state is visible

### Applications — Show community engagement
- Multiple applications per recruiting job (2-4 creators applying)
- Realistic `profile_note` on each application ("Soy hablante nativo de otomí del Valle del Mezquital, he trabajado como intérprete comunitario por 5 años...")
- Some applications already selected, showing the full pipeline

### Audio integration
- Wire up the existing Otomí audio files in `media/Audio/mp3/` to the audio snippet system so the UI audio buttons actually work
- Create `StaticUIElement` entries for each UI element that has audio

---

## Impact summary

| Before | After |
|---|---|
| 9 users with blank profiles | 12+ users with bios, notes, and (with your photos) images |
| 26 jobs all from one funder | 12-15 jobs from 3 funders across all lifecycle stages |
| No applications exist | 15+ applications with realistic profile notes |
| No submissions exist | 8+ submissions with actual content |
| Audio files sitting unused in /media | Audio wired into the snippet system |
| Every login looks the same | Each user login tells a different story |

---

## Recommended demo walkthrough after upgrade

1. **Browse as anonymous** → See a lively marketplace with real jobs
2. **Login as `carlos_otomi`** → See dashboard with applications, accepted jobs, work in progress
3. **Login as `demo_funder`** → See owner dashboard with submissions to review, contracts to manage
4. **Login as NGO funder** → See a different set of jobs, different stage of work

---

## Drop assets here
Put any images/audio/files in `/home/dev/marketplace/demo-assets/` and let me know. I'll wire everything up.
