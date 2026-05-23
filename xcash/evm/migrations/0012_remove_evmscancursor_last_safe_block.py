from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("evm", "0011_evmbroadcasttask_base_task_required"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="evmscancursor",
            name="last_safe_block",
        ),
    ]
