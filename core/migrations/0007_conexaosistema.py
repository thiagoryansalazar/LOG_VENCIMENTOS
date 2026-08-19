import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_conexaoerp"),
    ]

    operations = [
        migrations.RenameModel(old_name="ConexaoERP", new_name="ConexaoSistema"),
        migrations.AlterModelOptions(
            name="conexaosistema",
            options={
                "ordering": ["criado_em", "id"],
                "verbose_name": "Conexao de sistema",
                "verbose_name_plural": "Conexoes de sistemas",
            },
        ),
        migrations.AddField(
            model_name="conexaosistema",
            name="criado_em",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # A tabela era usada como singleton (get_or_create(id=1)), o que insere
        # com PK explicita sem avancar a sequence do Postgres. Sem este ajuste,
        # o primeiro INSERT feito pelo ORM (sem id explicito) colide com o
        # id=1 ja existente.
        migrations.RunSQL(
            sql="""
            SELECT setval(
                pg_get_serial_sequence('core_conexaosistema', 'id'),
                COALESCE((SELECT MAX(id) FROM core_conexaosistema), 1),
                (SELECT MAX(id) IS NOT NULL FROM core_conexaosistema)
            );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
