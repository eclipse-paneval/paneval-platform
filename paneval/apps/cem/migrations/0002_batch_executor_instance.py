from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cem', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='executor_instance',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
