from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        """Configure la connexion SQLite avec WAL mode pour de meilleures performances."""
        from django.db.backends.signals import connection_created

        def _set_sqlite_pragmas(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                with connection.cursor() as cursor:
                    cursor.execute('PRAGMA journal_mode=WAL;')
                    cursor.execute('PRAGMA synchronous=NORMAL;')
                    cursor.execute('PRAGMA cache_size=-10000;')   # ~10 MB cache
                    cursor.execute('PRAGMA temp_store=MEMORY;')
                    cursor.execute('PRAGMA mmap_size=268435456;')  # 256 MB mmap

        connection_created.connect(_set_sqlite_pragmas)
