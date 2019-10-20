ABSOLUTE_MIN = float('-inf')
ABSOLUTE_MAX = float('inf')


class Statistic:
    def __init__(self):
        self.count = 0
        self.total_time = 0
        self.min = ABSOLUTE_MAX
        self.max = ABSOLUTE_MIN

    @property
    def mean(self):
        if not self.count:
            return 0
        return self.total_time / self.count

    def add_run_time(self, run_time):
        self.count += 1
        self.total_time += run_time
        self.min = min(run_time, self.min)
        self.max = max(run_time, self.max)
