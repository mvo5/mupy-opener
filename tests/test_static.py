#!/usr/bin/python3

import os
import os.path
import subprocess
import unittest


class TestStatic(unittest.TestCase):
    def setUp(self):
        self.prj_path = os.path.join(os.path.dirname(__file__), "..")

    def test_flake8(self):
        subprocess.check_call(
            ["flake8", "--ignore=E402", "--exclude=./lib", self.prj_path]
        )

    def test_black_clean(self):
        subprocess.check_call(["black", "--check", self.prj_path])
