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
        self.and_or = elements[0]
        self.reference = elements[1]


class TreeNode3(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode3, self).__init__(text, offset, elements)
        self.unit = elements[0]
        self.main_ref = elements[2]


class TreeNode4(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode4, self).__init__(text, offset, elements)
        self.digit = elements[0]


class TreeNode5(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode5, self).__init__(text, offset, elements)
        self.sub_ref = elements[0]


class TreeNode6(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode6, self).__init__(text, offset, elements)
        self.sub_ref = elements[1]


class TreeNode7(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode7, self).__init__(text, offset, elements)
        self.num = elements[0]


class TreeNode8(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode8, self).__init__(text, offset, elements)
        self.num = elements[1]


class TreeNode9(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode9, self).__init__(text, offset, elements)
        self.to = elements[2]


class TreeNode10(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode10, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode11(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode11, self).__init__(text, offset, elements)
        self._and = elements[2]


class TreeNode12(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode12, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode13(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode13, self).__init__(text, offset, elements)
        self._or = elements[2]


class TreeNode14(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode14, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode15(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode15, self).__init__(text, offset, elements)
        self.comma = elements[1]


FAILURE = object()


class Grammar(object):
    REGEX_1 = re.compile('^[,;]')
    REGEX_2 = re.compile('^[0-9]')
    REGEX_3 = re.compile('^[a-zA-Z0-9.-]')

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
                address4 = self._read_and_or()
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address5 = FAILURE
                    address5 = self._read_reference()
                    if address5 is not FAILURE:
                        elements2.append(address5)
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
                address6 = FAILURE
                index4 = self._offset
                address6 = self._read_of()
                if address6 is FAILURE:
                    address6 = TreeNode(self._input[index4:index4], index4, [])
                    self._offset = index4
                if address6 is not FAILURE:
                    elements0.append(address6)
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
        address1 = self._read_unit()
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
                        index4 = self._offset
                        address7 = self._read_sub_refs()
                        if address7 is FAILURE:
                            address7 = TreeNode(self._input[index4:index4], index4, [])
                            self._offset = index4
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
                    address4 = self._read_and_or()
                    if address4 is FAILURE:
                        self._offset = index4
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address5 = FAILURE
                    address5 = self._read_sub_ref()
                    if address5 is not FAILURE:
                        elements2.append(address5)
                    else:
                        elements2 = None
                        self._offset = index3
                else:
                    elements2 = None
                    self._offset = index3
                if elements2 is None:
                    address3 = FAILURE
                else:
                    address3 = TreeNode6(self._input[index3:self._offset], index3, elements2)
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

    def _read_sub_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['sub_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_num()
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
                if len(elements3) >= 0:
                    address4 = TreeNode(self._input[index4:self._offset], index4, elements3)
                    self._offset = self._offset
                else:
                    address4 = FAILURE
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address6 = FAILURE
                    address6 = self._read_num()
                    if address6 is not FAILURE:
                        elements2.append(address6)
                    else:
                        elements2 = None
                        self._offset = index3
                else:
                    elements2 = None
                    self._offset = index3
                if elements2 is None:
                    address3 = FAILURE
                else:
                    address3 = TreeNode8(self._input[index3:self._offset], index3, elements2)
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
            address0 = self._actions.sub_ref(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['sub_ref'][index0] = (address0, self._offset)
        return address0

    def _read_num(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['num'].get(index0)
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
                self._expected.append(('Refs::num', '"("'))
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
            if len(elements1) >= 1:
                address2 = TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                chunk1, max1 = None, self._offset + 1
                if max1 <= self._input_size:
                    chunk1 = self._input[self._offset:max1]
                if chunk1 == ')':
                    address4 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                    self._offset = self._offset + 1
                else:
                    address4 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('Refs::num', '")"'))
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
            address0 = self._actions.num(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['num'][index0] = (address0, self._offset)
        return address0

    def _read_range(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['range'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        index3, elements1 = self._offset, []
        address2 = FAILURE
        index4, elements2, address3 = self._offset, [], None
        while True:
            address3 = self._read_WS()
            if address3 is not FAILURE:
                elements2.append(address3)
            else:
                break
        if len(elements2) >= 0:
            address2 = TreeNode(self._input[index4:self._offset], index4, elements2)
            self._offset = self._offset
        else:
            address2 = FAILURE
        if address2 is not FAILURE:
            elements1.append(address2)
            address4 = FAILURE
            address4 = self._read_comma()
            if address4 is not FAILURE:
                elements1.append(address4)
            else:
                elements1 = None
                self._offset = index3
        else:
            elements1 = None
            self._offset = index3
        if elements1 is None:
            address1 = FAILURE
        else:
            address1 = TreeNode10(self._input[index3:self._offset], index3, elements1)
            self._offset = self._offset
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address5 = FAILURE
            index5, elements3, address6 = self._offset, [], None
            while True:
                address6 = self._read_WS()
                if address6 is not FAILURE:
                    elements3.append(address6)
                else:
                    break
            if len(elements3) >= 1:
                address5 = TreeNode(self._input[index5:self._offset], index5, elements3)
                self._offset = self._offset
            else:
                address5 = FAILURE
            if address5 is not FAILURE:
                elements0.append(address5)
                address7 = FAILURE
                address7 = self._read_to()
                if address7 is not FAILURE:
                    elements0.append(address7)
                    address8 = FAILURE
                    index6, elements4, address9 = self._offset, [], None
                    while True:
                        address9 = self._read_WS()
                        if address9 is not FAILURE:
                            elements4.append(address9)
                        else:
                            break
                    if len(elements4) >= 1:
                        address8 = TreeNode(self._input[index6:self._offset], index6, elements4)
                        self._offset = self._offset
                    else:
                        address8 = FAILURE
                    if address8 is not FAILURE:
                        elements0.append(address8)
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
            address0 = self._actions.range(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['range'][index0] = (address0, self._offset)
        return address0

    def _read_and_or(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['and_or'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        index2, elements0 = self._offset, []
        address1 = FAILURE
        index3 = self._offset
        index4, elements1 = self._offset, []
        address2 = FAILURE
        index5, elements2, address3 = self._offset, [], None
        while True:
            address3 = self._read_WS()
            if address3 is not FAILURE:
                elements2.append(address3)
            else:
                break
        if len(elements2) >= 0:
            address2 = TreeNode(self._input[index5:self._offset], index5, elements2)
            self._offset = self._offset
        else:
            address2 = FAILURE
        if address2 is not FAILURE:
            elements1.append(address2)
            address4 = FAILURE
            address4 = self._read_comma()
            if address4 is not FAILURE:
                elements1.append(address4)
            else:
                elements1 = None
                self._offset = index4
        else:
            elements1 = None
            self._offset = index4
        if elements1 is None:
            address1 = FAILURE
        else:
            address1 = TreeNode12(self._input[index4:self._offset], index4, elements1)
            self._offset = self._offset
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index3:index3], index3, [])
            self._offset = index3
        if address1 is not FAILURE:
            elements0.append(address1)
            address5 = FAILURE
            index6, elements3, address6 = self._offset, [], None
            while True:
                address6 = self._read_WS()
                if address6 is not FAILURE:
                    elements3.append(address6)
                else:
                    break
            if len(elements3) >= 1:
                address5 = TreeNode(self._input[index6:self._offset], index6, elements3)
                self._offset = self._offset
            else:
                address5 = FAILURE
            if address5 is not FAILURE:
                elements0.append(address5)
                address7 = FAILURE
                address7 = self._read__and()
                if address7 is not FAILURE:
                    elements0.append(address7)
                    address8 = FAILURE
                    index7, elements4, address9 = self._offset, [], None
                    while True:
                        address9 = self._read_WS()
                        if address9 is not FAILURE:
                            elements4.append(address9)
                        else:
                            break
                    if len(elements4) >= 1:
                        address8 = TreeNode(self._input[index7:self._offset], index7, elements4)
                        self._offset = self._offset
                    else:
                        address8 = FAILURE
                    if address8 is not FAILURE:
                        elements0.append(address8)
                    else:
                        elements0 = None
                        self._offset = index2
                else:
                    elements0 = None
                    self._offset = index2
            else:
                elements0 = None
                self._offset = index2
        else:
            elements0 = None
            self._offset = index2
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.and_or(self._input, index2, self._offset, elements0)
            self._offset = self._offset
        if address0 is FAILURE:
            self._offset = index1
            index8, elements5 = self._offset, []
            address10 = FAILURE
            index9 = self._offset
            index10, elements6 = self._offset, []
            address11 = FAILURE
            index11, elements7, address12 = self._offset, [], None
            while True:
                address12 = self._read_WS()
                if address12 is not FAILURE:
                    elements7.append(address12)
                else:
                    break
            if len(elements7) >= 0:
                address11 = TreeNode(self._input[index11:self._offset], index11, elements7)
                self._offset = self._offset
            else:
                address11 = FAILURE
            if address11 is not FAILURE:
                elements6.append(address11)
                address13 = FAILURE
                address13 = self._read_comma()
                if address13 is not FAILURE:
                    elements6.append(address13)
                else:
                    elements6 = None
                    self._offset = index10
            else:
                elements6 = None
                self._offset = index10
            if elements6 is None:
                address10 = FAILURE
            else:
                address10 = TreeNode14(self._input[index10:self._offset], index10, elements6)
                self._offset = self._offset
            if address10 is FAILURE:
                address10 = TreeNode(self._input[index9:index9], index9, [])
                self._offset = index9
            if address10 is not FAILURE:
                elements5.append(address10)
                address14 = FAILURE
                index12, elements8, address15 = self._offset, [], None
                while True:
                    address15 = self._read_WS()
                    if address15 is not FAILURE:
                        elements8.append(address15)
                    else:
                        break
                if len(elements8) >= 1:
                    address14 = TreeNode(self._input[index12:self._offset], index12, elements8)
                    self._offset = self._offset
                else:
                    address14 = FAILURE
                if address14 is not FAILURE:
                    elements5.append(address14)
                    address16 = FAILURE
                    address16 = self._read__or()
                    if address16 is not FAILURE:
                        elements5.append(address16)
                        address17 = FAILURE
                        index13, elements9, address18 = self._offset, [], None
                        while True:
                            address18 = self._read_WS()
                            if address18 is not FAILURE:
                                elements9.append(address18)
                            else:
                                break
                        if len(elements9) >= 1:
                            address17 = TreeNode(self._input[index13:self._offset], index13, elements9)
                            self._offset = self._offset
                        else:
                            address17 = FAILURE
                        if address17 is not FAILURE:
                            elements5.append(address17)
                        else:
                            elements5 = None
                            self._offset = index8
                    else:
                        elements5 = None
                        self._offset = index8
                else:
                    elements5 = None
                    self._offset = index8
            else:
                elements5 = None
                self._offset = index8
            if elements5 is None:
                address0 = FAILURE
            else:
                address0 = self._actions.and_or(self._input, index8, self._offset, elements5)
                self._offset = self._offset
            if address0 is FAILURE:
                self._offset = index1
                index14, elements10 = self._offset, []
                address19 = FAILURE
                index15, elements11, address20 = self._offset, [], None
                while True:
                    address20 = self._read_WS()
                    if address20 is not FAILURE:
                        elements11.append(address20)
                    else:
                        break
                if len(elements11) >= 0:
                    address19 = TreeNode(self._input[index15:self._offset], index15, elements11)
                    self._offset = self._offset
                else:
                    address19 = FAILURE
                if address19 is not FAILURE:
                    elements10.append(address19)
                    address21 = FAILURE
                    address21 = self._read_comma()
                    if address21 is not FAILURE:
                        elements10.append(address21)
                        address22 = FAILURE
                        index16, elements12, address23 = self._offset, [], None
                        while True:
                            address23 = self._read_WS()
                            if address23 is not FAILURE:
                                elements12.append(address23)
                            else:
                                break
                        if len(elements12) >= 0:
                            address22 = TreeNode(self._input[index16:self._offset], index16, elements12)
                            self._offset = self._offset
                        else:
                            address22 = FAILURE
                        if address22 is not FAILURE:
                            elements10.append(address22)
                        else:
                            elements10 = None
                            self._offset = index14
                    else:
                        elements10 = None
                        self._offset = index14
                else:
                    elements10 = None
                    self._offset = index14
                if elements10 is None:
                    address0 = FAILURE
                else:
                    address0 = self._actions.and_or(self._input, index14, self._offset, elements10)
                    self._offset = self._offset
                if address0 is FAILURE:
                    self._offset = index1
        self._cache['and_or'][index0] = (address0, self._offset)
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
            address0 = self._actions.of(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['of'][index0] = (address0, self._offset)
        return address0

    def _read__and(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['_and'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 3
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'and'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 3], self._offset, [])
            self._offset = self._offset + 3
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::_and', '`and`'))
        self._cache['_and'][index0] = (address0, self._offset)
        return address0

    def _read__or(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['_or'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'or'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::_or', '`or`'))
        self._cache['_or'][index0] = (address0, self._offset)
        return address0

    def _read_comma(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['comma'].get(index0)
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
                self._expected.append(('Refs::comma', '[,;]'))
        self._cache['comma'][index0] = (address0, self._offset)
        return address0

    def _read_to(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'to'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::to', '`to`'))
        self._cache['to'][index0] = (address0, self._offset)
        return address0

    def _read_unit(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['unit'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 7
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'section'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
            self._offset = self._offset + 7
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('Refs::unit', '`section`'))
        self._cache['unit'][index0] = (address0, self._offset)
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
        if chunk0 is not None and Grammar.REGEX_2.search(chunk0):
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
        if chunk0 is not None and Grammar.REGEX_3.search(chunk0):
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
