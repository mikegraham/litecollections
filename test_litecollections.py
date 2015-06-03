from litecollections import SortedSet, SortedDict

import os
import tempfile
import unittest

class SortedSetTest(unittest.TestCase):
    def test_dedupe(self):
        ss = SortedSet([1, 2, 2])
        self.assertEqual(len(ss), 2)
        self.assertEqual(ss, SortedSet([1, 2]))

    def test_equal(self):
        self.assertEqual(SortedSet(), SortedSet())
        self.assertEqual(SortedSet(), set())
        self.assertEqual(SortedSet([1, 2]), SortedSet([1, 2]))
        ss = SortedSet(['foo', 'bar'])
        self.assertEqual(ss, ss)
        self.assertEqual(ss, set(ss))

    def test_add(self):
        ss = SortedSet(['foo', 'bar'])
        self.assertEqual(len(ss), 2)
        ss.add('foo')
        self.assertEqual(len(ss), 2)
        ss.add('baz')
        self.assertEqual(len(ss), 3)
        self.assertEqual(ss, {'bar', 'foo', 'baz'})

        with self.assertRaises(TypeError):
            ss.add([])

    def test_discard(self):
        ss = SortedSet(['foo', 'bar'])
        self.assertEqual(len(ss), 2)
        ss.discard('baz')
        self.assertEqual(len(ss), 2)
        ss.discard('foo')
        self.assertEqual(len(ss), 1)
        self.assertEqual(ss, {'bar'})

    def test_del(self):
        ss = SortedSet(['foo', 'bar'])
        self.assertEqual(len(ss), 2)
        del ss['bar']
        self.assertEqual(ss, {'foo'})

        ss = SortedSet([1, 2, 3, 4, 5])
        del ss[2:4]
        self.assertEqual(ss, {1, 4, 5})

    def test_slice(self):
        ss = SortedSet([1, 2, 3, 4, 5])
        self.assertEqual(ss[2:4], {2, 3})
        self.assertEqual(ss[5:], {5})
        self.assertEqual(ss[:2, 5:], {1, 5})
        self.assertEqual(ss[5:10, :2], {1, 5})
        self.assertEqual(ss[:], ss)
        self.assertEqual(ss[:, 1:2], ss)
        with self.assertRaises(ValueError):
            ss[1:5:2]

    def test_repr(self):
        ss = SortedSet([2, 1])
        self.assertEquals(repr(ss), 'SortedSet([1, 2])')

        (_, filename) = tempfile.mkstemp()
        try:
            s = SortedSet([1], filename)
            self.assertRegexpMatches(
                repr(s),
                r"SortedSet\(\[1\], '.+'\)")
        finally:
            os.remove(filename)

    def test_database_file(self):
        (_, filename) = tempfile.mkstemp()
        try:
            s1 = SortedSet([44, 55, 66], filename)
            s1.close()
            s2 = SortedSet(database=filename)
            self.assertEquals(s2, {44, 55, 66})
        finally:
            os.remove(filename)
        
class SortedDictTest(unittest.TestCase):
    def test_getitem(self):
        d = SortedDict([(1, 'foo'), (2, 'bar')])
        self.assertEqual(d[1], 'foo')
        with self.assertRaises(KeyError):
            d[10]
        with self.assertRaises(TypeError):
            d[[]]

    def test_setitem(self):
        d = SortedDict()
        d['foo'] = 'bar'
        d['foo'] = 'bar'
        d['foo'] = 'bar'
        self.assertEqual(d, {'foo': 'bar'})
        self.assertEqual(len(d), 1)

    def test_slices(self):
        d = SortedDict()
        
        d['foo1'] = "x"
        d['foo2'] = "y"
        d['foo3'] = "z"

        self.assertEqual(d['foo1':], {'foo1': 'x', 'foo2': 'y', 'foo3': 'z'})
        self.assertEqual(d['foo2':], {'foo2': 'y', 'foo3': 'z'})
        self.assertEqual(d['foo1':'foo3'], {'foo1': 'x', 'foo2': 'y'})

    def test_contains(self):
        d = SortedDict([(3, 4), (1, 9)])
        self.assertIn(1, d)
        self.assertNotIn(4, d)
        with self.assertRaises(TypeError):
            (1, 2) in d

    def test_keys(self):
        d = SortedDict([(3, 4), (1, 9)])

        self.assertIn(1, d.keys())
        self.assertNotIn(4, d.keys())
        with self.assertRaises(TypeError):
            (1, 2) in d.keys()

        self.assertEqual(list(d.keys()), [1, 3])

    def test_values(self):
        d = SortedDict([(3, 4), (1, 9)])

        self.assertIn(4, d.values())
        self.assertNotIn(1, d.values())
        with self.assertRaises(TypeError):
            (1, 2) in d.values()

        self.assertEqual(list(d.values()), [9, 4])

    def test_items(self):
        d = SortedDict([(3, 4), (1, 9)])
        self.assertIn((1, 2), d.items())
        self.assertEqual(list(d.items()), [(1, 9), (3, 4)])

    def test_repr(self):
        d = SortedDict([(3, 4), (1, 9)])
        self.assertEqual(repr(d), 'SortedDict([(1, 9), (3, 4)])')

        (_, filename) = tempfile.mkstemp()
        try:
            s = SortedDict([(1, 2)], filename)
            self.assertRegexpMatches(
                repr(s),
                r"SortedDict\(\[\(1, 2\)\], '.+'\)")
        finally:
            os.remove(filename)

    def test_database_file(self):
        (_, filename) = tempfile.mkstemp()
        try:
            d1 = SortedDict([('foo', 'bar'), ('baz', 'qux')], filename)
            d1.close()
            d2 = SortedDict(database=filename)
            self.assertEquals(d2, {'foo': 'bar', 'baz': 'qux'})
        finally:
            os.remove(filename)

if __name__ == '__main__':
    unittest.main()
