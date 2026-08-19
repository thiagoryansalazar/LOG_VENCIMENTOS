from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_eventooperacional"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConexaoERP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_sistema", models.CharField(blank=True, max_length=100)),
                ("api_url_encrypted", models.TextField(blank=True)),
                ("webhook_url_encrypted", models.TextField(blank=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Conexao ERP",
                "verbose_name_plural": "Conexoes ERP",
            },
        ),
    ]
