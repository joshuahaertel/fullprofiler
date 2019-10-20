from time import sleep
from unittest import TestCase

from fullprofiler.profiler import Profiler


class TestProfiler(TestCase):
    def test_all(self):
        Profiler.enable()
        self.do_something()
        Profiler.disable()
        Profiler.print_statistics()

    def do_something(self):
        self.do_sleep()
        self.do_something_else()

    @staticmethod
    def do_sleep():
        sleep(.3)

    @staticmethod
    def do_something_else():
        for _ in range(100):
            pass
