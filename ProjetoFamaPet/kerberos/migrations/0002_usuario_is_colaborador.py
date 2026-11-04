from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kerberos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="is_colaborador",
            field=models.BooleanField(default=False, verbose_name="Colaborador"),
        ),
    ]