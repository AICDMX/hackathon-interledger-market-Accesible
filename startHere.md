# Native Language Market (24h Hackathon Cut)

Interledger-powered Django marketplace where funders post Native-language jobs and creators get paid once work is accepted. Content types: text, video, audio, images.

## First steps
- [ ] Check escrow system
- [ ] really having the langauge support is very important
- [ ] check if spoken language with accessiblity is easy or how hard it is or if we have to write a custom solution. 
- [ ] Make a basic system with wallets. users should have wallets
- [ ] users can do two things. create jobs or do jobs. idk if they should be a different type of user bu they should have basic 2 types of interfaces. 

## Must Ship
1. **Post & Submit Loop**
   - Funders create a “work brief” with title, description, target language/dialect, deliverable type(s), budget.
   - Creators browse briefs and upload submissions (file + note). Multiple submissions allowed until one is accepted.
2. **Creator-Led Offers**
   - Creators can publish ready-made assets (text/audio/video/image bundles) so funders can buy without a brief.
3. **Escrow & Payout**
   - When a brief is posted, funds move into escrow (Interledger test connector). Acceptance triggers release to creator wallet; rejection returns funds.
4. **Basic Trust Signals**
   - Minimal profile (name, language, wallet endpoint) for both roles.
   - Status tracker per brief: `Open → In Review → Funded/Rejected`.

### First jobs
- Written Languages
	- nahuatl
- Voice in the languages
	- otomi, nahuatl,mazaua,quechua

## Nice To Have (only if time remains)
- Lightweight chat or comment thread per brief.
- First jobs should have audio translations of native languages. for sure spoken spanish.
	- have good pictures with spoken transcriptions
- Auto transcription or thumbnail previews for uploaded media.
- Email/WhatsApp notifications when submissions land or are approved.
- Public landing page with live tally of funded work and total ILP payouts.
- GNAP possibly

## Build Flow (24h)
1. **Hour 0–4:** Scaffold Django + DRF, set up Postgres, create models for users, briefs, submissions, escrow transactions.
2. **Hour 4–12:** Implement funder brief CRUD, submission upload pipeline for text/video/audio/image files (S3 bucket or local storage), Interledger testnet escrow stubs.
3. **Hour 12–20:** Build acceptance/rejection flow that toggles escrow state and records payouts; add creator asset listing path.
4. **Hour 20–24:** Polish UI (Django templates/HTMX), seed demo data, rehearse demo: funder posts brief → creator submits audio sample → escrow releases on acceptance.
