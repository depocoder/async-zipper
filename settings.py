import os

DEBUG_MODE = os.environ.get('DEBUG', 'True').casefold().strip() == 'true'

MEDIA_DIR = os.getenv('MEDIA_DIR', 'test_photos')

DEFAULT_BYTES_FOR_READ = 2**10 if DEBUG_MODE else -1

INTERVAL_SECS = int(os.getenv('INTERVAL_SECS', '0'))
