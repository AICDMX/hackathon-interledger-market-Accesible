from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_job_funded_amount_job_is_funded_job_payment_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobFunding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, help_text='Amount pledged in ILP tokens', max_digits=10, verbose_name='Amount')),
                ('note', models.CharField(blank=True, help_text='Optional note for context (shown on job page)', max_length=255, verbose_name='Note')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('funder', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='job_fundings', to=settings.AUTH_USER_MODEL, verbose_name='Funder')),
                ('job', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='fundings', to='jobs.job', verbose_name='Job')),
            ],
            options={
                'verbose_name': 'Job Funding',
                'verbose_name_plural': 'Job Fundings',
                'ordering': ['-created_at'],
            },
        ),
    ]
