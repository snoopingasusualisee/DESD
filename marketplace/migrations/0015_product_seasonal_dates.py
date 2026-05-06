# Generated migration for seasonal date fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0014_product_seasonal_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='seasonal_start_date',
            field=models.DateField(blank=True, help_text='Start of seasonal availability (e.g., June 1 for summer produce)', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='seasonal_end_date',
            field=models.DateField(blank=True, help_text='End of seasonal availability (e.g., August 31 for summer produce)', null=True),
        ),
    ]
