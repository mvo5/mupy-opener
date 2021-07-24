import os
import shutil
import tempfile
import unittest


class BaseTest(unittest.TestCase):
    def setUp(self):
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)
        self.addCleanup(shutil.rmtree, self.tmpdir)

    def add_cleanup(self, *args, **kwargs):
        self.addCleanup(*args, **kwargs)
