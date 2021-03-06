#!/usr/bin/env Python

import datetime
from decimal import Decimal
import warnings

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from agate import Table
from agate.data_types import *
from agate.computations import *
from agate.exceptions import *
from agate.warns import NullCalculationWarning

class TestTableComputation(unittest.TestCase):
    def setUp(self):
        self.rows = (
            ('a', 2, 3, 4),
            (None, 3, 5, None),
            ('a', 2, 4, None),
            ('b', 3, 4, None)
        )

        self.number_type = Number()
        self.text_type = Text()

        self.columns = (
            ('one', self.text_type),
            ('two', self.number_type),
            ('three', self.number_type),
            ('four', self.number_type)
        )

        self.table = Table(self.rows, self.columns)

    def test_change(self):
        new_table = self.table.compute([
            (Change('two', 'three'), 'test')
        ])

        self.assertIsNot(new_table, self.table)
        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        self.assertSequenceEqual(new_table.rows[0], ('a', Decimal('2'), Decimal('3'), Decimal('4'), Decimal('1')))
        self.assertEqual(new_table.columns['test'][0], Decimal('1'))
        self.assertEqual(new_table.columns['test'][1], Decimal('2'))
        self.assertEqual(new_table.columns['test'][2], Decimal('2'))
        self.assertEqual(new_table.columns['test'][3], Decimal('1'))

    def test_change_mixed_types(self):
        rows = (
            ('1', '10/24/1978'),
            ('2', '11/13/1974')
        )

        columns = (
            ('number', Number()),
            ('date', Date())
        )

        table = Table(rows, columns)

        with self.assertRaises(ValueError):
            table.compute([
                (Change('number', 'date'), 'test')
            ])

    def test_changed_invalid_types(self):
        rows = (
            (False, True),
            (True, False)
        )

        columns = (
            ('before', Boolean()),
            ('after', Boolean())
        )

        table = Table(rows, columns)

        with self.assertRaises(DataTypeError):
            table.compute([
                (Change('before', 'after'), 'test')
            ])

    def test_change_nulls(self):
        warnings.simplefilter('error')

        with self.assertRaises(NullCalculationWarning):
            new_table = self.table.compute([
                (Change('three', 'four'), 'test')
            ])

        with self.assertRaises(NullCalculationWarning):
            new_table = self.table.compute([
                (Change('four', 'three'), 'test')
            ])

        warnings.simplefilter('ignore')

        new_table = self.table.compute([
            (Change('three', 'four'), 'test')
        ])

        self.assertIsNot(new_table, self.table)
        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        self.assertSequenceEqual(new_table.rows[0], ('a', Decimal('2'), Decimal('3'), Decimal('4'), Decimal('1')))
        self.assertEqual(new_table.columns['test'][0], Decimal('1'))
        self.assertEqual(new_table.columns['test'][1], None)
        self.assertEqual(new_table.columns['test'][2], None)
        self.assertEqual(new_table.columns['test'][3], None)

    def test_percent_change(self):
        new_table = self.table.compute([
            (PercentChange('two', 'three'), 'test')
        ])

        self.assertIsNot(new_table, self.table)
        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        to_one_place = lambda d: d.quantize(Decimal('0.1'))

        self.assertSequenceEqual(new_table.rows[0], ('a', Decimal('2'), Decimal('3'), Decimal('4'), Decimal('50.0')))
        self.assertEqual(to_one_place(new_table.columns['test'][0]), Decimal('50.0'))
        self.assertEqual(to_one_place(new_table.columns['test'][1]), Decimal('66.7'))
        self.assertEqual(to_one_place(new_table.columns['test'][2]), Decimal('100.0'))
        self.assertEqual(to_one_place(new_table.columns['test'][3]), Decimal('33.3'))

    def test_percent_change_invalid_columns(self):
        with self.assertRaises(DataTypeError):
            new_table = self.table.compute([
                (PercentChange('one', 'three'), 'test')
            ])

    def test_rank_number(self):
        new_table = self.table.compute([
            (Rank('two'), 'rank')
        ])

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)
        self.assertSequenceEqual(new_table.columns['rank'], (1, 3, 1, 3))

    def test_rank_number_reverse(self):
        new_table = self.table.compute([
            (Rank('two', reverse=True), 'rank')
        ])

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)
        self.assertSequenceEqual(new_table.columns['rank'], (3, 1, 3, 1))

    def test_rank_number_key(self):
        new_table = self.table.compute([
            (Rank('two', comparer=lambda x,y: int(y - x)), 'rank')
        ])

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)
        self.assertSequenceEqual(new_table.columns['rank'], (3, 1, 3, 1))

    def test_rank_number_reverse_key(self):
        new_table = self.table.compute([
            (Rank('two', comparer=lambda x,y: int(y - x), reverse=True), 'rank')
        ])

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)
        self.assertSequenceEqual(new_table.columns['rank'], (1, 3, 1, 3))

    def test_rank_text(self):
        new_table = self.table.compute([
            (Rank('one'), 'rank')
        ])

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)
        self.assertSequenceEqual(new_table.columns['rank'], (1, 4, 1, 3))

    def test_percentile_rank(self):
        rows = [(n,) for n in range(1, 1001)]

        table = Table(rows, (('ints', self.number_type),))
        new_table = table.compute([
            (PercentileRank('ints'), 'percentiles')
        ])

        self.assertEqual(len(new_table.rows), 1000)
        self.assertEqual(len(new_table.columns), 2)

        self.assertSequenceEqual(new_table.rows[0], (1, 0))
        self.assertSequenceEqual(new_table.rows[50], (51, 5))
        self.assertSequenceEqual(new_table.rows[499], (500, 49))
        self.assertSequenceEqual(new_table.rows[500], (501, 50))
        self.assertSequenceEqual(new_table.rows[998], (999, 99))
        self.assertSequenceEqual(new_table.rows[999], (1000, 100))

