##### Database #####
TEST_COLLECTION_NAME = 'tests'
WRITTEN_TEST_COLLECTION_NAME = 'written-tests'
USER_COLLECTION_NAME = 'users'
GROUP_COLLECTION_NAME = 'groups'

##### Runtime file storage #####
RUNTIME_FOLDER = 'assets/runtime'

# folders inside RUNTIME_FOLDER
TESTS_FOLDERNAME = 'tests'
WRITTEN_TESTS_FOLDERNAME = 'results'

##### Excel formatting #####
HEADING_FORMAT = {
        'bold': True,
        'font_size': 11,
        }

CENTERED_HEADING_FORMAT = {
        **HEADING_FORMAT,
        'align': 'center',
        }

RIGHT_BORDERED_FORMAT = {
        'right': 1
        }

BOTTOM_BORDERED_FORMAT = {
        'bottom': 1
        }

COLUMN_BG_COLORED_FORMAT = {
        'pattern': 2,
        'bg_color': 'orange',
        }

ROW_BG_COLORED_FORMAT = {
        'pattern': 4,
        'bg_color': 'gold',
        }

WRAPPED_FORMAT = {
        'text_wrap': True
        }
DEFAULT_FONT_SIZE = 10
DEFAULT_FONT_NAME = 'Arial'
