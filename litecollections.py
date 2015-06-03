import collections
import logging
import re
import sqlite3
import sys

logger = logging.getLogger(__file__)

def _slices_to_where_statement(slices):
    conditions = []
    values = []
    for slice_ in slices:
        if slice_.step is not None:
            raise ValueError("Invalid selector {!r}. Slices used must not "
                             "provide a step.".format(slice_))
        if slice_.start is None and slice_.stop is None: # full copy
            return ('', []) # No where statement (get all)
        elif slice_.start is None:
            conditions.append("key < ?")
            values.append(slice_.stop)
        elif slice_.stop is None:
            conditions.append("key >= ?")
            values.append(slice_.start)
        else:
            conditions.append("(? <= key AND key < ?)")
            values.append(slice_.start)
            values.append(slice_.stop)

    statement = 'WHERE ' + ' OR '.join(conditions)
    return (statement, values)

class SetAndDictBase(object):
    def __len__(self):
        result = self.execute('SELECT COUNT(*) FROM data')
        (row,) = result
        (length,) = row
        return length

    def __iter__(self):
        for row in self.execute(
                'SELECT key FROM data ORDER BY key'):
            (item,) = row
            yield item

    def __contains__(self, item):
        result = self.execute(
            'SELECT COUNT(*) FROM data WHERE key=?', [item])
        (row,) = result
        (match,) = row
        return bool(match)

    def execute(self, query, params=[]):
        logger.debug('Executing {}, {}'.format(query, params))
        try:
            with self.connection as c:
                return c.execute(query, params)
        except sqlite3.InterfaceError as e:
            msg = e[0]
            match = re.match(
                '^Error binding parameter (\d+) - probably unsupported type.$',
                msg)
            if match is None:
                raise # pragma: no cover

            index = int(match.group(1))
            raise TypeError('Invalid value: {!r}'.format(params[index]))
            
    def __delitem__(self, key):
        # Handle slicing
        if isinstance(key, slice):
            key = (key,)

        if isinstance(key, tuple):
            where_statement, values = _slices_to_where_statement(key)
            query = "DELETE FROM data {}".format(
                where_statement)
    
            return type(self)(self.execute(query, values))

        # Handle individual item deleting
        self.execute("DELETE FROM data WHERE key=?", [key])

    def close(self):
        self.connection.close()

class SortedSet(SetAndDictBase, collections.MutableSet):
    def __init__(self, iterable=(), database=':memory:'):
        self.connection = sqlite3.connect(database)
        self.database = database
        with self.connection as c:
            c.execute('CREATE TABLE IF NOT EXISTS data (key DYNAMIC UNIQUE)')
            c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx ON data (key)')
        for item in iterable:
            self.add(item)

    def __repr__(self):
        opening = '{}({}'.format(type(self).__name__, list(self))
        if self.database == ':memory:':
            return '{})'.format(opening)
        else:
            return '{}, {!r})'.format(opening, self.database)

    def add(self, item):
        self.execute('INSERT OR IGNORE INTO data(key) VALUES (?)', [item])

    def discard(self, item):
        self.execute('DELETE FROM data WHERE key=?', [item])

    def __getitem__(self, slices):
        if isinstance(slices, slice):
            slices = (slices,)

        where_statement, values = _slices_to_where_statement(slices)
        query = "SELECT key from data {} ORDER BY key".format(where_statement)
   
        return type(self)(k for (k,) in self.execute(query, values))

class SortedDict(SetAndDictBase, collections.MutableMapping):
    def __init__(self, items=(), database=':memory:'):
        self.connection = sqlite3.connect(database)
        self.database = database
        with self.connection as c:
            c.execute('CREATE TABLE IF NOT EXISTS '
                      'data (key DYNAMIC UNIQUE, value DYNAMIC)')
            c.execute('CREATE UNIQUE INDEX IF NOT EXISTS '
                      'idx ON data (key)')
        for k, v in items:
            self[k] = v

    def __getitem__(self, key):
        # Handle slicing
        if isinstance(key, slice):
            key = (key,)

        if isinstance(key, tuple):
            where_statement, values = _slices_to_where_statement(key)
            query = "SELECT key,value from data {} ORDER BY key".format(
                where_statement)
    
            return type(self)(self.execute(query, values))

        # Handle individual item getting
        result = self.execute(
            "SELECT value FROM data WHERE key=?", [key])
        try:
            (row,) = result
        except ValueError as e:
            if '0 values' not in e[0]: # Make sure it's the ValueError we
                                       # expect (for no rows)
                raise # pragma: no cover
            return self.__missing__(key)
        else:
            (value,) = row
            return value

    def __missing__(self, key):
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.execute(
            "INSERT OR REPLACE INTO data (key,value) VALUES (?,?)",
            [key, value])

    def items(self):
        return ItemsView(self)

    def keys(self):
        return KeysView(self)

    def values(self):
        return ValuesView(self)

    def __repr__(self):
        opening = '{}({}'.format(type(self).__name__, list(self.items()))
        if self.database == ':memory:':
            return '{})'.format(opening)
        else:
            return '{}, {!r})'.format(opening, self.database)

class ViewMixin(object):
    def __init__(self, sorted_dict):
        self.sorted_dict = sorted_dict

    def __repr__(self):
        '{}({})'.format(type(self).__name__, self.sorted_dict)

class ItemsView(ViewMixin, collections.ItemsView):
    def __iter__(self):
        for row in self.sorted_dict.connection.execute(
                'SELECT key, value FROM data ORDER BY key'):
            yield row

    def __contains__(self, pair):
        result = self.sorted_dict.execute(
            'SELECT COUNT(*) FROM data WHERE key=? AND value=?', pair)
        ((count,),) = result
        return bool(result)

class KeysView(ViewMixin, collections.KeysView):
    def __iter__(self):
        return iter(self.sorted_dict)

    def __contains__(self, key):
        return key in self.sorted_dict

class ValuesView(ViewMixin, collections.ValuesView):
    def __iter__(self):
        for row in self.sorted_dict.execute(
                'SELECT value FROM data ORDER BY key'):
            (value,) = row
            yield value

    def __contains__(self, value):
        result = self.sorted_dict.execute(
            'SELECT COUNT(*) FROM data WHERE value=?', [value])
        ((count,),) = result
        return bool(count)
