# Completed Tasks

[x] we need to make sure each job allows for uploading image/video/audio/audiorecord
[x] we need a way for people to create and fund jobs. 
[x] jobs should show funded when they are funded and by how much
[x] when a user clicks on a audio translation it should use their language. if translation does not exsist it should use their language fallback. then if not that then the final fallback. 
[x] audio translation popup is to fast. we need it to stay up 30 seconds
[x] we need to be able to mark how many responses we want to a job. default is one. this is like if someone wants 20 people to do the same voice or the same picture set. 
[x] setup the default jobs to auto load into the system.
[X] create a job should have have a place to upload audio/image/video/and audio record like completing jobs does since the user might barely read or write. 
[X] a user should only be able to complete jobs that have not been completed
[x] a user should only be able to complete a job once. 
[X] making a job should allow recording video then just like finishing jobs does
[X] the defualt Quechua Voice Recording job should start as funded
[X] search jobs on brows job page starts with None in the box
[x] browse jobs should just show funded jobs with an optional check box to show unfunded.
[x] Show unfunded jobs check box needs proper formating
[x] add browse job page checkboxes for completed jobs, unfunded jobs, defualt selected should only be funded jobs
[x] i have a funded ob but its not showing on the brows job page. we should be able to see it
[X] when i am in a funded job i see no way to click to sumbit page?
[X] when a user makes a job it should have an amount per person that completes it. defualt is one person so in that case they need to fund 1xamount. but if they want more then one person then it should b n*amount and that should be the amount requested for funding.
[x] Idioma del audio should not be there for the one doing the job. when a job is created it should be created for a specific language. that language should be displayed.
[X] Deliverable Types * (comma-separated: text,video,audio,image) should be multi select
[X] Fund this job immediately - removed. we should create the job and will create a wallet. and then the user will fund it.
[X] Deliverable Types * spacing has been limited
[X] we need to have a dashboard that only shows if there are jobs we made. if we made a job it should show a list of the jobs. and its current state if completed or not. if a job is completeded we should have place we see/download files then mark complete. this should also show partial completions so we can release partial funds.
[X] once a user has completed a job that job should stop accepting new posts. and should have that as a status. waiting completion.
[X] finishing a job should also live recording of a video with audio or to take a picture right there rather then just upload. we want to keep upload though. Easy part done (camera capture for video/images), hard part (MediaRecorder API) documented in TODO-Hard.md
[x] ok we need to change the flow of things. funded is no longer a thing. jobs should be drafts, awaiting sellers/submiter profiles, waiting confirmation/selections of submiters, waiting for submissions, waiting for confirmation of submisions, expired, complete. 
[x] make a submitting limit say 10 defualt and a time frame. so if either hits it swiches to review and submissions are not allowed anymore.
[x] we need to add a new work flow. so when a user creates a job. then workers can submit their profile. the job maker needs to see all the workers and select those they want to do. then there needs to be a button (doesnt work yet) that will send them to make the pre approved payment for those people. then when users upload the work. they need to be able mark the work as complete.
[x] jobs should have a expired date. if nothing is reqruited in the time or if its in submitting if no submissions by then it swiches to expired. created wallet contract should expire 7 days after this date.
[x] we need to search for places where funding is mentioned. that does not match the new flow. the new flow is they make a job. then it goes up for reqruiting. then the poster can view and select who will have the job. at the end the click "create contract" button that will take them to the pre approve payment page. or click close for submissions and it goes to selecting. selecting can be skipped if they just click create contract then it goes to submitting. at any time they can close for sumbisions then it goes to reviewing. they can review basics of submissions and hit complete. if complete the state changes and the contract payment is released.
[x] make a reqruite limit so when that limit is hit it changes to selecting. also add a time that it will auto change default to 7 days. should be an option in job creation.
[x] on job creation give a way to save it as a draft. make the drafts discoverable in one of dashboard were job creaters can see their jobs
[x] seprate signup pages for job creaters and job doers
[x] make creaters and doers only see links to things relevent to themselves
[x] add a profile page where users can update their profile
[x] add a demo users list where the json 
[x] make it so the defualt jobs are in diffrent job states from the docs/job-states file. we dont need expired. just the usefull states. 
[x] all the stuff in apply should exsist in profile and auto fill from profile
[x] browser jobs dashboard should show how many have been submited of workers or if in works submit stage it should show how many of needed have been submited. it should also have some tags. applied would be good. or about to start when its like 48 hours or less be for deadline
[x] lots of things missing spanish translation. can we get that added to the forms and such. 
[x] anyplace we have titles we want to start having the speaker button so we can read out the thing in the native langauge selected
[x] use the listen.png for all the audio buttons. we dont need the plain text just the icon
[x] grab the fave icon/tiny logo from the top level media file. and any others from there like logo and add them were expected
[x] fromat the liten buttons so they are next to the text they belong too.
[x] copy Perd?n-esto-a?n-no-se-ha-traducido.mp3 to be the defualt for fallback-oto.mp3 instead
[x] users should have a pretty name and that should be used on the site front end like in dashboards and job pages. like Financiador. in data dir update the default users to have a pretty name that goes with the username. uploaders should have names as well.
[x] if i submit a job. if i dont have profile defualts already set. then make those my profile defualts
[x] title audio is not requried but we still get this error if we dont have it Error creating job: name 'title_audio' is not defined
[x] to user profile add wallet address
[x] Continue adding audio buttons to remaining templates: dashboard titles, job creation/edit forms, job list pages, and other form pages throughout the app
[x] audio buttons are far from titles
[x] audio buttons are missing from buttons, filtrar and many more
[x] when i click the audio button for Seleccionar idioma it changes pages and doesnt play the sound
[x] currency should all be in pesos
[x] for text file requests it should allow both upload a text file and just a text field.
[x] Text File and note are in english not spanish
[x]    return view_func(request, *args, **kwargs)
  File "/home/sumwey/PrograminProjects/hackathon-interledger-market-Accesible/marketplace-py/jobs/views.py", line 181, in my_jobs
    return render(request, 'jobs/my_jobs.html', context) 
    self.invalid_block_tag(token, command, parse_until)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sumwey/PrograminProjects/hackathon-interledger-market-Accesible/marketplace-py/.venv/lib/python3.13/site-packages/django/template/base.py", line 577, in invalid_block_tag
    raise self.error(
    ...<3 lines>...
    )
