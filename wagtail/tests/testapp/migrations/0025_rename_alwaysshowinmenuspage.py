from django.db.migrations import Migration as BaseMigration, RenameModel


class Migration(BaseMigration):
    atomic = False

    dependencies = [('tests', '0024_tableblockstreampage')]

    operations = [RenameModel('AlwaysShowInMenusPage', 'NeverShowInMenusPage')]
