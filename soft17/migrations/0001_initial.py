# Generated by Django 4.1.6 on 2023-04-18 02:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suit', models.CharField(choices=[('SPADE', 'Spade'), ('CLUB', 'Club'), ('DIAMOND', 'Diamond'), ('HEART', 'Heart')], default='SPADE', max_length=10)),
                ('rank', models.CharField(choices=[('A', 'Ace'), ('2', 'Two'), ('3', 'Three'), ('4', 'Four'), ('5', 'Five'), ('6', 'Six'), ('7', 'Seven'), ('8', 'Eight'), ('9', 'Nine'), ('10', 'Ten'), ('J', 'Jack'), ('Q', 'Queen'), ('K', 'King')], default='A', max_length=10)),
                ('value', models.IntegerField(default=1)),
                ('url', models.CharField(default='none', max_length=200)),
            ],
            options={
                'ordering': ('hand_order__hand_position',),
            },
        ),
        migrations.CreateModel(
            name='Dealer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False)),
                ('curr_state', models.IntegerField(choices=[(0, 'Reset Game'), (1, 'Start Game'), (2, 'Place Bet'), (3, 'Deal Players'), (4, 'Deal Dealer'), (5, 'Player Turn'), (6, 'Dealer Turn'), (7, 'Compute Scores')], default=1)),
                ('num_players', models.IntegerField(default=1)),
                ('created', models.DateTimeField(blank=True, default=None, null=True)),
                ('completed', models.DateTimeField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GameRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='None', max_length=200)),
                ('balance', models.IntegerField(default=1000)),
                ('is_multiplayer', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Hand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_cards', models.IntegerField(default=0)),
                ('hand_value', models.IntegerField(default=0)),
                ('is_dealer_hand', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_picture', models.FileField(blank=True, upload_to='')),
                ('content_type', models.CharField(default='None', max_length=50)),
                ('wallet_balance', models.IntegerField(default=1)),
                ('multiplayer_room', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='multiplayer_room', to='soft17.gameroom')),
                ('profile_user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('single_player_room', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='single_player_room', to='soft17.gameroom')),
            ],
        ),
        migrations.CreateModel(
            name='Hand_Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hand_position', models.IntegerField(default=1)),
                ('card', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hand_order', to='soft17.card')),
                ('hand', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hand_order', to='soft17.hand')),
            ],
            options={
                'ordering': ('hand_position',),
            },
        ),
        migrations.AddField(
            model_name='hand',
            name='cards',
            field=models.ManyToManyField(through='soft17.Hand_Order', to='soft17.card'),
        ),
        migrations.AddField(
            model_name='hand',
            name='dealer',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='dealer_hand', to='soft17.dealer'),
        ),
        migrations.AddField(
            model_name='hand',
            name='game',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='game', to='soft17.game'),
        ),
        migrations.AddField(
            model_name='hand',
            name='player',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='player_hand', to='soft17.profile'),
        ),
        migrations.AddField(
            model_name='game',
            name='game_room',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='room', to='soft17.gameroom'),
        ),
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_cards', models.ManyToManyField(blank=True, null=True, related_name='assigned_cards_to_deck', to='soft17.card')),
                ('dealer', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='soft17.dealer')),
                ('remaining_cards', models.ManyToManyField(blank=True, null=True, related_name='remaining_cards_in_deck', to='soft17.card')),
            ],
        ),
        migrations.AddField(
            model_name='dealer',
            name='game_room',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='game_room', to='soft17.gameroom'),
        ),
        migrations.CreateModel(
            name='Bet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_chips_5', models.IntegerField(default=0)),
                ('num_chips_10', models.IntegerField(default=0)),
                ('num_chips_25', models.IntegerField(default=0)),
                ('num_chips_50', models.IntegerField(default=0)),
                ('num_chips_100', models.IntegerField(default=0)),
                ('bet_order', models.CharField(default='', max_length=200)),
                ('game', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='game_bet', to='soft17.game')),
                ('player', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='player_bet', to='soft17.profile')),
            ],
        ),
    ]
