from __future__ import absolute_import, unicode_literals

import time
import tracemalloc


class Benchmark:
    repeat = 10

    def test(self):
        timings = []
        memory_usage = []
        tracemalloc.start()

        for i in range(self.repeat):
            before_memory = tracemalloc.take_snapshot()
            start_time = time.time()

            self.bench()

            end_time = time.time()
            after_memory = tracemalloc.take_snapshot()
            timings.append(end_time - start_time)
            memory_usage.append(
                sum(
                    [t.size for t in after_memory.compare_to(before_memory, "filename")]
                )
            )

        print(  # noqa
            "time min:",
            min(timings),
            "max:",
            max(timings),
            "avg:",
            sum(timings) / len(timings),
        )  # NOQA
        print(  # noqa
            "memory min:",
            min(memory_usage),
            "max:",
            max(memory_usage),
            "avg:",
            sum(memory_usage) / len(memory_usage),
        )  # NOQA
