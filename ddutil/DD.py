#! /usr/bin/env python3
# $Id: DD.py,v 1.2 2001/11/05 19:53:33 zeller Exp $
# Enhanced Delta Debugging class
# Copyright (c) 1999, 2000, 2001 Andreas Zeller.


# This module (written in Python) implements the base delta debugging
# algorithms and is at the core of all our experiments.  This should
# easily run on any platform and any Python version since 1.6.
#
# To plug this into your system, all you have to do is to create a
# subclass with a dedicated `test()' method.  Basically, you would
# invoke the DD test case minimization algorithm (= the `ddmin()'
# method) with a list of characters; the `test()' method would combine
# them to a document and run the test.  This should be easy to realize
# and give you some good starting results; the file includes a simple
# sample application.
#
# This file is in the public domain; feel free to copy, modify, use
# and distribute this software as you wish - with one exception.
# Passau University has filed a patent for the use of delta debugging
# on program states (A. Zeller: `Isolating cause-effect chains',
# Saarland University, 2001).  The fact that this file is publicly
# available does not imply that I or anyone else grants you any rights
# related to this patent.
#
# The use of Delta Debugging to isolate failure-inducing code changes
# (A. Zeller: `Yesterday, my program worked', ESEC/FSE 1999) or to
# simplify failure-inducing input (R. Hildebrandt, A. Zeller:
# `Simplifying failure-inducing input', ISSTA 2000) is, as far as I
# know, not covered by any patent, nor will it ever be.  If you use
# this software in any way, I'd appreciate if you include a citation
# such as `This software uses the delta debugging algorithm as
# described in (insert one of the papers above)'.
#
# All about Delta Debugging is found at the delta debugging web site,
#
#               http://www.st.cs.uni-sb.de/dd/
#
# Happy debugging,
#
# Andreas Zeller


import logging
import numpy as np
from typing import List, Tuple
import random
import math
from numpy import ndarray
from networkx import DiGraph
from tabulate import tabulate

from collections import deque
from typing import List
import copy



logger = logging.getLogger()


# Start with some helpers.
class OutcomeCache:
    # This class holds test outcomes for configurations.  This avoids
    # running the same test twice.


    # The outcome cache is implemented as a tree.  Each node points
    # to the outcome of the remaining list.
    #
    # Example: ([1, 2, 3], PASS), ([1, 2], FAIL), ([1, 4, 5], FAIL):
    #
    #      (2, FAIL)--(3, PASS)
    #     /
    # (1, None)
    #     \
    #      (4, None)--(5, FAIL)
    
    def __init__(self):
        self.tail = {}                  # Points to outcome of tail
        self.result = None              # Result so far


    def add(self, c, result):
        """Add (C, RESULT) to the cache.  C must be a list of scalars."""
        cs = c[:]
        cs.sort(key=str)


        p = self
        for start in range(len(c)):
            if c[start] not in p.tail:
                p.tail[c[start]] = OutcomeCache()
            p = p.tail[c[start]]
            
        p.result = result


    def lookup(self, c):
        """Return RESULT if (C, RESULT) is in the cache; None, otherwise."""
        p = self
        for start in range(len(c)):
            if c[start] not in p.tail:
                return None
            p = p.tail[c[start]]


        return p.result


    def lookup_superset(self, c, start = 0):
        """Return RESULT if there is some (C', RESULT) in the cache with
        C' being a superset of C or equal to C.  Otherwise, return None."""


        # FIXME: Make this non-recursive!
        if start >= len(c):
            if self.result:
                return self.result
            elif self.tail != {}:
                # Select some superset
                superset = self.tail[self.tail.keys()[0]]
                return superset.lookup_superset(c, start + 1)
            else:
                return None


        if c[start] in self.tail:
            return self.tail[c[start]].lookup_superset(c, start + 1)


        # Let K0 be the largest element in TAIL such that K0 <= C[START]
        k0 = None
        for k in self.tail.keys():
            if (k0 == None or k > k0) and k <= c[start]:
                k0 = k


        if k0 != None:
            return self.tail[k0].lookup_superset(c, start)
        
        return None


    def lookup_subset(self, c):
        """Return RESULT if there is some (C', RESULT) in the cache with
        C' being a subset of C or equal to C.  Otherwise, return None."""
        p = self
        for start in range(len(c)):
            if c[start] in p.tail:
                p = p.tail[c[start]]


        return p.result
        