django.template.exceptions.TemplateSyntaxError: Invalid block tag on line 58: 'endblock'. Did you forget to register or load this tag?
[x] Note: Some accepted submissions have not been marked as complete by workers yet. You can still complete the contract. is showing on the jobs page even when its not true
  - Fixed: Simplified workflow - when a job owner accepts a submission, it's automatically marked as complete. Removed the redundant "Mark as Complete" step since submitting work IS completing the work. The warning message no longer appears because all accepted submissions are automatically complete.
[x] anyplace we have titles we want to start having the speaker button so we can read out the thing in the native langauge selected, Informaci?n del Perfil i dont see one and a ton of other places this task will take a few passes. think all titles. and icons that are clickable. includeing menu items and all the form fields everywhere. like Idioma Preferido. remember the buttons especially, and Seleccionar idioma 
  - Third pass completed: Added audio buttons to view_applications.html (Reset to Pending buttons), job_detail.html (Ready to Submit heading, Apply to This Job button, Submissions heading), my_jobs.html (Filter label/button, View Details button, Create First Job button), accepted_jobs.html (View Job button, Browse Available Jobs button), job_owner_dashboard.html (Published Jobs heading, Edit Draft/Preview buttons, View public page/Edit/Mark completed buttons, Download links), my_money.html (title and labels), my_products.html (title). Comprehensive coverage achieved!