class TestDateAndTimeComputations(unittest.TestCase):
    def test_change_dates(self):
        rows = (
            ('10/4/2015', '10/7/2015'),
            ('10/2/2015', '9/28/2015'),
            ('9/28/2015', '9/1/2015')
        )

        date_type = Date()

        columns = (
            ('one', date_type),
            ('two', date_type)
        )

        table = Table(rows, columns)

        new_table = table.compute([
            (Change('one', 'two'), 'test')
        ])

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 3)

        self.assertSequenceEqual(new_table.rows[0], (
            datetime.date(2015, 10, 4),
            datetime.date(2015, 10, 7),
            datetime.timedelta(days=3)
        ))

        self.assertEqual(new_table.columns['test'][0], datetime.timedelta(days=3))
        self.assertEqual(new_table.columns['test'][1], datetime.timedelta(days=-4))
        self.assertEqual(new_table.columns['test'][2], datetime.timedelta(days=-27))

    def test_change_datetimes(self):
        rows = (
            ('10/4/2015 4:43', '10/7/2015 4:50'),
            ('10/2/2015 12 PM', '9/28/2015 12 PM'),
            ('9/28/2015 12:00:00', '9/1/2015 6 PM')
        )

        datetime_type = DateTime()

        columns = (
            ('one', datetime_type),
            ('two', datetime_type)
        )

        table = Table(rows, columns)

        new_table = table.compute([
            (Change('one', 'two'), 'test')
        ])

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 3)

        self.assertSequenceEqual(new_table.rows[0], (
            datetime.datetime(2015, 10, 4, 4, 43),
            datetime.datetime(2015, 10, 7, 4, 50),
            datetime.timedelta(days=3, minutes=7)
        ))

        self.assertEqual(new_table.columns['test'][0], datetime.timedelta(days=3, minutes=7))
        self.assertEqual(new_table.columns['test'][1], datetime.timedelta(days=-4))
        self.assertEqual(new_table.columns['test'][2], datetime.timedelta(days=-26, hours=-18))

    def test_change_timedeltas(self):
        rows = (
            ('4:15', '8:18'),
            ('4h 2m', '2h'),
            ('4 weeks', '27 days')
        )

        timedelta_type = TimeDelta()

        columns = (
            ('one', timedelta_type),
            ('two', timedelta_type)
        )

        table = Table(rows, columns)

        new_table = table.compute([
            (Change('one', 'two'), 'test')
        ])

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 3)

        self.assertSequenceEqual(new_table.rows[0], (
            datetime.timedelta(minutes=4, seconds=15),
            datetime.timedelta(minutes=8, seconds=18),
            datetime.timedelta(minutes=4, seconds=3)
        ))
        self.assertEqual(new_table.columns['test'][0], datetime.timedelta(minutes=4, seconds=3))
        self.assertEqual(new_table.columns['test'][1], datetime.timedelta(hours=-2, minutes=-2))
        self.assertEqual(new_table.columns['test'][2], datetime.timedelta(days=-1))
