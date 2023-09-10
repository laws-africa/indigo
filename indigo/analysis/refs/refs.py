# This file was generated from indigo/analysis/refs/refs.peg
# See https://canopy.jcoglan.com/ for documentation

from collections import defaultdict
import re


class TreeNode(object):
    def __init__(self, text, offset, elements):
        self.text = text
        self.offset = offset
        self.elements = elements

    def __iter__(self):
        for el in self.elements:
            yield el


class TreeNode1(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode1, self).__init__(text, offset, elements)
        self.reference = elements[0]


class TreeNode2(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode2, self).__init__(text, offset, elements)
        self.reference = elements[3]


class TreeNode3(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode3, self).__init__(text, offset, elements)
        self.main_ref = elements[2]
        self.sub_refs = elements[4]


class TreeNode4(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode4, self).__init__(text, offset, elements)
        self.sub_ref = elements[0]


class TreeNode5(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode5, self).__init__(text, offset, elements)
        self.sub_ref = elements[1]


class TreeNode6(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode6, self).__init__(text, offset, elements)
        self.digit = elements[0]


class TreeNode7(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode7, self).__init__(text, offset, elements)
        self.alpha_num_dot = elements[1]


FAILURE = object()


class Grammar(object):
    REGEX_1 = re.compile('^[0-9]')
    REGEX_2 = re.compile('^[a-zA-Z0-9.-]')

    def _read_root(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['root'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_reference()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2, elements1, address3 = self._offset, [], None
            while True:
                index3, elements2 = self._offset, []
                address4 = FAILURE
                index4, elements3, address5 = self._offset, [], None
                while True:
                    address5 = self._read_WS()
                    if address5 is not FAILURE:
                        elements3.append(address5)
                    else:
                        break
                if len(elements3) >= 1:
                    address4 = TreeNode(self._input[index4:self._offset], index4, elements3)
                    self._offset = self._offset
                else:
                    address4 = FAILURE
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address6 = FAILURE
                    index5 = self._offset
                    chunk0, max0 = None, self._offset + 3
                    if max0 <= self._input_size:
                        chunk0 = self._input[self._offset:max0]
                    if chunk0 == 'and':
                        address6 = TreeNode(self._input[self._offset:self._offset + 3], self._offset, [])
                        self._offset = self._offset + 3
                    else:
                        address6 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append(('Refs::root', '"and"'))
                    if address6 is FAILURE:
                        self._offset = index5
                        chunk1, max1 = None, self._offset + 2
                        if max1 <= self._input_size:
                            chunk1 = self._input[self._offset:max1]
                        if chunk1 == 'or':
                            address6 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
                            self._offset = self._offset + 2
                        else:
                            address6 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append(('Refs::root', '"or"'))
                        if address6 is FAILURE:
                            self._offset = index5
                    if address6 is not FAILURE:
                        elements2.append(address6)
                        address7 = FAILURE
                        index6, elements4, address8 = self._offset, [], None
                        while True:
                            address8 = self._read_WS()
                            if address8 is not FAILURE:
                                elements4.append(address8)
                            else:
                                break
                        if len(elements4) >= 1:
                            address7 = TreeNode(self._input[index6:self._offset], index6, elements4)
                            self._offset = self._offset
                        else:
                            address7 = FAILURE
                        if address7 is not FAILURE:
                            elements2.append(address7)
                            address9 = FAILURE
                            address9 = self._read_reference()
                            if address9 is not FAILURE:
                                elements2.append(address9)
                            else:
                                elements2 = None
                                self._offset = index3
                        else:
                            elements2 = None
                            self._offset = index3
                    else:
                        elements2 = None
                        self._offset = index3
                else:
                    elements2 = None
                    self._offset = index3
                if elements2 is None:
                    address3 = FAILURE
                else:
                    address3 = TreeNode2(self._input[index3:self._offset], index3, elements2)
                    self._offset = self._offset
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address10 = FAILURE
                index7 = self._offset
                address10 = self._read_of()
                if address10 is FAILURE:
                    address10 = TreeNode(self._input[index7:index7], index7, [])
                    self._offset = index7
                if address10 is not FAILURE:
                    elements0.append(address10)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.root(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['root'][index0] = (address0, self._offset)
        return address0

    def _read_reference(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['reference'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0, max0 = None, self._offset + 7
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'section'.lower():
            address1 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
            self._offset = self._offset + 7
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::reference', '`section`'))
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_WS()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 1:
                address2 = TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                address4 = self._read_main_ref()
                if address4 is not FAILURE:
                    elements0.append(address4)
                    address5 = FAILURE
                    index3, elements2, address6 = self._offset, [], None
                    while True:
                        address6 = self._read_WS()
                        if address6 is not FAILURE:
                            elements2.append(address6)
                        else:
                            break
                    if len(elements2) >= 0:
                        address5 = TreeNode(self._input[index3:self._offset], index3, elements2)
                        self._offset = self._offset
                    else:
                        address5 = FAILURE
                    if address5 is not FAILURE:
                        elements0.append(address5)
                        address7 = FAILURE
                        address7 = self._read_sub_refs()
                        if address7 is not FAILURE:
                            elements0.append(address7)
                        else:
                            elements0 = None
                            self._offset = index1
                    else:
                        elements0 = None
                        self._offset = index1
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.reference(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['reference'][index0] = (address0, self._offset)
        return address0

    def _read_sub_refs(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['sub_refs'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_sub_ref()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2, elements1, address3 = self._offset, [], None
            while True:
                index3, elements2 = self._offset, []
                address4 = FAILURE
                index4 = self._offset
                address4 = self._read_range()
                if address4 is FAILURE:
                    self._offset = index4
                    index5, elements3 = self._offset, []
                    address5 = FAILURE
                    index6, elements4, address6 = self._offset, [], None
                    while True:
                        address6 = self._read_WS()
                        if address6 is not FAILURE:
                            elements4.append(address6)
                        else:
                            break
                    if len(elements4) >= 1:
                        address5 = TreeNode(self._input[index6:self._offset], index6, elements4)
                        self._offset = self._offset
                    else:
                        address5 = FAILURE
                    if address5 is not FAILURE:
                        elements3.append(address5)
                        address7 = FAILURE
                        index7 = self._offset
                        chunk0, max0 = None, self._offset + 3
                        if max0 <= self._input_size:
                            chunk0 = self._input[self._offset:max0]
                        if chunk0 == 'and':
                            address7 = TreeNode(self._input[self._offset:self._offset + 3], self._offset, [])
                            self._offset = self._offset + 3
                        else:
                            address7 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append(('Refs::sub_refs', '"and"'))
                        if address7 is FAILURE:
                            self._offset = index7
                            chunk1, max1 = None, self._offset + 2
                            if max1 <= self._input_size:
                                chunk1 = self._input[self._offset:max1]
                            if chunk1 == 'or':
                                address7 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
                                self._offset = self._offset + 2
                            else:
                                address7 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append(('Refs::sub_refs', '"or"'))
                            if address7 is FAILURE:
                                self._offset = index7
                        if address7 is not FAILURE:
                            elements3.append(address7)
                            address8 = FAILURE
                            index8, elements5, address9 = self._offset, [], None
                            while True:
                                address9 = self._read_WS()
                                if address9 is not FAILURE:
                                    elements5.append(address9)
                                else:
                                    break
                            if len(elements5) >= 1:
                                address8 = TreeNode(self._input[index8:self._offset], index8, elements5)
                                self._offset = self._offset
                            else:
                                address8 = FAILURE
                            if address8 is not FAILURE:
                                elements3.append(address8)
                            else:
                                elements3 = None
                                self._offset = index5
                        else:
                            elements3 = None
                            self._offset = index5
                    else:
                        elements3 = None
                        self._offset = index5
                    if elements3 is None:
                        address4 = FAILURE
                    else:
                        address4 = TreeNode(self._input[index5:self._offset], index5, elements3)
                        self._offset = self._offset
                    if address4 is FAILURE:
                        self._offset = index4
                        index9, elements6, address10 = self._offset, [], None
                        while True:
                            index10 = self._offset
                            index11, elements7, address11 = self._offset, [], None
                            while True:
                                address11 = self._read_WS()
                                if address11 is not FAILURE:
                                    elements7.append(address11)
                                else:
                                    break
                            if len(elements7) >= 1:
                                address10 = TreeNode(self._input[index11:self._offset], index11, elements7)
                                self._offset = self._offset
                            else:
                                address10 = FAILURE
                            if address10 is FAILURE:
                                self._offset = index10
                                chunk2, max2 = None, self._offset + 1
                                if max2 <= self._input_size:
                                    chunk2 = self._input[self._offset:max2]
                                if chunk2 == ',':
                                    address10 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                                    self._offset = self._offset + 1
                                else:
                                    address10 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append(('Refs::sub_refs', '","'))
                                if address10 is FAILURE:
                                    self._offset = index10
                            if address10 is not FAILURE:
                                elements6.append(address10)
                            else:
                                break
                        if len(elements6) >= 0:
                            address4 = TreeNode(self._input[index9:self._offset], index9, elements6)
                            self._offset = self._offset
                        else:
                            address4 = FAILURE
                        if address4 is FAILURE:
                            self._offset = index4
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address12 = FAILURE
                    address12 = self._read_sub_ref()
                    if address12 is not FAILURE:
                        elements2.append(address12)
                    else:
                        elements2 = None
                        self._offset = index3
                else:
                    elements2 = None
                    self._offset = index3
                if elements2 is None:
                    address3 = FAILURE
                else:
                    address3 = TreeNode5(self._input[index3:self._offset], index3, elements2)
                    self._offset = self._offset
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.sub_refs(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['sub_refs'][index0] = (address0, self._offset)
        return address0

    def _read_main_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['main_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_digit()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_alpha_num_dot()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.main_ref(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['main_ref'][index0] = (address0, self._offset)
        return address0

    def _read_range(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['range'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2, elements1, address2 = self._offset, [], None
        while True:
            address2 = self._read_WS()
            if address2 is not FAILURE:
                elements1.append(address2)
            else:
                break
        if len(elements1) >= 1:
            address1 = TreeNode(self._input[index2:self._offset], index2, elements1)
            self._offset = self._offset
        else:
            address1 = FAILURE
        if address1 is not FAILURE:
            elements0.append(address1)
            address3 = FAILURE
            chunk0, max0 = None, self._offset + 2
            if max0 <= self._input_size:
                chunk0 = self._input[self._offset:max0]
            if chunk0 == 'to':
                address3 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
                self._offset = self._offset + 2
            else:
                address3 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('Refs::range', '"to"'))
            if address3 is not FAILURE:
                elements0.append(address3)
                address4 = FAILURE
                index3, elements2, address5 = self._offset, [], None
                while True:
                    address5 = self._read_WS()
                    if address5 is not FAILURE:
                        elements2.append(address5)
                    else:
                        break
                if len(elements2) >= 1:
                    address4 = TreeNode(self._input[index3:self._offset], index3, elements2)
                    self._offset = self._offset
                else:
                    address4 = FAILURE
                if address4 is not FAILURE:
                    elements0.append(address4)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.range(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['range'][index0] = (address0, self._offset)
        return address0

    def _read_sub_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['sub_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '(':
            address1 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::sub_ref', '"("'))
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_alpha_num_dot()
            if address2 is not FAILURE:
                elements0.append(address2)
                address3 = FAILURE
                chunk1, max1 = None, self._offset + 1
                if max1 <= self._input_size:
                    chunk1 = self._input[self._offset:max1]
                if chunk1 == ')':
                    address3 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('Refs::sub_ref', '")"'))
                if address3 is not FAILURE:
                    elements0.append(address3)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.sub_ref(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['sub_ref'][index0] = (address0, self._offset)
        return address0

    def _read_of(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2, elements1, address2 = self._offset, [], None
        while True:
            address2 = self._read_WS()
            if address2 is not FAILURE:
                elements1.append(address2)
            else:
                break
        if len(elements1) >= 1:
            address1 = TreeNode(self._input[index2:self._offset], index2, elements1)
            self._offset = self._offset
        else:
            address1 = FAILURE
        if address1 is not FAILURE:
            elements0.append(address1)
            address3 = FAILURE
            index3 = self._offset
            chunk0, max0 = None, self._offset + 2
            if max0 <= self._input_size:
                chunk0 = self._input[self._offset:max0]
            if chunk0 == 'of':
                address3 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
                self._offset = self._offset + 2
            else:
                address3 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('Refs::of', '"of"'))
            if address3 is FAILURE:
                self._offset = index3
                chunk1, max1 = None, self._offset + 7
                if max1 <= self._input_size:
                    chunk1 = self._input[self._offset:max1]
                if chunk1 == 'thereof':
                    address3 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                    self._offset = self._offset + 7
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('Refs::of', '"thereof"'))
                if address3 is FAILURE:
                    self._offset = index3
            if address3 is not FAILURE:
                elements0.append(address3)
                address4 = FAILURE
                index4, elements2, address5 = self._offset, [], None
                while True:
                    address5 = self._read_WS()
                    if address5 is not FAILURE:
                        elements2.append(address5)
                    else:
                        break
                if len(elements2) >= 1:
                    address4 = TreeNode(self._input[index4:self._offset], index4, elements2)
                    self._offset = self._offset
                else:
                    address4 = FAILURE
                if address4 is not FAILURE:
                    elements0.append(address4)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = TreeNode(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        self._cache['of'][index0] = (address0, self._offset)
        return address0

    def _read_digit(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['digit'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and Grammar.REGEX_1.search(chunk0):
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::digit', '[0-9]'))
        self._cache['digit'][index0] = (address0, self._offset)
        return address0

    def _read_alpha_num_dot(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['alpha_num_dot'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and Grammar.REGEX_2.search(chunk0):
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::alpha_num_dot', '[a-zA-Z0-9.-]'))
        self._cache['alpha_num_dot'][index0] = (address0, self._offset)
        return address0

    def _read_WS(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['WS'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == ' ':
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::WS', '" "'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 1
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 == '\t':
                address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                self._offset = self._offset + 1
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('Refs::WS', '"\\t"'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['WS'][index0] = (address0, self._offset)
        return address0


class Parser(Grammar):
    def __init__(self, input, actions, types):
        self._input = input
        self._input_size = len(input)
        self._actions = actions
        self._types = types
        self._offset = 0
        self._cache = defaultdict(dict)
        self._failure = 0
        self._expected = []

    def parse(self):
        tree = self._read_root()
        if tree is not FAILURE and self._offset == self._input_size:
            return tree
        if not self._expected:
            self._failure = self._offset
            self._expected.append(('Refs', '<EOF>'))
        raise ParseError(format_error(self._input, self._failure, self._expected))


class ParseError(SyntaxError):
    pass


def parse(input, actions=None, types=None):
    parser = Parser(input, actions, types)
    return parser.parse()

def format_error(input, offset, expected):
    lines = input.split('\n')
    line_no, position = 0, 0

    while position <= offset:
        position += len(lines[line_no]) + 1
        line_no += 1

    line = lines[line_no - 1]
    message = 'Line ' + str(line_no) + ': expected one of:\n\n'

    for pair in expected:
        message += '    - ' + pair[1] + ' from ' + pair[0] + '\n'

    number = str(line_no)
    while len(number) < 6:
        number = ' ' + number

    message += '\n' + number + ' | ' + line + '\n'
    message += ' ' * (len(line) + 10 + offset - position)
    return message + '^'
