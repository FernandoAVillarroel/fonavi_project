from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0008_alter_nivelbasico_nivel'),
    ]

    operations = [
        # No hace nada en la base, solo marca que estamos al día.
        migrations.RunSQL(
            sql="SELECT 1",
            reverse_sql="SELECT 1",
        ),
    ]