# Test the outcome cache
def oc_test():
    oc = OutcomeCache()


    assert oc.lookup([1, 2, 3]) == None
    oc.add([1, 2, 3], 4)
    assert oc.lookup([1, 2, 3]) == 4
    assert oc.lookup([1, 2, 3, 4]) == None


    assert oc.lookup([5, 6, 7]) == None
    oc.add([5, 6, 7], 8)
    assert oc.lookup([5, 6, 7]) == 8
    
    assert oc.lookup([]) == None
    oc.add([], 0)
    assert oc.lookup([]) == 0
    
    assert oc.lookup([1, 2]) == None
    oc.add([1, 2], 3)
    assert oc.lookup([1, 2]) == 3
    assert oc.lookup([1, 2, 3]) == 4


    assert oc.lookup_superset([1]) == 3 or oc.lookup_superset([1]) == 4
    assert oc.lookup_superset([1, 2]) == 3 or oc.lookup_superset([1, 2]) == 4
    assert oc.lookup_superset([5]) == 8
    assert oc.lookup_superset([5, 6]) == 8
    assert oc.lookup_superset([6, 7]) == 8
    assert oc.lookup_superset([7]) == 8
    assert oc.lookup_superset([]) != None


    assert oc.lookup_superset([9]) == None
    assert oc.lookup_superset([7, 9]) == None
    assert oc.lookup_superset([-5, 1]) == None
    assert oc.lookup_superset([1, 2, 3, 9]) == None
    assert oc.lookup_superset([4, 5, 6, 7]) == None


    assert oc.lookup_subset([]) == 0
    assert oc.lookup_subset([1, 2, 3]) == 4
    assert oc.lookup_subset([1, 2, 3, 4]) == 4
    assert oc.lookup_subset([1, 3]) == None
    assert oc.lookup_subset([1, 2]) == 3


    assert oc.lookup_subset([-5, 1]) == None
    assert oc.lookup_subset([-5, 1, 2]) == 3
    assert oc.lookup_subset([-5]) == 0