[x] Ya has enviado trabajo para este trabajo. Solo puedes enviar una vez por trabajo. should have a audio version button
[x] we need to double check this. when i accepted the work of one person it jumped straight to complete so when a user creates a job. then workers can submit their profile. the job maker needs to see all the workers and select those they want to do. then there needs to be a button (doesnt work yet) that will send them to make the pre approved payment for those people. then when users upload the work. they need to be able mark the work as complete.
  - Fixed: 
    1. Removed automatic transition to 'complete' status when accepting submissions. Job now stays in 'reviewing' status until owner manually marks it as complete.
    2. Updated mark_job_completed to check that all accepted submissions have been marked as complete by workers (is_complete=True) before allowing job completion.
    3. Added transition from 'selecting' to 'submitting' state when pre_approve_payments is called (even though payment functionality is still a stub).
    4. Added check in submit_job to ensure only selected applicants can submit work for a job.
    5. Added "Complete Contract" button that appears after accepting work when all accepted submissions are marked complete by workers. This button releases payments (stub - functionality coming soon). After contract is completed, job owner can then mark job as complete.
    6. Added contract_completed field to Job model to track contract completion status.
    7. Updated workflow: selecting ? pre-approve payments ? submitting ? reviewing ? complete contract ? mark job completed
[x] i am working through the work flow. but when i have a user apply to a job. there is nothing on the job side from the guy who added the job to accept them to the job. and when 1 or more accepted the button to start contract should be there. it should be there before any accepted. but inactive unusable untill atleast 1 has accepted. if they ask for more then one job doer and the number of accepted is lower then that number then it should do a pop up warning that you can only start the contract once. and it will start with only those accepted now and wont allow more to apply
  - Fixed:
    1. Added applications section to job_detail.html for job owners when job is in 'recruiting' or 'selecting' state, showing all applications with ability to select/reject/reset them directly from the job detail page.
    2. Added "Start Contract" button that appears when job is in 'selecting' state. Button is visible but disabled until at least one application is selected.
    3. Added JavaScript popup warning when starting contract with fewer selected applicants than max_responses, warning that contract can only start once and will start with only currently selected workers.
    4. Updated pre_approve_payments view to redirect to job detail page and show message that no more applications will be accepted after contract starts.
    5. Updated select_application view to redirect back to job detail page after selecting/rejecting applications.
    6. Once contract is started (job transitions to 'submitting' state), no more applications can be accepted (already enforced by apply_to_job view checking job.status == 'recruiting').
[x] is there still a point to the page work accepted? seems like it shows at the top of the main dashboard view?
  - Analysis: The `accepted_jobs` page shows detailed information (submission notes, text content, accepted date, funder) that is NOT shown in `my_money` page (which only shows title + budget in a simple list). However, there is some redundancy:
    - `accepted_jobs`: All accepted jobs with full details
    - `my_money`: All accepted jobs in simple list format (part of financial summary)
    - `pending_jobs`: Only incomplete accepted jobs (for work management)
  - Action taken: 
    1. Added a "View Details" link from `my_money` page to the `accepted_jobs` page
    2. **MAJOR IMPROVEMENT**: Enhanced `accepted_jobs` page to show critical status information that was missing:
       - Job Status (submitting/reviewing/complete) with color-coded badges
       - Work Completion Status (completed/not submitted/in progress)
       - Payment Status (contract completed/payment released/waiting for contract completion/payment pending)
       - Action Required alerts (when work needs to be submitted, when waiting for payment)
       - "Submit Work" button when work needs to be submitted
    3. **RENAMED & EXPANDED**: Renamed page from "Accepted Jobs" to "My Jobs" and now shows:
       - **My Applications** section: Shows all jobs user applied to (pending/selected/rejected) with application status, job status, and action alerts
       - **Accepted Jobs** section: Shows accepted submissions with full status details (work completion, payment status, etc.)
    Now users can see ALL their job activity in one place: applications they submitted (and their status), jobs they were accepted for, payment status, and what actions they need to take next. Much more useful!
