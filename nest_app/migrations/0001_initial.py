# Generated by Django 3.2 on 2022-01-15 22:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('mass_g', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.order')),
            ],
        ),
        migrations.CreateModel(
            name='ShippedItem',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.product')),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.shipment')),
            ],
        ),
        migrations.CreateModel(
            name='ProductInventory',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.product')),
            ],
        ),
        migrations.CreateModel(
            name='OrderedItem',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(default=1)),
                ('shipped_quantity', models.IntegerField(default=0)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='nest_app.product')),
            ],
        ),
    ]
