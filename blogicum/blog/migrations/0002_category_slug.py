# Generated by Django 3.2.16 on 2024-06-30 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(default=0, help_text='Идентификатор страницы для URL; разрешены символы латиницыб цифры, дефис и подчёркивание.', unique=True, verbose_name='Идентификатор'),
            preserve_default=False,
        ),
    ]