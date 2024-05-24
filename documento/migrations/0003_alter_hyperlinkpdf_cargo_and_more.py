# Generated by Django 5.0.4 on 2024-05-17 17:34

import django.db.models.deletion
import documento.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documento', '0002_alter_hyperlinkpdf_empresa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hyperlinkpdf',
            name='cargo',
            field=models.ForeignKey(default=documento.models.default_cargo_id, null=True, on_delete=django.db.models.deletion.CASCADE, to='documento.cargo'),
        ),
        migrations.AlterField(
            model_name='hyperlinkpdf',
            name='colaborador',
            field=models.ForeignKey(default=documento.models.default_colaborador_id, null=True, on_delete=django.db.models.deletion.CASCADE, to='documento.colaborador'),
        ),
        migrations.AlterField(
            model_name='hyperlinkpdf',
            name='documento',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='documento.tipodocumento'),
        ),
        migrations.AlterField(
            model_name='hyperlinkpdf',
            name='regional',
            field=models.ForeignKey(default=documento.models.default_regional_id, null=True, on_delete=django.db.models.deletion.CASCADE, to='documento.regional'),
        ),
        migrations.AlterField(
            model_name='hyperlinkpdf',
            name='unidade',
            field=models.ForeignKey(default=documento.models.default_unidade_id, null=True, on_delete=django.db.models.deletion.CASCADE, to='documento.unidade'),
        ),
    ]
