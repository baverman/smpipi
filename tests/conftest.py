import sys
import time
import logging
import subprocess
logging.basicConfig(level=logging.DEBUG)

import pytest


@pytest.fixture(scope='session')
def smsc(request):
    p = subprocess.Popen([sys.executable, '-m', 'smpipi.tornado', '30001'])
    time.sleep(3)
    request.addfinalizer(p.kill)
