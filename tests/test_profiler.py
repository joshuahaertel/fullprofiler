import asyncio
from time import sleep
from unittest import TestCase

from fullprofiler.profiler import Profiler


class TestProfiler(TestCase):
    def setUp(self):
        Profiler.statistics.clear()

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


class TestAsyncioProfile(TestCase):
    def setUp(self):
        Profiler.statistics.clear()

    def test_all(self):
        Profiler.statistics.clear()
        loop = asyncio.get_event_loop()
        Profiler.enable()
        loop.run_until_complete(self.do_something())
        Profiler.disable()
        print('\n\nNew Test\n\n')
        Profiler.print_statistics()

    async def do_something(self):
        await self.do_sleep()
        await self.do_something_else()

    @staticmethod
    async def do_sleep():
        await asyncio.sleep(.3)

    @staticmethod
    async def do_something_else():
        for _ in range(100):
            pass
