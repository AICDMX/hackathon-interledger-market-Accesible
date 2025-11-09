#Todo file
## instructions
Pick any job not in progress or done only those empty []
Before doing anything. Immediately claim it. claim a job check box with a [P] for in progress.
mark [C] for user to check the work and wait.
[X] when it is done.
if no jobs then just stop and let the user know

if wallet work is needed make sure to add it todo-wallet.md cause the wallet part is not implimented. so we just leave buttons and add a task there. 
you can break things up into more tasks in this file. but only do one task at a time. so first mark it p for in progress then create a new job with [] but dont do it. just stop at the part your doing and leave that for later. 

## jobs
[C] anyplace we have titles we want to start having the speaker button so we can read out the thing in the native langauge selected, Información del Perfil i dont see one and a ton of other places this task will take a few passes. think all titles. and icons that are clickable. includeing menu items and all the form fields everywhere. like Idioma Preferido. remember the buttons especially, and Seleccionar idioma 
  - Third pass completed: Added audio buttons to view_applications.html (Reset to Pending buttons), job_detail.html (Ready to Submit heading, Apply to This Job button, Submissions heading), my_jobs.html (Filter label/button, View Details button, Create First Job button), accepted_jobs.html (View Job button, Browse Available Jobs button), job_owner_dashboard.html (Published Jobs heading, Edit Draft/Preview buttons, View public page/Edit/Mark completed buttons, Download links), my_money.html (title and labels), my_products.html (title). Comprehensive coverage achieved!
[X] Continue adding audio buttons to remaining templates: dashboard titles, job creation/edit forms, job list pages, and other form pages throughout the app 
[X] audio buttons are far from titles
[X] audio buttons are missing from buttons, filtrar and many more
[X] when i click the audio button for Seleccionar idioma it changes pages and doesnt play the sound
[X] currency should all be in pesos
[P] where we can upload job titles we should have a associated optional upload for the title and that should match the target langague
[X] for text file requests it should allow both upload a text file and just a text field.
[X] Text File and note are in english not spanish
[C] Ya has enviado trabajo para este trabajo. Solo puedes enviar una vez por trabajo. should have a audio version button
[X]    return view_func(request, *args, **kwargs)
  File "/home/sumwey/PrograminProjects/hackathon-interledger-market-Accesible/marketplace-py/jobs/views.py", line 181, in my_jobs
    return render(request, 'jobs/my_jobs.html', context) 
    self.invalid_block_tag(token, command, parse_until)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sumwey/PrograminProjects/hackathon-interledger-market-Accesible/marketplace-py/.venv/lib/python3.13/site-packages/django/template/base.py", line 577, in invalid_block_tag
    raise self.error(
    ...<3 lines>...
    )
django.template.exceptions.TemplateSyntaxError: Invalid block tag on line 58: 'endblock'. Did you forget to register or load this tag?
[C] we need to double check this. when i accepted the work of one person it jumped straight to complete so when a user creates a job. then workers can submit their profile. the job maker needs to see all the workers and select those they want to do. then there needs to be a button (doesnt work yet) that will send them to make the pre approved payment for those people. then when users upload the work. they need to be able mark the work as complete.
  - Fixed: 
    1. Removed automatic transition to 'complete' status when accepting submissions. Job now stays in 'reviewing' status until owner manually marks it as complete.
    2. Updated mark_job_completed to check that all accepted submissions have been marked as complete by workers (is_complete=True) before allowing job completion.
    3. Added transition from 'selecting' to 'submitting' state when pre_approve_payments is called (even though payment functionality is still a stub).
    4. Added check in submit_job to ensure only selected applicants can submit work for a job.
    5. Added "Complete Contract" button that appears after accepting work when all accepted submissions are marked complete by workers. This button releases payments (stub - functionality coming soon). After contract is completed, job owner can then mark job as complete.
    6. Added contract_completed field to Job model to track contract completion status.
    7. Updated workflow: selecting → pre-approve payments → submitting → reviewing → complete contract → mark job completed
[C] i am working through the work flow. but when i have a user apply to a job. there is nothing on the job side from the guy who added the job to accept them to the job. and when 1 or more accepted the button to start contract should be there. it should be there before any accepted. but inactive unusable untill atleast 1 has accepted. if they ask for more then one job doer and the number of accepted is lower then that number then it should do a pop up warning that you can only start the contract once. and it will start with only those accepted now and wont allow more to apply
  - Fixed:
    1. Added applications section to job_detail.html for job owners when job is in 'recruiting' or 'selecting' state, showing all applications with ability to select/reject/reset them directly from the job detail page.
    2. Added "Start Contract" button that appears when job is in 'selecting' state. Button is visible but disabled until at least one application is selected.
    3. Added JavaScript popup warning when starting contract with fewer selected applicants than max_responses, warning that contract can only start once and will start with only currently selected workers.
    4. Updated pre_approve_payments view to redirect to job detail page and show message that no more applications will be accepted after contract starts.
    5. Updated select_application view to redirect back to job detail page after selecting/rejecting applications.
    6. Once contract is started (job transitions to 'submitting' state), no more applications can be accepted (already enforced by apply_to_job view checking job.status == 'recruiting').
[x] to user profile add wallet address
  - Added wallet_address field to User model as TextField (multi-line text box)
  - Added wallet_address to ProfileForm with Textarea widget (3 rows)
  - Added wallet_address field to profile template with audio button support
  - Created migration 0005_user_wallet_address.py
[C] is there still a point to the page work accepted? seems like it shows at the top of the main dashboard view?
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
[C] we should have a duplicat job button. it should be in my jobs page as well on all stages of the jobs page. 
[X] Note: Some accepted submissions have not been marked as complete by workers yet. You can still complete the contract. is showing on the jobs page even when its not true
  - Fixed: Simplified workflow - when a job owner accepts a submission, it's automatically marked as complete. Removed the redundant "Mark as Complete" step since submitting work IS completing the work. The warning message no longer appears because all accepted submissions are automatically complete.
[P] add save draft to job submission. so they can save it for later