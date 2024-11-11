# Generated by Django 5.0.3 on 2024-08-30 11:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credits', models.IntegerField(default=0)),
                ('description', models.TextField(default='Hello, this is my description!', max_length=500)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='abilityhub.chat')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='abilityhub.person')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('image', models.ImageField(upload_to='images/')),
                ('is_private', models.BooleanField(default=False)),
                ('uploader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='abilityhub.person')),
            ],
        ),
        migrations.CreateModel(
            name='Deposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.CharField(max_length=50)),
                ('added_credits', models.IntegerField()),
                ('depositor_credits_after', models.IntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('depositor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deposits', to='abilityhub.person')),
            ],
        ),
        migrations.AddField(
            model_name='chat',
            name='participants',
            field=models.ManyToManyField(related_name='chats', to='abilityhub.person'),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_credits_after', models.IntegerField()),
                ('receiver_credits_after', models.IntegerField()),
                ('sent_credits', models.IntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('receiver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_transactions', to='abilityhub.person')),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_transactions', to='abilityhub.person')),
            ],
        ),
    ]