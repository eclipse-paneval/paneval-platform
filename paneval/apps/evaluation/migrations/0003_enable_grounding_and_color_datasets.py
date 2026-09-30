from django.db import migrations


# Suite membership comes from the source multimodal catalog. Config paths use
# the paneval runner layout, and display names also identify saved results.
SUITES = [
    ('视觉定位', [
        ('RefCOCO', 'paneval/tasks/refcoco/refcoco_val.py'),
        ('RefCOCOg', 'paneval/tasks/refcoco/refcoco_g_val.py'),
        ('RefCOCO+', 'paneval/tasks/refcoco/refcoco_plus_val.py'),
        ('arpgrounding_priority_val', 'paneval/tasks/arpgrounding/arpgrounding_priority_val.py'),
        ('arpgrounding_attribute_val', 'paneval/tasks/arpgrounding/arpgrounding_attribute_val.py'),
        ('arpgrounding_relation_val', 'paneval/tasks/arpgrounding/arpgrounding_relation_val.py'),
    ]),
    ('色彩理解', [
        ('color_bench_test', 'paneval/tasks/color_bench/color_bench_test.py'),
    ]),
]


def enable_datasets(apps, schema_editor):
    CvData = apps.get_model('evaluation', 'CvData')
    MmDataset = apps.get_model('evaluation', 'MmDataset')
    database = schema_editor.connection.alias

    for suite_name, datasets in SUITES:
        suite, _ = CvData.objects.using(database).update_or_create(
            name=suite_name,
            parent_name='',
            defaults={'meta_data': '{"data": []}', 'deleted_at': None},
        )
        for name, config_path in datasets:
            MmDataset.objects.using(database).update_or_create(
                cv_id=suite.pk,
                name=name,
                lbx=0,
                defaults={
                    'data': {
                        'name': suite_name,
                        'dataset': config_path,
                        'is_admin': 0,
                        'description': '非榜单任务',
                        'dataset_show': name,
                    },
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ('evaluation', '0002_auto_20260609_1108'),
    ]

    operations = [
        migrations.RunPython(enable_datasets),
    ]