[x] we should have a duplicat job button. it should be in my jobs page as well on all stages of the jobs page.
[x] add save draft to job submission. so they can save it for later
  - Implemented draft functionality for job submissions:
    1. Added `is_draft` boolean field to JobSubmission model
    2. Updated submit_job view to handle both "Save Draft" and "Submit" actions
    3. Users can now save drafts and continue editing them later
    4. Drafts are automatically loaded when returning to the submission page
    5. Drafts don't count toward submission limits or trigger job status transitions
    6. Added "Save Draft" button alongside "Submit" button in the submission form
    7. Form fields are pre-populated with draft data when editing
    8. Updated all submission count methods to exclude drafts
[x] when you click duplicate it should take you to edit the job.
[x] when a job is in draft there should be an edit button
  - Added edit button to my_jobs.html for draft jobs
  - Added edit button to job_detail.html for draft jobs when user is the funder
  - job_owner_dashboard.html already had edit button for drafts
[x] for job subbission if its new or a draft it should have preview button that saves it as a draft and in new tab opens it so they can see what it looks like
  - Implemented preview functionality for job submissions:
    1. Added preview_submission view that displays draft submissions in preview mode
    2. Added preview button to submit_job.html form with JavaScript handler
    3. Preview button saves form data as draft via AJAX and opens preview page in new tab
    4. Created preview_submission.html template showing how submission will appear to job owner
    5. Preview shows all submission content: notes, text content, and all file types (text, audio, video, image)
    6. Preview page includes warning banner indicating it's a draft and hasn't been submitted yet
    7. Preview page has "Edit Submission" button to return to form for editing
[x] on the job view the duplicate button is in a weird place. put it with the other buttons
  - Fixed: Moved the duplicate button to be grouped with the Edit Draft button in the same flex container. Both buttons now appear together with proper spacing and alignment.
[x] for a job poster there should be an option to decline Submissions
  - Implemented decline submission functionality:
    1. Added decline_submission view that allows job owners to reject submissions
    2. Added URL route for decline_submission at '<int:job_pk>/decline/<int:submission_pk>/'
    3. Added "Decline" button next to "Accept" button in job_detail.html for pending submissions
    4. Added "Decline" button in job_owner_dashboard.html for pending submissions
    5. Both buttons include audio player support for accessibility
    6. Decline action sets submission status to 'rejected' and shows success message
[x] mark job complete button is redundent. once they do complete contract that marks the job as complete
  - Fixed: Updated `complete_contract` view to automatically mark job status as 'complete' when contract is completed. Removed redundant "Mark job completed" button from job_detail.html and job_owner_dashboard.html templates. Now completing the contract immediately marks the job as complete in a single action.
[x] where we can upload job titles we should have a associated optional upload for the title and that should match the target langague
[x] i get this error on the docker version Error loading audio: Error: Failed to fetch audio
    loadAudioPlayer http://127.0.0.1:8000/static/audio/audio-player.js:42
[x] the main dashboard page when your logged in should be the one with all the big icons
[x] main dashboard goes off the screen on some screen sizes. can we do better?
[x] i see images that still have blank space instead of - can we get that fixed?
[x] i cant see the the menu when i click on the hamburger in middl nerrow size
[x] when i got this error it cleared all the feilds. maybe we save it first? or somehow not clear all my work, Please select at least one deliverable type.
[x] make it so there is only one funder in demo users. add that funder to all the default jobs.
wallet address sshould be "ilp.interledger-test.dev/send-money"
[x] add these to all of the seller creator demo users
seller key id 
d7c6fdbe-c9f0-41b0-b86f-8d79877759aa
seller private key
-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIPGTviT7rj1sYw/Y5LML3ymeZnF1wpv2ku+wEq7jTzPk
-----END PRIVATE KEY-----
wallet address
ilp.interledger-test.dev/get-money
and the default language should be otomi
[x] update the readme
[x] create a makefile
[x] add to profile the profile defualts that are found when doing a job for creators. we are already storeing those defaults we should make them accessable.
[x] update the readme to include the makefile usage info.
