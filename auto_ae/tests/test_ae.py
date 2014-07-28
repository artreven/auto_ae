'''
Use with Nosetests (https://nose.readthedocs.org/en/latest/)

Created on Jun 7, 2013

@author: artreven
'''
import os
import shutil
import itertools

import fca

import auto_ae.ae

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r)
                                         for r in range(len(s)+1))

def has_att(obj, att):
    return int(obj) % int(att) == 0

def ce_finder(imp, wait):
    for i in range(1000):
        if (all(i % j == 0 for j in imp.premise) and
            any(i % j != 0 for j in imp.conclusion)):
                return (i, '')
    else:
        return (None, 'No such number under 1000')
    
def prover(imp):
    if any(reduce(lambda x, y: x*y, num_seq, 1)
           for num_seq in powerset(imp.premise)):
        return True
    else:
        return False

class Test:
    def setUp(self):
        objects = [5, 12, 48]
        attributes = [2, 3, 8]
        table = [[0, 0, 0],
                 [1, 1, 0],
                 [1, 1, 1]]
        self.cxt = fca.Context(table, objects, attributes)
        self.ae = auto_ae.ae.AE(os.getcwd() + '/ae_test', self.cxt, has_att, ce_finder)

    def tearDown(self):
        shutil.rmtree(self.ae.dest)
        
    def test_basis_computation_and_reset(self):
        assert not hasattr(self.ae, '_basis')
        self.ae.basis
        assert self.ae._basis
        self.ae._reset()
        assert not hasattr(self.ae, '_basis')
        
    def test_run(self):
        self.ae.run(1, 1)
        assert len(self.ae.basis) == 1