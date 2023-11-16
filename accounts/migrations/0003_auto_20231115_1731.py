# Generated by Django 3.1.14 on 2023-11-15 08:31

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20200513_2031'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='age',
            field=models.IntegerField(choices=[(1, '10代'), (2, '20代'), (3, '30代'), (4, '40代'), (5, '50代'), (6, '60代'), (7, '70代以上')], default=1, verbose_name='年齢'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='gender',
            field=models.IntegerField(choices=[(0, '男性'), (1, '女性'), (2, 'その他')], default=0, verbose_name='性別'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, verbose_name='ユーザーID'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='zipCode',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='郵便番号'),
        ),
    ]
