import os
import pathlib
import csv
import copy
import atexit
from collections import defaultdict
from itertools import chain
      
def split_by_n(seq:str, n:int):
    """
    A generator to divide a sequence into chunks of n units.
    """
    while seq:
        yield seq[:n]
        seq = seq[n:]

class Document:
    """ A bucket representing data to be assigned

    buffer: Dict<str, list>   Data to be written to a file
    expectations: Set  (set of criteria document expects to receive data from)
    """
    def __init__(self, label):
        self.label = label
        self.buffer = dict()
        self.expectations = set()

    def expect(self, criteria):
        self.expectations.add(criteria)

    def is_expecting(self, criteria):
        return criteria in self.expectations

    def cancel(self, criteria):
        """ remove element from set if exists, no key error """
        self.expectations.discard(criteria)

    def add(self, key, value):
        if key not in self.buffer:
            self.buffer[key] = list()

        self.buffer[key].append(value)
        
    def get(self, key):
        return self.buffer.get(key, list())

    def update(self, key):
        return self.buffer.update(key)

    def save_buffer(self, outdir, storage, header=None):
        path = os.path.join(outdir, f"{self.label}.csv")
        with open(path, 'w') as f:
            w = storage(f)
            if header:
                w.writerow(header)
                
            for values in self.buffer.values():
                w.writerows(values)
        ret = copy.copy(self.buffer)
        self.buffer.clear()
        return ret

    @property
    def buffer_length(self):
        return sum(len(v) for v in self.buffer.values())

    def __iter__(self):
        yield self

    def __str__(self):
        return self.label

    def __cmp__(self, other):
        """ This is apparently slower than using lambda function"""
        return cmp(self.buffer_length, other.buffer_length)

class DocumentList:
    def __init__(self, docdir):
        docpath = pathlib.Path(docdir)
        if not os.path.exists(docpath):
            raise FileNotFoundError('Doc Dir not found.')
        
        self.members = dict()
        for doc in self._walk_files(docpath):
            key = doc.label
            self.members[key] = doc

    def save(self, outdir):
        for member in self.members:
            member.save(outdir, csv)

    def get_documents_expecting(self, criteria):
        """ Returns a sorted list of documents expecting 
        to be allocated `criteria`. """
        items = [m for m in self.members.values() if m.is_expecting(criteria)]
        return sorted(items, key=lambda x: x.buffer_length, reverse=True)
        
    def labels(self):
        return self.keys()

    def keys(self):
        return self.members.keys()

    def items(self):
        return self.members.items()

    def values(self):
        return self.members.values()

    def __iter__(self):
        return iter(self.members)
    
    def __getitem__(self, name):
        return self.members[name]
    
    def __len__(self):
        return len(self.members)
        
    def _walk_files(self, path):
        docs = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            docs.extend(map(Document, filenames))
            break
        return docs

class Datafile:
    def __init__(self, datapath):
        path_obj = pathlib.Path(datapath)
        if not os.path.exists(path_obj):
            raise FileNotFoundError('Datafile not found.')
        self.path = path_obj
        atexit.register(self.cleanup)
        self.fh = open(self.path, 'r')
        self._header = self._read_header()

    def contents(self, reader):
        """ Returns an iterator """
        self.rewind()
        contents = reader(self.fh)
        _ = next(contents)
        return contents

    @property
    def header(self):
        if len(self._header) > 0:
            return self._header
        else:
            return list()

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
    

def allocate(datafile, doc_list, column):
    """ 
    Fill Strategies:
    - Equal:  share equally between documents for a given criteria
    """
    i = datafile.header.index(column)
    reader = csv.reader
    contents = datafile.contents(reader)
    nobody = Document('nobody')

    for row in contents:
        value = row[i] # e.g. 15601
        try:
            doc = doc_list.get_documents_expecting(value)[-1]
            doc.add(value, row)
        except IndexError:
            nobody.add(value, row)

    print("Note: allocated %s items to %s." % (nobody.buffer_length, nobody.label))
    return nobody

