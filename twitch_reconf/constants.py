import os 
from twitch_reconf.utils import abs_path_for_file
from twitch_reconf.utils import dir_name
from twitch_reconf.utils import get_cwd
from twitch_reconf.utils import path_join
from twitch_reconf.utils import user_dir

DS_BASE = 'base'
DS_SQL = 'sql'

DATASOURCE_TYPES = [
    DS_BASE,
    DS_SQL,
]

COMP_BASE = 'base'

COMPOSITION_TYPES = [
    COMP_BASE,
]

REDACT = '<REDACT>'
ENCODING = 'cp1252'

COST_RSE = 2
COST_ARC = 3
COST_HEX = 8
COST_O365 = 12

PACKAGE_ROOT = dir_name(abs_path_for_file(__file__))
PROJECT_ROOT = abs_path_for_file(path_join(PACKAGE_ROOT, os.pardir))

USER_HOME_DIR = path_join(user_dir(), '.twreconf')
CACHE_DIR = path_join(USER_HOME_DIR, 'cache')
SCRATCH_DIR = path_join(USER_HOME_DIR, 'scratch')
TEST_DATA_DIR = path_join(USER_HOME_DIR, 'test_data')
DEFAULT_SUPPORT_DIR = path_join(PROJECT_ROOT, 'support_files')
LOG_LOCATION = path_join(USER_HOME_DIR, 'twreconf.log')

CONF_FILENAME = 'twreconf.conf'
CONF_SEARCH_PATHS = [USER_HOME_DIR, get_cwd(), '/etc', DEFAULT_SUPPORT_DIR]
DEFAULT_CONF_DIRS = [
    path_join(path, CONF_FILENAME) for path in CONF_SEARCH_PATHS]

