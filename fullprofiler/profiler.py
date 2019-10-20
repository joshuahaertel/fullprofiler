import asyncio
import inspect
import sys
from collections import defaultdict
from time import time

from fullprofiler.statistic import Statistic


class ProxyCFunc:
    def __init__(self, c_func):
        self.c_func = c_func

    def __eq__(self, other):
        try:
            return (
                    self.c_func == other or
                    self.c_func == other.c_func
            )
        except:
            return False

    def __hash__(self):
        try:
            return hash(self.c_func)
        except TypeError:
            return hash(self.c_func.__qualname__)

    def get_args(self):
        return (
            self.c_func.__module__ or '?',
            '?',
            self.c_func.__qualname__,
        )


class Profiler:
    frame_to_start_time = {}
    c_frame_to_start_time = {}
    statistics = defaultdict(Statistic)

    @staticmethod
    def enable():
        if sys.getprofile():
            raise RuntimeError('Another profiler is currently running!')
        sys.setprofile(Profiler._handle_profile_event)

    @staticmethod
    def _handle_profile_event(frame, event, arg):
        actions = {
            'call': Profiler._start_callable_profile,
            'return': Profiler._end_callable_profile,
            'c_call': Profiler._start_c_callable_profile,
            'c_return': Profiler._end_c_callable_profile,
            'c_exception': Profiler._end_c_callable_profile,
        }
        actions[event](frame, arg)

    @classmethod
    def _start_callable_profile(cls, frame, _):
        # Potential way to avoid issues when a function returns a future
        # bool(frame.f_code.co_flags & inspect.CO_COROUTINE)

        cls.frame_to_start_time[frame] = time()

    @classmethod
    def _end_callable_profile(cls, frame, return_value):
        end_time = time()
        value = cls.frame_to_start_time.get(frame)
        if not value:
            return

        start_time = value

        if (return_value
                and asyncio.isfuture(return_value)
                and not hasattr(return_value, 'real_start_time')):
            return_value.real_start_time = start_time
            return_value.frame = frame
            return_value.add_done_callback(Profiler._fix_coroutines)
            del cls.frame_to_start_time[frame]
            return

        del cls.frame_to_start_time[frame]
        cls._update_statistics(end_time, frame, start_time)

    @staticmethod
    def _fix_coroutines(future):
        print('here')
        end_time = time()
        Profiler._update_statistics(
            end_time, future.frame, future.real_start_time
        )

    @classmethod
    def _update_statistics(cls, end_time, frame, start_time):
        total_time = end_time - start_time
        callable_statistic = cls.statistics[
            (frame.f_code, None)]  # type: Statistic
        callable_statistic.add_run_time(total_time)


    @classmethod
    def _start_c_callable_profile(cls, frame, _):
        cls.c_frame_to_start_time[frame] = time()

    @classmethod
    def _end_c_callable_profile(cls, frame, c_func):
        end_time = time()
        start_time = cls.c_frame_to_start_time.get(frame)
        if not start_time:
            return
        del cls.c_frame_to_start_time[frame]
        total_time = end_time - start_time
        callable_statistic = cls.statistics[
            (frame.f_code, ProxyCFunc(c_func))]  # type: Statistic
        callable_statistic.add_run_time(total_time)

    @staticmethod
    def disable():
        if sys.getprofile() != Profiler._handle_profile_event:
            raise RuntimeError('Attempting to disable another profiler!')
        sys.setprofile(None)
        Profiler.frame_to_start_time.clear()
        Profiler.c_frame_to_start_time.clear()

    @staticmethod
    def print_statistics(sort_key='mean', sort_order='descending'):
        statistic_list = [
            (getattr(statistic, sort_key), index, statistic, (code, c_func))
            for index, ((code, c_func), statistic) in
            enumerate(Profiler.statistics.items())
        ]

        reverse = True if sort_order == 'descending' else False
        statistic_list.sort(reverse=reverse)

        print(
            'filename | first line | name | count | total time | min | mean '
            '| max '
        )
        for _, _, statistic, (code, proxy_c_func) in statistic_list:
            if proxy_c_func:
                code_args = proxy_c_func.get_args()
            else:
                code_args = (
                    code.co_filename,
                    code.co_firstlineno,
                    code.co_name
                )
            print(
                '{: ^} | {: ^} | {: ^} | {: ^} | {: ^} | {: ^} | {: ^} |'
                ' {: ^}'.format(
                    *code_args,
                    statistic.count, statistic.total_time, statistic.min,
                    statistic.mean, statistic.max,
                ))
