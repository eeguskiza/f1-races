from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0002_newspost_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='grandprix',
            name='result_sainz_pos',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='prediction',
            name='sainz_pos_guess',
            field=models.IntegerField(default=0),
        ),
    ]
