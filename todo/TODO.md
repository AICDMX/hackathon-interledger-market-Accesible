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