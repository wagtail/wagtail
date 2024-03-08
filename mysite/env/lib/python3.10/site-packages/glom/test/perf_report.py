"""
slow gloms that came up organically, used as performance metrics
"""
import time
import gc

import attr

from glom import glom, T



STR_SPEC = [{
    'id': ('id', str),
    'name': 'short_name',
    'external_id': 'external_id',
    'created_date': 'created_date',
}]


T_SPEC = [{
    'id': (T.id, str),
    'name': T.short_name,
    'external_id': T.external_id,
    'created_date': T.created_date,
}]


def func(data):
    return [{
            'id': str(t.id),
            'name': t.short_name,
            'external_id': t.external_id,
            'created_date': t.created_date
        } for t in data]


def setup_list_of_dict(num=100):
    """
    a common use case is list-of-dicts object processing
    to prepare internal objects for JSON serialization
    """
    Obj = attr.make_class(
        'Obj', ['id', 'short_name', 'external_id', 'created_date'])

    data = [
        Obj(i, 'name' + str(i), 'external' + str(i), 'now') for i in range(num)]

    return data


def run(spec, data):
    start = time.time()
    glom(data, spec)
    end = time.time()
    print("{} us per object".format((end - start) / len(data) * 1e6))


def ratio(spec, func, data):
    glom_dur = []
    py_dur = []
    for i in range(10):
        t1 = time.perf_counter_ns()
        glom(data, spec)
        t2 = time.perf_counter_ns()
        func(data)
        t3 = time.perf_counter_ns()
        glom_dur.append(t2 - t1)
        py_dur.append(t3 - t2)

    glom_avg = sum(sorted(glom_dur)[2:-2])
    py_avg = sum(sorted(py_dur)[2:-2])

    return 1.0 * glom_avg / py_avg


if __name__ == "__main__":
    import cProfile
    data = setup_list_of_dict(100000)
    run(STR_SPEC, data)
    run(STR_SPEC, data)
    print(ratio(STR_SPEC, func, setup_list_of_dict(1000)))
    print(ratio(STR_SPEC, func, setup_list_of_dict(1000)))


# suggest using scalene to profile with:
# $ scalene glom/test/perf_report.py --profile-all --reduced-profile --cpu-only --outfile SCALENE-CPU.txt