# Main Delta Debugging algorithm.
class DD:
    # Delta debugging base class.  To use this class for a particular
    # setting, create a subclass with an overloaded `test()' method.
    #
    # Main entry points are:
    # - `ddmin()' which computes a minimal failure-inducing configuration, and
    # - `dd()' which computes a minimal failure-inducing difference.
    #
    # See also the usage sample at the end of this file.
    #
    # For further fine-tuning, you can implement an own `resolve()'
    # method (tries to add or remove configuration elements in case of
    # inconsistencies), or implement an own `split()' method, which
    # allows you to split configurations according to your own
    # criteria.
    # 
    # The class includes other previous delta debugging alorithms,
    # which are obsolete now; they are only included for comparison
    # purposes.


    # Test outcomes.
    PASS       = "FAL"
    FAIL       = "PASS"
    UNRESOLVED = "UNRESOLVED"
    CE = "CE"
    GREEDY = 0.1


    # Resolving directions.
    ADD    = "ADD"          # Add deltas to resolve
    REMOVE = "REMOVE"           # Remove deltas to resolve


    # Debugging output (set to 1 to enable)
    debug_test      = 0
    debug_dd        = 0
    debug_split     = 0
    debug_resolve   = 0
    ERR_GAIN =1
    Matirx_GAIN = 0    
    CE_DICT={}

    def __init__(self):
        self.__resolving = 0
        self.__last_reported_length = 0
        self.monotony = 0
        self.outcome_cache  = OutcomeCache()
        self.cache_outcomes = 1
        self.minimize = 1
        self.maximize = 1
        self.assume_axioms_hold = 1
        self.ce_his = set()


    # Helpers
    def __listminus(self, c1, c2):
        """Return a list of all elements of C1 that are not in C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1
        
        c = []
        for delta in c1:
            if delta not in s2:
                c.append(delta)


        return c


    def __listintersect(self, c1, c2):
        """Return the common elements of C1 and C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1


        c = []
        for delta in c1:
            if delta in s2:
                c.append(delta)


        return c


    def __listunion(self, c1, c2):
        """Return the union of C1 and C2."""
        s1 = {}
        for delta in c1:
            s1[delta] = 1


        c = c1[:]
        for delta in c2:
            if delta not in s1:
                c.append(delta)


        return c


    def __listsubseteq(self, c1, c2):
        """Return 1 if C1 is a subset or equal to C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1


        for delta in c1:
            if delta not in s2:
                return 0


        return 1


    def show_status(self, run, cs, n):
        print("dd (run #" + repr(run) + "): trying", end=' ')
        for i in range(n):
            if i > 0:
                print("+", end=' ')
            print(len(cs[i]), end=' ')
        print()


    # Output
    def coerce(self, c):
        """Return the configuration C as a compact string"""
        # Default: use printable representation
        return repr(c)


    def pretty(self, c):
        """Like coerce(), but sort beforehand"""
        sorted_c = c[:]
        sorted_c.sort(key=str)
        return self.coerce(sorted_c)


    # Testing
    def test(self, c,dest_dir,uid):
        """Test the configuration C.  Return PASS, FAIL, or UNRESOLVED"""
        c.sort(key=str)


        # If we had this test before, return its result
        if self.cache_outcomes:
            cached_result = self.outcome_cache.lookup(c)
            if cached_result != None:
                return cached_result


        # if self.monotony:
        #     # Check whether we had a passing superset of this test before
        #     cached_result = self.outcome_cache.lookup_superset(c)
        #     if cached_result == self.PASS:
        #         return self.PASS
            
            cached_result = self.outcome_cache.lookup_subset(c)
            if cached_result == self.FAIL:
                return self.FAIL


        if self.debug_test:
            logger.debug("test({})...".format(self.coerce(c)))

        outcome = self._test(c,dest_dir,uid)


        if self.debug_test:
            logger.debug("test({}) = {}".format(self.coerce(c), repr(outcome)))


        if self.cache_outcomes:
            self.outcome_cache.add(c, outcome)


        return outcome


    def _test(self,dest_dir,uid,keep_variant):
        """Stub to overload in subclasses"""
        return self.UNRESOLVED      # Placeholder
    
    def _build(self,c,uid=None, ignore_ref=False, keep_variant=False):
        """Stub to overload in subclasses"""
        return False,None,None,None    # Placeholder
 

    # Splitting
    def split(self, c, n):
        """Split C into [C_1, C_2, ..., C_n]."""
        if self.debug_split:
            logger.debug("split({}, {})...".format(self.coerce(c), repr(n)))


        outcome = self._split(c, n)


        if self.debug_split:
            logger.debug("split({}, {}) = {}".format(self.coerce(c), repr(n), repr(outcome)))


        return outcome


    def _split(self, c, n):
        """Stub to overload in subclasses"""
        subsets = []
        start = 0
        for i in range(n):
            subset = c[start:start + int((len(c) - start) / (n - i))]
            subsets.append(subset)
            start = start + len(subset)
        return subsets



    # Resolving
    def resolve(self, csub, c, direction):
        """If direction == ADD, resolve inconsistency by adding deltas
           to CSUB.  Otherwise, resolve by removing deltas from CSUB."""


        if self.debug_resolve:
            logger.debug("resolve({}, {}, {})...".format(repr(csub), self.coerce(c), repr(direction)))


        outcome = self._resolve(csub, c, direction)


        if self.debug_resolve:
            logger.debug("resolve({}, {}, {}) = {}".format(repr(csub), self.coerce(c), repr(direction), repr(outcome)))


        return outcome



    def _resolve(self, csub, c, direction):
        """Stub to overload in subclasses."""
        # By default, no way to resolve
        return None


    # Inquiries
    def resolving(self):
        """Return 1 while resolving."""
        return self.__resolving


    # Logging
    def report_progress(self, c, title):
        if len(c) != self.__last_reported_length:
            logger.info('{}: {} deltas left: {}'.format(title, repr(len(c)), self.coerce(c)))
            #print(title + ": " + repr(len(c)) + " deltas left:", self.coerce(c))
            self.__last_reported_length = len(c)

    
    def _get_dep_matrix(self):
        return None

    def getIdx2test(self, inp1, inp2):
        res = []
        for elm in inp1:
            if not (elm in inp2):
                res.append(elm)
        return res

    def computRatio(self, deleteconfig, p) -> float:
        res = 0
        tmplog = 0.0
        for delc in deleteconfig:
            if 0 < p[delc] < 1:
                tmplog += math.log(1 - p[delc])
        tmplog = math.exp(tmplog)
        res = 1 / (1 - tmplog)
        return res

    def sample(self, p):
        delset = []
        idx = np.argsort(p)  # sort by probabilities and return index
        k = 0
        tmp = 1
        last = -99999
        idxlist = list(idx)
        i = 0
        while i < len(p):
            if p[idxlist[i]] == 0:
                k = k + 1
                i = i + 1
                continue
            if not p[idxlist[i]] < 1:
                break
            for j in range(k, i + 1):
                tmp *= (1 - p[idxlist[j]])
            tmp *= (i - k + 1)
            if tmp < last:
                break
            last = tmp
            tmp = 1
            i = i + 1
        while i > k:
            i = i - 1
            delset.append(idxlist[i])
        return delset

    def testDone(self, p):
        for prob in p:
            if abs(prob - 1.0) > 1e-6 and min(prob, 1) < 1.0:
                return False
        return True


    # General delta debugging (new TSE version)
    def dddiff(self, c):
        n = 2


        if self.debug_dd:
            logger.debug("dddiff({}, {})...".format(self.pretty(c), repr(n)))


        outcome = self._dddiff([], c, n)


        if self.debug_dd:
            logger.debug("dddiff({}, {}) = {}".format(self.pretty(c), repr(n), repr(outcome)))


        return outcome


    def _prodd(self,c):
        print("Use ProbDD")
        assert self.test([]) == self.PASS #check wether F meet T
        retseq = c
        retIdx = range(0,len(c))
        p = []
        for idx in range(0,len(c)): # initialize the probability for each element in the input sequence
            p.append(0.1)
        while not self.testDone(p):
            delIdx = self.sample(p)
            if len(delIdx) == 0:
                break
            idx2test = self.getIdx2test(retIdx,delIdx) 
            if self.test(idx2test) == self.FAIL: # set probabilities of the deleted elements to 0
                for set0 in range(0,len(p)):
                    if set0 not in idx2test:
                        p[set0] = 0
                retIdx = idx2test
            else: #test(seq2test, *test_args) == PASS:
                for setd in range(0,len(p)):
                    if setd in delIdx and p[setd] != 0 and p[setd] != 1:
                        delta = (self.computRatio(delIdx,p) - 1) * p[setd]
                        p[setd] = p[setd] + delta
        return retseq

if __name__ == '__main__':
    # Test the outcome cache
    oc_test()
    
    # Define our own DD class, with its own test method
    class MyDD(DD):        
        def _test_a(self, c):
            "Test the configuration C.  Return PASS, FAIL, or UNRESOLVED."


            # Just a sample
            # if 2 in c and not 3 in c:
            #   return self.UNRESOLVED
            # if 3 in c and not 7 in c:
            #   return self.UNRESOLVED
            if 7 in c and not 2 in c:
                return self.UNRESOLVED
            if 5 in c and 8 in c:
                return self.FAIL
            return self.PASS


        def _test_b(self, c):
            if c == []:
                return self.PASS
            if 1 in c and 2 in c and 3 in c and 4 in c and \
               5 in c and 6 in c and 7 in c and 8 in c:
                return self.FAIL
            return self.UNRESOLVED


        def _test_c(self, c):
            if 1 in c and 2 in c and 3 in c and 4 in c and \
               6 in c and 8 in c:
                if 5 in c and 7 in c:
                    return self.UNRESOLVED
                else:
                    return self.FAIL
            if 1 in c or 2 in c or 3 in c or 4 in c or \
               6 in c or 8 in c:
                return self.UNRESOLVED
            return self.PASS


        def __init__(self):
            self._test = self._test_c
            DD.__init__(self)
                        


    logger.info("WYNOT - a tool for delta debugging.")
    mydd = MyDD()
    # mydd.debug_test     = 1           # Enable debugging output
    # mydd.debug_dd       = 1           # Enable debugging output
    # mydd.debug_split    = 1           # Enable debugging output
    # mydd.debug_resolve  = 1           # Enable debugging output


    # mydd.cache_outcomes = 0
    # mydd.monotony = 0


    logger.info("Minimizing failure-inducing input...")
    c = mydd.ddmin([1, 2, 3, 4, 5, 6, 7, 8])  # Invoke DDMIN
    logger.info("The 1-minimal failure-inducing input is {}".format(c))
    logger.info("Removing any element will make the failure go away.")
    logger.info('')
    
    logger.info("Computing the failure-inducing difference...")
    (c, c1, c2) = mydd.dd([1, 2, 3, 4, 5, 6, 7, 8]) # Invoke DD
    logger.info("The 1-minimal failure-inducing difference is {}".format(c))
    logger.info("{} passes, {} fails".format(c1, c2))
    


# Local Variables:
# mode: python
# End: