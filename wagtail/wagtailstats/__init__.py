import redis
import datetime


def _today(now=datetime.datetime.now()):
    year, month, day = now.timetuple()[0:3]
    return '{0}-{1}-{2}'.format(year, month, day)


def _daysToNow(x, now=datetime.datetime.today()):
    # returns last x days in yyyy-mm-dd format
    days_list = []
    for x in range(0, x):
        past_date = now-datetime.timedelta(days=x)
        year, month, day = past_date.timetuple()[0:3]
        days_list.append('{0}-{1}-{2}'.format(year, month, day))
    return days_list


class Metric(object):
    def __init__(self):
        try:
            # Use Celery's redis connection details, if available
            # e.g. settings.BROKER_URL = 'redis://127.0.0.1:6379'
            from django.conf import settings
            from django.core.exceptions import ImproperlyConfigured
            self.r = redis.from_url(settings.BROKER_URL)
        except (ImportError, AttributeError, ImproperlyConfigured):
            self.r = redis.Redis()

    def record(self, metric, value):
        # something happened today
        # e.g. record('request', 44)
        return self.r.zincrby('{0}:{1}'.format(metric, _today()), value)

    def report(self, metric, limit, range='day'):
        # return ranked results for specified span, with scores
        # metrics.report('request', 5)
        if range == 'day':
            key = '{0}:{1}'.format(metric, _today())
            return self.r.zrevrange(key, 0, limit, withscores=True)
        elif range == 'week':
            keys = []
            union_key = '{0}:{1}:week'.format(metric, _today())
            for date in _daysToNow(7):
                key = '{0}:{1}'.format(metric, date)
                keys.append(key)
            self.r.zunionstore(union_key, keys)
            week_report = self.r.zrevrange(union_key, 0, limit, withscores=True)
            self.r.delete(union_key)  # TODO: consider caching
            return week_report
        elif range == 'month':
            keys = []
            union_key = '{0}:{1}:month'.format(metric, _today())
            for date in _daysToNow(31):
                key = '{0}:{1}'.format(metric, date)
                keys.append(key)
            self.r.zunionstore(union_key, keys)
            month_report = self.r.zrevrange(union_key, 0, limit, withscores=True)
            self.r.delete(union_key)  # TODO: consider caching
            return month_report
        else:
            raise NotImplementedError('range must be day, week or month')

    def score(self, metric, value, range='day'):
        # return score for value of metric over range
        if range == 'day':
            key = '{0}:{1}'.format(metric, _today())
            return self.r.zscore(key, value)
        elif range == 'week':
            score = 0
            for date in _daysToNow(7):
                key = '{0}:{1}'.format(metric, date)
                score += self.r.zscore(key, value) or 0
            return score
        elif range == 'month':
            score = 0
            for date in _daysToNow(31):
                key = '{0}:{1}'.format(metric, date)
                score += self.r.zscore(key, value) or 0
            return score
        else:
            raise NotImplementedError('range must be day, week or month')
