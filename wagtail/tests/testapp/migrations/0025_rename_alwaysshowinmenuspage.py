from django.db.migrations import Migration as BaseMigration, RenameModel


class Migration(BaseMigration):
    dependencies = [('tests', '0024_tableblockstreampage')]

    operations = [RenameModel('AlwaysShowInMenusPage', 'NeverShowInMenusPage')]
