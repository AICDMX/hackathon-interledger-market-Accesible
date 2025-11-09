from decimal import Decimal
from django.contrib import admin
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from .models import Job, JobSubmission, JobFunding, JobApplication


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'funder', 'target_language', 'status', 'budget', 'funded_amount', 'created_at']
    list_filter = ['status', 'target_language', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    # Note: Audio snippets and requests use GenericForeignKey, so they can't be used as standard inlines
    # Use the audio admin directly or create custom admin views if needed
    
    def save_model(self, request, obj, form, change):
        """
        Override save to handle manual funded_amount changes.
        When funded_amount is manually set in admin, create/update a JobFunding record
        so that get_funded_amount() returns the correct value.
        """
        if change:
            # Get the original object from database
            original_obj = Job.objects.get(pk=obj.pk)
            original_funded = original_obj.funded_amount
            new_funded = obj.funded_amount
            
            # If funded_amount was manually changed
            if original_funded != new_funded:
                # Save the object first
                super().save_model(request, obj, form, change)
                
                # Get existing funding total from JobFunding records
                existing_total = obj.get_funded_amount()
                
                # If the new funded_amount doesn't match what's in JobFunding records,
                # create/update an admin funding record to match
                if existing_total != new_funded:
                    # Get all existing funding records for this job from the owner
                    owner_fundings = JobFunding.objects.filter(job=obj, funder=obj.funder)
                    
                    # Calculate total from other funders (not the owner)
                    other_fundings_total = obj.fundings.exclude(funder=obj.funder).aggregate(
                        total=Sum('amount')
                    )['total'] or Decimal('0')
                    
                    # Calculate what the owner's funding should be
                    owner_funding_amount = new_funded - other_fundings_total
                    
                    # Ensure amount is not negative
                    if owner_funding_amount < Decimal('0'):
                        owner_funding_amount = Decimal('0')
                    
                    # Update or create owner funding record
                    if owner_fundings.exists():
                        if owner_funding_amount > Decimal('0'):
                            # Update the first owner funding record
                            owner_funding = owner_fundings.first()
                            owner_funding.amount = owner_funding_amount
                            owner_funding.note = 'Admin funding'
                            owner_funding.save()
                            # Delete any additional owner funding records
                            owner_fundings.exclude(pk=owner_funding.pk).delete()
                        else:
                            # If owner funding should be 0, delete all owner funding records
                            owner_fundings.delete()
                    else:
                        # Create a new owner funding record only if amount > 0
                        if owner_funding_amount > Decimal('0'):
                            JobFunding.objects.create(
                                job=obj,
                                funder=obj.funder,
                                amount=owner_funding_amount,
                                note='Admin funding'
                            )
                    
                    # Recalculate to sync everything
                    obj.refresh_funding_snapshot()
            else:
                # No change to funded_amount, save normally
                super().save_model(request, obj, form, change)
        else:
            # New object, save normally
            super().save_model(request, obj, form, change)


@admin.register(JobSubmission)
class JobSubmissionAdmin(admin.ModelAdmin):
    list_display = ['job', 'creator', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JobFunding)
class JobFundingAdmin(admin.ModelAdmin):
    list_display = ['job', 'funder', 'amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['job__title', 'funder__username']
    readonly_fields = ['created_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'applicant__username', 'profile_note']
    readonly_fields = ['created_at', 'updated_at']
