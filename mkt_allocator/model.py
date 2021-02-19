import os
import pathlib
import csv
import atexit
from collections import defaultdict

class Database:
    def __init__(self):
        self.db = dict()
        
    def get(self, key):
        return self.db.get(key, set())

    def add(self, key, value):
        current = self.get(key)
        if type(value) in [list]:
            current.update(value)
        else:
            current.update([value])
        return self.db.update({key: current})

    def __len__(self):
        return len(self.db)
        
def split_by_n(seq:str, n:int):
    """
    A generator to divide a sequence into chunks of n units.
    """
    while seq:
        yield seq[:n]
        seq = seq[n:]

class DocumentList:
    def __init__(self, docdir):
        docpath = pathlib.Path(docdir)
        if not os.path.exists(docpath):
            raise FileNotFoundError('Doc Dir not found.')
        
        all_docs = []
        all_docs.extend(self._walk_files(docpath))
        self.items = all_docs
        self.index = 0

    def __iter__(self):
        yield self.items
    
    def __next__(self):
        try:
            item = self.items[self.index]
        except IndexError:
            raise StopIteration()
        self.index += 1
        return item
    
    def __len__(self):
        return len(self.items)
        
    def _walk_files(self, path):
        docs = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            docs.extend(filenames)
            break
        return docs
        

class Datafile:
    def __init__(self, datapath):
        path_obj = pathlib.Path(datapath)
        if not os.path.exists(path_obj):
            raise FileNotFoundError('Datafile not found.')
        self.path = path_obj
        self.fh = open(self.path, 'r')
        self._header = self._read_header()
        atexit.register(self.cleanup)

    @property
    def header(self):
        if len(self._header) > 0:
            return self._header

    def rewind(self, pos=0):
        self.fh.seek(pos)

    def _read_header(self):
        self.fh.seek(0)
        csv_file = csv.reader(self.fh)
        header = next(csv_file)
        self.fh.seek(0)
        return header

    def cleanup(self):
        if self.fh:
            try:
                self.fh.close()
            except Exception:
                pass
    
                    
class GroupedDatafile(Datafile):
    def __init__(self, datapath, column):
        super().__init__(datapath)
        self.rows = {}
        self._readfile(column)

    def __getitem__(self, key):
        return self.rows[key]

    def __iter__(self):
        return iter(self.rows)

    def keys(self):
        return self.rows.keys()

    def items(self):
        return self.rows.items()

    def values(self):
        return self.rows.values()

    def _readfile(self, column):
        items = dict()
        with open(self.path, 'r') as f:
            csv_file = csv.reader(f)
            # skip header
            _ = next(csv_file)
            i = self.header.index(column)

            # group rows by column value e.g. Zipcode
            for row in csv_file:
                if row[i] not in items:
                    items[row[i]] = []
                items[row[i]].append(row)
            
            self.rows = items
        