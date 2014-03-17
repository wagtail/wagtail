import unittest
from wagtail.wagtailstats import _daysToNow, _today, Metric


class MetricsTests(unittest.TestCase):

    def setUp(self):
        m = Metric()
        for key in m.r.keys("test:request"):
            m.r.delete(key)

    def testDateFormat(self):
        valentines = datetime.datetime(2014, 2, 14)
        self.failUnless(_today(valentines) == '2014-2-14')

    def testDaysToNow(self):
        valentines = datetime.datetime(2014, 2, 14)
        out = _daysToNow(2, now=valentines)
        self.failUnless(out == ['2014-2-14', '2014-2-13'])

    def testOneRecord(self):
        out = m.record('test:request', 1)
        self.failUnless(out == 1)

    def testMultiRecord(self):
        m.record('test:request', 1)
        out = m.record('test:request', 1)
        self.failUnless(out == 2)

    def testSingleRecordAndScore(self):
        m.record('test:request', 'foo')
        out = m.score('test:request', 'foo')
        self.failUnless(out == 1)

    def testMultiRecordAndScore(self):
        m.record('test:request', 'foo')
        m.record('test:request', 'foo')
        out = score('test:request', 'foo')
        self.failUnless(out == 2)

    def testMultiRecordAndMonthlyScore(self):
        m.record('test:request', 'foo')
        m.record('test:request', 'foo')
        out = m.score('test:request', 'foo', range='month')
        self.failUnless(out == 2)

    def testSingleRecordAndReport(self):
        m.record('test:request', 'foo')
        out = m.report('test:request', 1)
        self.failUnless(out == [('foo', 1)])

    def testMultiRecordAndReport(self):
        m.record('test:request', 'foo')
        m.record('test:request', 'foo')
        m.record('test:request', 'foo2')
        out = m.report('test:request', 2)
        self.failUnless(out == [('foo', 2), ('foo2', 1)])

    def testMultiRecordAndWeeklyReport(self):
        m.record('test:request', 'foo')
        m.record('test:request', 'foo')
        m.record('test:request', 'foo2')
        out = m.report('test:request', 2, range='week')
        self.failUnless(out == [('foo', 2), ('foo2', 1)])

    def testAnnualReportFails(self):
        self.assertRaises(NotImplementedError, m.report, 'a', 1, range='year')

    def testAnnualScoreFails(self):
        self.assertRaises(NotImplementedError, m.score, 'a', 'b', range='year')

    def tearDown(self):
        for key in m.r.keys("test:request:*"):
            m.r.delete(key)

if __name__ == '__main__':
    unittest.main()
