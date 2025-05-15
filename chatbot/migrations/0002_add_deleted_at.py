from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ] 