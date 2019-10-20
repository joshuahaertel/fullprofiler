import sys
from collections import defaultdict
from time import time

from fullprofiler.statistic import Statistic


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
        cls.frame_to_start_time[frame] = time()

    @classmethod
    def _end_callable_profile(cls, frame, _):
        end_time = time()
        start_time = cls.frame_to_start_time.get(frame)
        if not start_time:
            return
        del cls.frame_to_start_time[frame]
        total_time = end_time - start_time
        callable_statistic = cls.statistics[
            (frame.f_code, None)]  # type: Statistic
        callable_statistic.add_run_time(total_time)

    @classmethod
    def _start_c_callable_profile(cls, frame, c_func):
        cls.c_frame_to_start_time[(frame, c_func)] = time()

    @classmethod
    def _end_c_callable_profile(cls, frame, c_func):
        end_time = time()
        start_time = cls.c_frame_to_start_time.get((frame, c_func))
        if not start_time:
            return
        del cls.c_frame_to_start_time[(frame, c_func)]
        total_time = end_time - start_time
        callable_statistic = cls.statistics[
            (frame.f_code, c_func)]  # type: Statistic
        callable_statistic.add_run_time(total_time)

    @staticmethod
    def disable():
        if sys.getprofile() != Profiler._handle_profile_event:
            raise RuntimeError('Attempting to disable another profiler!')
        sys.setprofile(None)
        Profiler.frame_to_start_time.clear()

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
        for _, _, statistic, (code, c_func) in statistic_list:
            if c_func:
                code_args = (
                    'builtin: {}'.format(c_func.__module__),
                    '?',
                    c_func.__qualname__
                )
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
