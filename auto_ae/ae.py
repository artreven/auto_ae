'''
Created on Feb 5, 2014

@author: artreven
'''
import os
import time
import logging

import fca.readwrite.cxt

class AE(object):
    '''
    Class to represent Attribute Exploration procedure. Every instance
    possesses a context and two special functions. The first one *ce_finder* is
    capable of finding objects which have a given subset of attributes and do
    not have a given attribute (possibly, a given subset of attributes).
    Therefore *ce_finder* is capable of finding counter-examples to implications
    of the context; the counter-examples are further added to the context.
    The second special function *go_on* is essential for the extensions of 
    Attribute Exploration. When no further counter-examples can be found *go_on*
    is required to perform an action. It could add new attributes, try different
    strategy for finding counter-examples, try to prove implications, etc. The
    whole procedure is supposed to run automatically (except for, probably, 
    manual change of time limit for *ce_finder* and *go_on*) and produce enlarged
    context. Implicative theory of the context approximates (or, in best case,
    is equal to) the implicative theory of the corresponding data domain.
    @see: *advance* method for details about *go_on* function.
    @see: *find_ces* method for details about *ce_finder* function.
    
    A possibility of considering equal sets of objects and attributes is
    provided. In this case every new entity is a new object and a new attribute
    at the same time.
    
    A function *has_attribute* is required for finding incidence relation I.
    
    Class instance creates a logger and outputs all the progress in
    './progress.log' file via logger.
    
    Functions for public interface include functions for adding objects
    and attributes, calculating basis, running the procedure, finding
    counter-examples, advancing without any counter-examples found.
    '''

    def __init__(self, dest, cxt, has_attribute, ce_finder, go_on=None,
                 attributes_growing=False, get_new_attribute=lambda x: x):
        '''
        Constructor
        
        @param dest: destination for current AE.
        @param cxt: initial cxt to start with.
        @param has_attribute: function taking object_name and attribute_name and
        return incidence relation - Boolean value.
        @param ce_finder: see *find_ces* method.
        @param go_on: see *advance* method.
        @param attributes_changing: determines if new attribute should be added.
        @ivar step: current step of AE
        '''
        self.dest = _check_dest(dest)
        open(dest + '/progress.log', 'a').close()
        logging.basicConfig(filename=dest + '/progress.log',
                            filemode='w',
                            format='%(levelname)s %(asctime)s: %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
#         self.logger = logging.getLogger(__name__)
        self.cxt = cxt
        self.go_on = go_on
        self.ce_finder = ce_finder # usage *ce_finder(implication, wait)* => (ce, imp)
        self.has_attribute = has_attribute
        self.get_new_attribute = get_new_attribute
        self.attributes_growing = attributes_growing
        self.step = 1
        
    def _reset(self):
        del self._basis
        
    def _get_basis(self):
        try:
            if self._basis != None:
                return self._basis
        except AttributeError:
            pass
        ts = time.time()
        basis = self.cxt.get_attribute_canonical_basis()
        te = time.time()
        m = '\nIt took {0} seconds to compute the canonical basis.\n'.format(te-ts)
        logging.info(m)
        self._basis = basis
        return basis

    basis = property(_get_basis)
    
    def output_implications(self):
        with open(self.dest + '/implication_basis_step{0}.txt'.format(self.step),
                  'w') as f:
            for imp in self.basis:
                f.write(str(imp) + '\n')
        
    def output_cxt(self, name):
        with open(self.dest + '/' + name + '.txt', 'w') as f:
            f.write(str(self.cxt) + '\n')
        fca.readwrite.cxt.write_cxt(self.cxt, self.dest + '/' + name + '.cxt')
        
    def add_row(self, row, object_name):
        self.cxt.add_object(row, object_name)
        self._reset()
        
    def add_column(self, col, attr_name):
        self.cxt.add_attribute(col, attr_name)
        self._reset()
        
    def add_object(self, object_name):
        row = [self.has_attribute(object_name, attr)
               for attr in self.cxt.attributes]
        self.add_row(row, object_name)
    
    def add_attribute(self, attribute_name):
        column = [self.has_attribute(obj, attribute_name)
                  for obj in self.cxt.objects]
        self.add_column(column, attribute_name)
    
    def reduce_objects(self):
        self.cxt = self.cxt.reduce_objects()
        
    def reduce_attributes(self):
        self.cxt = self.cxt.reduce_attributes()
        
    def advance(self, wait=float('inf')):
        """
        Launch *go_on* function. Function *go_on* takes time limit *wait* and 
        the instance of AE, therefore, it is able to manipulate context.
        However, it is expected that it does not produce any changes in AE
        instance (and in the context). There is only one time limit parameter,
        therefore, if several time constraints needed they should be expressed
        through *wait* parameter. *go_on* produce a tuple of new objects and
        new attributes. They are added to the context.
        
        It is not necessary that during the run of this functions new
        entities are found. For example, *go_on* could try to prove
        the implications. In this case output of *go_on* should be ([], []).
        
        @param wait: time limit for *go_on* function.
        """
        if self.go_on == None:
            m = '\nDo not know how to continue.'
            logging.info(m)
            return ([], [])
        ts = time.time()
        (new_objects, new_attributes) = self.go_on(self, wait)
        te = time.time()
        m = '\n\tADVANCE PHASE, wait = {0}:\n'.format(wait)
        m += 'It took {0} seconds.\n'.format(te - ts)
        if new_objects or new_attributes:
            for new_obj in new_objects:
                self.add_object(str(new_obj))
            for new_attr in new_attributes:
                self.add_attribute(str(new_attr))
            self.step += 1
        else:
            m += 'No new entities.\n'
        if new_objects:
            self.reduce_objects()
            m += '{0} new objects found: {1}\n'.format(len(new_objects), new_objects)
            m += '{0} objects left after reducing.\n'.format(len(self.cxt.objects))
        if new_attributes:
            self.reduce_attributes()
            m += '{0} new attributes found: {1}\n'.format(len(new_attributes), new_attributes)
            m += '{0} attributes left after reducing.\n'.format(len(self.cxt.attributes))
        logging.info(m)
        return new_objects, new_attributes
    
    def find_ces(self, imps, wait=float('inf')):
        """
        Try to find counter-examples for implications from *imps* and, if found,
        add them to the context. *ce_finder* takes implication and *wait* and
        returns a counter-example to this implication and a *reason*. String *reason*
        contains additional information about finding process, for example,
        if no counter-example found it could tell that this is due to timeout.
        The counter-example has to be compatible with *has_attribute* function.
        *ce_finder* should return *None* if no counter-example found to current
        implication. There is only one time limit parameter, therefore, if
        several time constraints needed they should be expressed through *wait*
        parameter.
        
        @attention: only one counter-example is added at a time. After finding first counter-example method quits.
        @param wait: time limit for self.ce_finder.
        @param imps: implications in non-unit form; if needed convert to unit form in *ce_finder*;
        this is to allow speed up if *ce_finder* is able to process non-unit implications.
        @return: (implication, counter-example).
        """
        s_imps = set(imps)
        num_imps = len(s_imps)
        ts = time.time()
        cnt = 0
        with open(self.dest + '/step{0}ces.txt'.format(self.step), 'a') as f:
            f.write('\tCurrent Context:\n' + str(self.cxt) + '\n'*5)
            f.write('Total {0} (non-unit) implications.\n'.format(num_imps))
        for imp in s_imps:
            cnt += 1
            ts_ce = time.time() 
            (ce, reason) = self.ce_finder(imp, wait)
            te_ce = time.time()
            with open(self.dest + '/step{0}ces.txt'.format(self.step), 'a') as f:
                m = str(imp) + '\n'
                if ce:
                    m += 'Found: ' + str(ce)
                else:
                    m += reason
                m += '\nTime taken:{0}\n\n'.format(te_ce - ts_ce)
                f.write(m)
            if ce:
                self.add_object(repr(ce))
                self.reduce_objects()
                if self.attributes_growing:
                    new_attribute = self.get_new_attribute(ce)
                    if new_attribute:
                        self.add_attribute(repr(new_attribute))
                        self.reduce_attributes()
                self.step += 1
                break
        te = time.time()
        # messages
        m = '\nCOUNTER-EXAMPLE FINDING PHASE, wait = {0}:\n'.format(wait)
        m += 'It took {0} seconds.\n'.format(te - ts)
        m += 'Total {0} (non-unit) implications, '.format(num_imps)
        m += 'processed {0} implications.\n'.format(cnt)
        if ce:
            m += '\tNew counter-example: '
            m += '{0} is a counter-example to {1}.\n'.format(ce, imp)
            m += '{0} objects left after reducing.\n'.format(len(self.cxt.objects))
            if self.attributes_growing and new_attribute:
                m += 'New attribute {0} added.\n'.format(str(new_attribute))
                m += '{0} attributes left after reducing.\n'.format(len(self.cxt.attributes))
        else:
            m += 'No counter-examples found.\n'
        logging.info(m)
        return ce, imp
    
    def run(self, ce_wait, go_on_wait=float('inf')):
        """
        Run Attribute Exploration procedure. On every step first *find_ces* is
        launched. If counter-examples found, proceeds to next step. If no
        counter-examples found, *advance* is launched. If any new objects or
        new attributes added, proceeds to next step. If no changes made after
        *advance* function, *run* quits.
        
        @param ce_wait: time limit for *ce_finder*.
        @param go_on_wait: time limit for *go_on*.
        """
        while True:
            self.output_cxt('current_cxt')
            m = '\n\tSTARTING STEP {0}\n'.format(self.step)
            m += 'There were {0} '.format(len(self.cxt.objects))
            m += 'objects before the start of this step\n'
            if self.attributes_growing:
                m += 'There were {0} '.format(len(self.cxt.attributes))
                m += 'attributes before the start of this step\n'
            logging.info(m)
            basis = self.basis
            (ce, imp_ce) = self.find_ces(basis, ce_wait)
            if not ce:
                new_objects, new_attributes = self.advance(go_on_wait)
                if not (new_objects or new_attributes):
                    break
                    
###############################################################################
def _check_dest(dest):
    """
    Check if directory does not exist. if it does not exist create it and return
    *dest*
    """
    if not os.path.exists(dest):
        os.makedirs(dest)
    return dest
    
########################################################
if __name__ == '__main__':
    pass