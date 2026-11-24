"""Restore only the already-shipped dev schema baseline; never print a DSN."""
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from brain_api.config import Settings
from sqlalchemy.engine import make_url

root = Path('/app/brain')
url = make_url(Settings.from_env().database_url).set(
    drivername='postgresql+psycopg', database='brain'
)
os.environ['BRAIN_DATABASE_URL'] = url.render_as_string(hide_password=False)
config = Config(str(root / 'engine/migrations/alembic.ini'))
config.set_main_option('script_location', str(root / 'engine/migrations'))
command.upgrade(config, '0015')
print('dev baseline restored using existing migrations through 0015')
