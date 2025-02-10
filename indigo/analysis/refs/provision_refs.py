# This file was generated from indigo/analysis/refs/provision_refs.peg
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
        self.references = elements[0]
        self.tail = elements[3]


class TreeNode2(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode2, self).__init__(text, offset, elements)
        self.to_and_or = elements[0]
        self.references = elements[1]


class TreeNode3(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode3, self).__init__(text, offset, elements)
        self.main_num = elements[2]


class TreeNode4(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode4, self).__init__(text, offset, elements)
        self.unit__i18n = elements[0]
        self.main_ref = elements[2]


class TreeNode5(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode5, self).__init__(text, offset, elements)
        self.to_and_or = elements[0]
        self.main_ref = elements[1]


class TreeNode6(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode6, self).__init__(text, offset, elements)
        self.sub_refs = elements[1]


class TreeNode7(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode7, self).__init__(text, offset, elements)
        self.digit = elements[0]


class TreeNode8(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode8, self).__init__(text, offset, elements)
        self.sub_ref = elements[0]


class TreeNode9(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode9, self).__init__(text, offset, elements)
        self.to_and_or = elements[0]
        self.sub_ref = elements[1]


class TreeNode10(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode10, self).__init__(text, offset, elements)
        self.num = elements[0]


class TreeNode11(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode11, self).__init__(text, offset, elements)
        self.num = elements[1]


class TreeNode12(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode12, self).__init__(text, offset, elements)
        self.to = elements[1]


class TreeNode13(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode13, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode14(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode14, self).__init__(text, offset, elements)
        self.dash = elements[1]


class TreeNode15(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode15, self).__init__(text, offset, elements)
        self.to__i18n = elements[1]


class TreeNode16(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode16, self).__init__(text, offset, elements)
        self.and__i18n = elements[2]


class TreeNode17(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode17, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode18(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode18, self).__init__(text, offset, elements)
        self.or__i18n = elements[2]


class TreeNode19(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode19, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode20(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode20, self).__init__(text, offset, elements)
        self.comma = elements[1]


class TreeNode21(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode21, self).__init__(text, offset, elements)
        self.of_this__i18n = elements[2]


class TreeNode22(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode22, self).__init__(text, offset, elements)
        self.of_the_act__i18n = elements[2]


class TreeNode23(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode23, self).__init__(text, offset, elements)
        self.of__i18n = elements[2]


class TreeNode24(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode24, self).__init__(text, offset, elements)
        self.thereof__i18n = elements[2]


class TreeNode25(TreeNode):
    def __init__(self, text, offset, elements):
        super(TreeNode25, self).__init__(text, offset, elements)
        self.of_that_act__i18n = elements[2]


FAILURE = object()


class Grammar(object):
    REGEX_1 = re.compile('^[a-zA-Z]')
    REGEX_2 = re.compile('^[,;]')
    REGEX_3 = re.compile('^[0-9]')
    REGEX_4 = re.compile('^[a-zA-Z0-9.-]')
    REGEX_5 = re.compile('^[a-zA-Z0-9-]')
    REGEX_6 = re.compile('^[a-zA-Z0-9]')

    def _read_root(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['root'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_references()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2, elements1, address3 = self._offset, [], None
            while True:
                index3, elements2 = self._offset, []
                address4 = FAILURE
                address4 = self._read_to_and_or()
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address5 = FAILURE
                    address5 = self._read_references()
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
                address6 = self._read_target()
                if address6 is FAILURE:
                    address6 = TreeNode(self._input[index4:index4], index4, [])
                    self._offset = index4
                if address6 is not FAILURE:
                    elements0.append(address6)
                    address7 = FAILURE
                    address7 = self._read_tail()
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
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.root(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['root'][index0] = (address0, self._offset)
        return address0

    def _read_references(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['references'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_attachment_ref()
        if address0 is FAILURE:
            self._offset = index1
            address0 = self._read_unit_refs()
            if address0 is FAILURE:
                self._offset = index1
        self._cache['references'][index0] = (address0, self._offset)
        return address0

    def _read_attachment_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['attachment_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_attachment_num_ref()
        if address0 is FAILURE:
            self._offset = index1
            address0 = self._read_the_attachment_ref()
            if address0 is FAILURE:
                self._offset = index1
        self._cache['attachment_ref'][index0] = (address0, self._offset)
        return address0

    def _read_attachment_num_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['attachment_num_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0, max0 = None, self._offset + 8
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == 'Schedule':
            address1 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
            self._offset = self._offset + 8
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::attachment_num_ref', '"Schedule"'))
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
                address4 = self._read_main_num()
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
            address0 = self._actions.attachment_num_ref(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['attachment_num_ref'][index0] = (address0, self._offset)
        return address0

    def _read_the_attachment_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['the_attachment_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0, max0 = None, self._offset + 12
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == 'the Schedule':
            address1 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
            self._offset = self._offset + 12
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::the_attachment_ref', '"the Schedule"'))
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index2 = self._offset
            chunk1, max1 = None, self._offset + 1
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and Grammar.REGEX_1.search(chunk1):
                address2 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                self._offset = self._offset + 1
            else:
                address2 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::the_attachment_ref', '[a-zA-Z]'))
            self._offset = index2
            if address2 is FAILURE:
                address2 = TreeNode(self._input[self._offset:self._offset], self._offset, [])
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
            address0 = self._actions.the_attachment_ref(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['the_attachment_ref'][index0] = (address0, self._offset)
        return address0

    def _read_unit_refs(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['unit_refs'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_unit__i18n()
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
                        index4, elements3 = self._offset, []
                        address7 = FAILURE
                        address7 = self._read_to_and_or()
                        if address7 is not FAILURE:
                            elements3.append(address7)
                            address8 = FAILURE
                            address8 = self._read_main_ref()
                            if address8 is not FAILURE:
                                elements3.append(address8)
                            else:
                                elements3 = None
                                self._offset = index4
                        else:
                            elements3 = None
                            self._offset = index4
                        if elements3 is None:
                            address6 = FAILURE
                        else:
                            address6 = TreeNode5(self._input[index4:self._offset], index4, elements3)
                            self._offset = self._offset
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
            address0 = self._actions.unit_refs(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['unit_refs'][index0] = (address0, self._offset)
        return address0

    def _read_main_ref(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['main_ref'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_main_num()
        if address1 is FAILURE:
            self._offset = index2
            address1 = self._read_num()
            if address1 is FAILURE:
                self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index3 = self._offset
            index4, elements1 = self._offset, []
            address3 = FAILURE
            index5, elements2, address4 = self._offset, [], None
            while True:
                address4 = self._read_WS()
                if address4 is not FAILURE:
                    elements2.append(address4)
                else:
                    break
            if len(elements2) >= 0:
                address3 = TreeNode(self._input[index5:self._offset], index5, elements2)
                self._offset = self._offset
            else:
                address3 = FAILURE
            if address3 is not FAILURE:
                elements1.append(address3)
                address5 = FAILURE
                address5 = self._read_sub_refs()
                if address5 is not FAILURE:
                    elements1.append(address5)
                else:
                    elements1 = None
                    self._offset = index4
            else:
                elements1 = None
                self._offset = index4
            if elements1 is None:
                address2 = FAILURE
            else:
                address2 = TreeNode6(self._input[index4:self._offset], index4, elements1)
                self._offset = self._offset
            if address2 is FAILURE:
                address2 = TreeNode(self._input[index3:index3], index3, [])
                self._offset = index3
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

    def _read_main_num(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['main_num'].get(index0)
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
                address3 = self._read_alpha_num_no_trailing_dot()
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
            address0 = self._actions.main_num(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['main_num'][index0] = (address0, self._offset)
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
                address4 = self._read_to_and_or()
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
                    address3 = TreeNode9(self._input[index3:self._offset], index3, elements2)
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
                    address3 = TreeNode11(self._input[index3:self._offset], index3, elements2)
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
                self._expected.append(('ProvisionRefs::num', '"("'))
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
                        self._expected.append(('ProvisionRefs::num', '")"'))
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

    def _read_to_and_or(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to_and_or'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_range()
        if address0 is FAILURE:
            self._offset = index1
            address0 = self._read_and_or()
            if address0 is FAILURE:
                self._offset = index1
        self._cache['to_and_or'][index0] = (address0, self._offset)
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
            address1 = TreeNode13(self._input[index3:self._offset], index3, elements1)
            self._offset = self._offset
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address5 = FAILURE
            address5 = self._read_to()
            if address5 is not FAILURE:
                elements0.append(address5)
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

    def _read_to(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        index2, elements0 = self._offset, []
        address1 = FAILURE
        index3, elements1, address2 = self._offset, [], None
        while True:
            address2 = self._read_WS()
            if address2 is not FAILURE:
                elements1.append(address2)
            else:
                break
        if len(elements1) >= 0:
            address1 = TreeNode(self._input[index3:self._offset], index3, elements1)
            self._offset = self._offset
        else:
            address1 = FAILURE
        if address1 is not FAILURE:
            elements0.append(address1)
            address3 = FAILURE
            address3 = self._read_dash()
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
                if len(elements2) >= 0:
                    address4 = TreeNode(self._input[index4:self._offset], index4, elements2)
                    self._offset = self._offset
                else:
                    address4 = FAILURE
                if address4 is not FAILURE:
                    elements0.append(address4)
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
            address0 = TreeNode14(self._input[index2:self._offset], index2, elements0)
            self._offset = self._offset
        if address0 is FAILURE:
            self._offset = index1
            index5, elements3 = self._offset, []
            address6 = FAILURE
            index6, elements4, address7 = self._offset, [], None
            while True:
                address7 = self._read_WS()
                if address7 is not FAILURE:
                    elements4.append(address7)
                else:
                    break
            if len(elements4) >= 1:
                address6 = TreeNode(self._input[index6:self._offset], index6, elements4)
                self._offset = self._offset
            else:
                address6 = FAILURE
            if address6 is not FAILURE:
                elements3.append(address6)
                address8 = FAILURE
                address8 = self._read_to__i18n()
                if address8 is not FAILURE:
                    elements3.append(address8)
                    address9 = FAILURE
                    index7, elements5, address10 = self._offset, [], None
                    while True:
                        address10 = self._read_WS()
                        if address10 is not FAILURE:
                            elements5.append(address10)
                        else:
                            break
                    if len(elements5) >= 1:
                        address9 = TreeNode(self._input[index7:self._offset], index7, elements5)
                        self._offset = self._offset
                    else:
                        address9 = FAILURE
                    if address9 is not FAILURE:
                        elements3.append(address9)
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
                address0 = FAILURE
            else:
                address0 = TreeNode15(self._input[index5:self._offset], index5, elements3)
                self._offset = self._offset
            if address0 is FAILURE:
                self._offset = index1
        self._cache['to'][index0] = (address0, self._offset)
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
            address1 = TreeNode17(self._input[index4:self._offset], index4, elements1)
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
            if len(elements3) >= 0:
                address5 = TreeNode(self._input[index6:self._offset], index6, elements3)
                self._offset = self._offset
            else:
                address5 = FAILURE
            if address5 is not FAILURE:
                elements0.append(address5)
                address7 = FAILURE
                address7 = self._read_and__i18n()
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
                address10 = TreeNode19(self._input[index10:self._offset], index10, elements6)
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
                if len(elements8) >= 0:
                    address14 = TreeNode(self._input[index12:self._offset], index12, elements8)
                    self._offset = self._offset
                else:
                    address14 = FAILURE
                if address14 is not FAILURE:
                    elements5.append(address14)
                    address16 = FAILURE
                    address16 = self._read_or__i18n()
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

    def _read_target(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['target'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_of_this()
        if address0 is FAILURE:
            self._offset = index1
            address0 = self._read_of_the_act()
            if address0 is FAILURE:
                self._offset = index1
                address0 = self._read_thereof()
                if address0 is FAILURE:
                    self._offset = index1
                    address0 = self._read_of_that_act()
                    if address0 is FAILURE:
                        self._offset = index1
                        address0 = self._read_of()
                        if address0 is FAILURE:
                            self._offset = index1
        self._cache['target'][index0] = (address0, self._offset)
        return address0

    def _read_of_this(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_this'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_comma()
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index3, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_WS()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index3:self._offset], index3, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                address4 = self._read_of_this__i18n()
                if address4 is not FAILURE:
                    elements0.append(address4)
                    address5 = FAILURE
                    index4, elements2, address6 = self._offset, [], None
                    while True:
                        address6 = self._read_WS()
                        if address6 is not FAILURE:
                            elements2.append(address6)
                        else:
                            break
                    if len(elements2) >= 1:
                        address5 = TreeNode(self._input[index4:self._offset], index4, elements2)
                        self._offset = self._offset
                    else:
                        address5 = FAILURE
                    if address5 is not FAILURE:
                        elements0.append(address5)
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
            address0 = self._actions.of_this(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['of_this'][index0] = (address0, self._offset)
        return address0

    def _read_of_the_act(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_the_act'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_comma()
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index3, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_WS()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index3:self._offset], index3, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                address4 = self._read_of_the_act__i18n()
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
            address0 = self._actions.of_the_act(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['of_the_act'][index0] = (address0, self._offset)
        return address0

    def _read_of(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_comma()
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index3, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_WS()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index3:self._offset], index3, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                address4 = self._read_of__i18n()
                if address4 is not FAILURE:
                    elements0.append(address4)
                    address5 = FAILURE
                    index4, elements2, address6 = self._offset, [], None
                    while True:
                        address6 = self._read_WS()
                        if address6 is not FAILURE:
                            elements2.append(address6)
                        else:
                            break
                    if len(elements2) >= 1:
                        address5 = TreeNode(self._input[index4:self._offset], index4, elements2)
                        self._offset = self._offset
                    else:
                        address5 = FAILURE
                    if address5 is not FAILURE:
                        elements0.append(address5)
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
            address0 = self._actions.of(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['of'][index0] = (address0, self._offset)
        return address0

    def _read_thereof(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['thereof'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_comma()
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index3, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_WS()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index3:self._offset], index3, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                address4 = self._read_thereof__i18n()
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
            address0 = self._actions.thereof(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['thereof'][index0] = (address0, self._offset)
        return address0

    def _read_of_that_act(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_that_act'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_comma()
        if address1 is FAILURE:
            address1 = TreeNode(self._input[index2:index2], index2, [])
            self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            index3, elements1, address3 = self._offset, [], None
            while True:
                address3 = self._read_WS()
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    break
            if len(elements1) >= 0:
                address2 = TreeNode(self._input[index3:self._offset], index3, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
                address4 = FAILURE
                address4 = self._read_of_that_act__i18n()
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
            address0 = self._actions.thereof(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['of_that_act'][index0] = (address0, self._offset)
        return address0

    def _read_tail(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['tail'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0, address1 = self._offset, [], None
        while True:
            if self._offset < self._input_size:
                address1 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                self._offset = self._offset + 1
            else:
                address1 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::tail', '<any char>'))
            if address1 is not FAILURE:
                elements0.append(address1)
            else:
                break
        if len(elements0) >= 0:
            address0 = TreeNode(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache['tail'][index0] = (address0, self._offset)
        return address0

    def _read_and__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['and__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::and__i18n', '""'))
        self._cache['and__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_of__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of__i18n', '""'))
        self._cache['of__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_of_the_act__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_the_act__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_the_act__i18n', '""'))
        self._cache['of_the_act__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_of_that_act__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_that_act__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_that_act__i18n', '""'))
        self._cache['of_that_act__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_of_this__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_this__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_this__i18n', '""'))
        self._cache['of_this__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_or__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['or__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::or__i18n', '""'))
        self._cache['or__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_thereof__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['thereof__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::thereof__i18n', '""'))
        self._cache['thereof__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_to__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::to__i18n', '""'))
        self._cache['to__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_unit__i18n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['unit__i18n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 0
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 == '':
            address0 = TreeNode(self._input[self._offset:self._offset + 0], self._offset, [])
            self._offset = self._offset + 0
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::unit__i18n', '""'))
        self._cache['unit__i18n'][index0] = (address0, self._offset)
        return address0

    def _read_unit_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['unit_eng'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 8
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'articles'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
            self._offset = self._offset + 8
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::unit_eng', '`articles`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 7
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'article'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                self._offset = self._offset + 7
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::unit_eng', '`article`'))
            if address0 is FAILURE:
                self._offset = index1
                chunk2, max2 = None, self._offset + 8
                if max2 <= self._input_size:
                    chunk2 = self._input[self._offset:max2]
                if chunk2 is not None and chunk2.lower() == 'chapters'.lower():
                    address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                    self._offset = self._offset + 8
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('ProvisionRefs::unit_eng', '`chapters`'))
                if address0 is FAILURE:
                    self._offset = index1
                    chunk3, max3 = None, self._offset + 7
                    if max3 <= self._input_size:
                        chunk3 = self._input[self._offset:max3]
                    if chunk3 is not None and chunk3.lower() == 'chapter'.lower():
                        address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                        self._offset = self._offset + 7
                    else:
                        address0 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append(('ProvisionRefs::unit_eng', '`chapter`'))
                    if address0 is FAILURE:
                        self._offset = index1
                        chunk4, max4 = None, self._offset + 5
                        if max4 <= self._input_size:
                            chunk4 = self._input[self._offset:max4]
                        if chunk4 is not None and chunk4.lower() == 'items'.lower():
                            address0 = TreeNode(self._input[self._offset:self._offset + 5], self._offset, [])
                            self._offset = self._offset + 5
                        else:
                            address0 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append(('ProvisionRefs::unit_eng', '`items`'))
                        if address0 is FAILURE:
                            self._offset = index1
                            chunk5, max5 = None, self._offset + 4
                            if max5 <= self._input_size:
                                chunk5 = self._input[self._offset:max5]
                            if chunk5 is not None and chunk5.lower() == 'item'.lower():
                                address0 = TreeNode(self._input[self._offset:self._offset + 4], self._offset, [])
                                self._offset = self._offset + 4
                            else:
                                address0 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append(('ProvisionRefs::unit_eng', '`item`'))
                            if address0 is FAILURE:
                                self._offset = index1
                                chunk6, max6 = None, self._offset + 10
                                if max6 <= self._input_size:
                                    chunk6 = self._input[self._offset:max6]
                                if chunk6 is not None and chunk6.lower() == 'paragraphs'.lower():
                                    address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                    self._offset = self._offset + 10
                                else:
                                    address0 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append(('ProvisionRefs::unit_eng', '`paragraphs`'))
                                if address0 is FAILURE:
                                    self._offset = index1
                                    chunk7, max7 = None, self._offset + 9
                                    if max7 <= self._input_size:
                                        chunk7 = self._input[self._offset:max7]
                                    if chunk7 is not None and chunk7.lower() == 'paragraph'.lower():
                                        address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                                        self._offset = self._offset + 9
                                    else:
                                        address0 = FAILURE
                                        if self._offset > self._failure:
                                            self._failure = self._offset
                                            self._expected = []
                                        if self._offset == self._failure:
                                            self._expected.append(('ProvisionRefs::unit_eng', '`paragraph`'))
                                    if address0 is FAILURE:
                                        self._offset = index1
                                        chunk8, max8 = None, self._offset + 5
                                        if max8 <= self._input_size:
                                            chunk8 = self._input[self._offset:max8]
                                        if chunk8 is not None and chunk8.lower() == 'parts'.lower():
                                            address0 = TreeNode(self._input[self._offset:self._offset + 5], self._offset, [])
                                            self._offset = self._offset + 5
                                        else:
                                            address0 = FAILURE
                                            if self._offset > self._failure:
                                                self._failure = self._offset
                                                self._expected = []
                                            if self._offset == self._failure:
                                                self._expected.append(('ProvisionRefs::unit_eng', '`parts`'))
                                        if address0 is FAILURE:
                                            self._offset = index1
                                            chunk9, max9 = None, self._offset + 4
                                            if max9 <= self._input_size:
                                                chunk9 = self._input[self._offset:max9]
                                            if chunk9 is not None and chunk9.lower() == 'part'.lower():
                                                address0 = TreeNode(self._input[self._offset:self._offset + 4], self._offset, [])
                                                self._offset = self._offset + 4
                                            else:
                                                address0 = FAILURE
                                                if self._offset > self._failure:
                                                    self._failure = self._offset
                                                    self._expected = []
                                                if self._offset == self._failure:
                                                    self._expected.append(('ProvisionRefs::unit_eng', '`part`'))
                                            if address0 is FAILURE:
                                                self._offset = index1
                                                chunk10, max10 = None, self._offset + 6
                                                if max10 <= self._input_size:
                                                    chunk10 = self._input[self._offset:max10]
                                                if chunk10 is not None and chunk10.lower() == 'points'.lower():
                                                    address0 = TreeNode(self._input[self._offset:self._offset + 6], self._offset, [])
                                                    self._offset = self._offset + 6
                                                else:
                                                    address0 = FAILURE
                                                    if self._offset > self._failure:
                                                        self._failure = self._offset
                                                        self._expected = []
                                                    if self._offset == self._failure:
                                                        self._expected.append(('ProvisionRefs::unit_eng', '`points`'))
                                                if address0 is FAILURE:
                                                    self._offset = index1
                                                    chunk11, max11 = None, self._offset + 5
                                                    if max11 <= self._input_size:
                                                        chunk11 = self._input[self._offset:max11]
                                                    if chunk11 is not None and chunk11.lower() == 'point'.lower():
                                                        address0 = TreeNode(self._input[self._offset:self._offset + 5], self._offset, [])
                                                        self._offset = self._offset + 5
                                                    else:
                                                        address0 = FAILURE
                                                        if self._offset > self._failure:
                                                            self._failure = self._offset
                                                            self._expected = []
                                                        if self._offset == self._failure:
                                                            self._expected.append(('ProvisionRefs::unit_eng', '`point`'))
                                                    if address0 is FAILURE:
                                                        self._offset = index1
                                                        chunk12, max12 = None, self._offset + 11
                                                        if max12 <= self._input_size:
                                                            chunk12 = self._input[self._offset:max12]
                                                        if chunk12 is not None and chunk12.lower() == 'regulations'.lower():
                                                            address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                                                            self._offset = self._offset + 11
                                                        else:
                                                            address0 = FAILURE
                                                            if self._offset > self._failure:
                                                                self._failure = self._offset
                                                                self._expected = []
                                                            if self._offset == self._failure:
                                                                self._expected.append(('ProvisionRefs::unit_eng', '`regulations`'))
                                                        if address0 is FAILURE:
                                                            self._offset = index1
                                                            chunk13, max13 = None, self._offset + 10
                                                            if max13 <= self._input_size:
                                                                chunk13 = self._input[self._offset:max13]
                                                            if chunk13 is not None and chunk13.lower() == 'regulation'.lower():
                                                                address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                                                self._offset = self._offset + 10
                                                            else:
                                                                address0 = FAILURE
                                                                if self._offset > self._failure:
                                                                    self._failure = self._offset
                                                                    self._expected = []
                                                                if self._offset == self._failure:
                                                                    self._expected.append(('ProvisionRefs::unit_eng', '`regulation`'))
                                                            if address0 is FAILURE:
                                                                self._offset = index1
                                                                chunk14, max14 = None, self._offset + 8
                                                                if max14 <= self._input_size:
                                                                    chunk14 = self._input[self._offset:max14]
                                                                if chunk14 is not None and chunk14.lower() == 'sections'.lower():
                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                                                                    self._offset = self._offset + 8
                                                                else:
                                                                    address0 = FAILURE
                                                                    if self._offset > self._failure:
                                                                        self._failure = self._offset
                                                                        self._expected = []
                                                                    if self._offset == self._failure:
                                                                        self._expected.append(('ProvisionRefs::unit_eng', '`sections`'))
                                                                if address0 is FAILURE:
                                                                    self._offset = index1
                                                                    chunk15, max15 = None, self._offset + 7
                                                                    if max15 <= self._input_size:
                                                                        chunk15 = self._input[self._offset:max15]
                                                                    if chunk15 is not None and chunk15.lower() == 'section'.lower():
                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                                                                        self._offset = self._offset + 7
                                                                    else:
                                                                        address0 = FAILURE
                                                                        if self._offset > self._failure:
                                                                            self._failure = self._offset
                                                                            self._expected = []
                                                                        if self._offset == self._failure:
                                                                            self._expected.append(('ProvisionRefs::unit_eng', '`section`'))
                                                                    if address0 is FAILURE:
                                                                        self._offset = index1
                                                                        chunk16, max16 = None, self._offset + 13
                                                                        if max16 <= self._input_size:
                                                                            chunk16 = self._input[self._offset:max16]
                                                                        if chunk16 is not None and chunk16.lower() == 'subparagraphs'.lower():
                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 13], self._offset, [])
                                                                            self._offset = self._offset + 13
                                                                        else:
                                                                            address0 = FAILURE
                                                                            if self._offset > self._failure:
                                                                                self._failure = self._offset
                                                                                self._expected = []
                                                                            if self._offset == self._failure:
                                                                                self._expected.append(('ProvisionRefs::unit_eng', '`subparagraphs`'))
                                                                        if address0 is FAILURE:
                                                                            self._offset = index1
                                                                            chunk17, max17 = None, self._offset + 12
                                                                            if max17 <= self._input_size:
                                                                                chunk17 = self._input[self._offset:max17]
                                                                            if chunk17 is not None and chunk17.lower() == 'subparagraph'.lower():
                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                                                self._offset = self._offset + 12
                                                                            else:
                                                                                address0 = FAILURE
                                                                                if self._offset > self._failure:
                                                                                    self._failure = self._offset
                                                                                    self._expected = []
                                                                                if self._offset == self._failure:
                                                                                    self._expected.append(('ProvisionRefs::unit_eng', '`subparagraph`'))
                                                                            if address0 is FAILURE:
                                                                                self._offset = index1
                                                                                chunk18, max18 = None, self._offset + 14
                                                                                if max18 <= self._input_size:
                                                                                    chunk18 = self._input[self._offset:max18]
                                                                                if chunk18 is not None and chunk18.lower() == 'sub-paragraphs'.lower():
                                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                    self._offset = self._offset + 14
                                                                                else:
                                                                                    address0 = FAILURE
                                                                                    if self._offset > self._failure:
                                                                                        self._failure = self._offset
                                                                                        self._expected = []
                                                                                    if self._offset == self._failure:
                                                                                        self._expected.append(('ProvisionRefs::unit_eng', '`sub-paragraphs`'))
                                                                                if address0 is FAILURE:
                                                                                    self._offset = index1
                                                                                    chunk19, max19 = None, self._offset + 13
                                                                                    if max19 <= self._input_size:
                                                                                        chunk19 = self._input[self._offset:max19]
                                                                                    if chunk19 is not None and chunk19.lower() == 'sub-paragraph'.lower():
                                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 13], self._offset, [])
                                                                                        self._offset = self._offset + 13
                                                                                    else:
                                                                                        address0 = FAILURE
                                                                                        if self._offset > self._failure:
                                                                                            self._failure = self._offset
                                                                                            self._expected = []
                                                                                        if self._offset == self._failure:
                                                                                            self._expected.append(('ProvisionRefs::unit_eng', '`sub-paragraph`'))
                                                                                    if address0 is FAILURE:
                                                                                        self._offset = index1
                                                                                        chunk20, max20 = None, self._offset + 14
                                                                                        if max20 <= self._input_size:
                                                                                            chunk20 = self._input[self._offset:max20]
                                                                                        if chunk20 is not None and chunk20.lower() == 'sub paragraphs'.lower():
                                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                            self._offset = self._offset + 14
                                                                                        else:
                                                                                            address0 = FAILURE
                                                                                            if self._offset > self._failure:
                                                                                                self._failure = self._offset
                                                                                                self._expected = []
                                                                                            if self._offset == self._failure:
                                                                                                self._expected.append(('ProvisionRefs::unit_eng', '`sub paragraphs`'))
                                                                                        if address0 is FAILURE:
                                                                                            self._offset = index1
                                                                                            chunk21, max21 = None, self._offset + 13
                                                                                            if max21 <= self._input_size:
                                                                                                chunk21 = self._input[self._offset:max21]
                                                                                            if chunk21 is not None and chunk21.lower() == 'sub paragraph'.lower():
                                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 13], self._offset, [])
                                                                                                self._offset = self._offset + 13
                                                                                            else:
                                                                                                address0 = FAILURE
                                                                                                if self._offset > self._failure:
                                                                                                    self._failure = self._offset
                                                                                                    self._expected = []
                                                                                                if self._offset == self._failure:
                                                                                                    self._expected.append(('ProvisionRefs::unit_eng', '`sub paragraph`'))
                                                                                            if address0 is FAILURE:
                                                                                                self._offset = index1
                                                                                                chunk22, max22 = None, self._offset + 14
                                                                                                if max22 <= self._input_size:
                                                                                                    chunk22 = self._input[self._offset:max22]
                                                                                                if chunk22 is not None and chunk22.lower() == 'subregulations'.lower():
                                                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                                    self._offset = self._offset + 14
                                                                                                else:
                                                                                                    address0 = FAILURE
                                                                                                    if self._offset > self._failure:
                                                                                                        self._failure = self._offset
                                                                                                        self._expected = []
                                                                                                    if self._offset == self._failure:
                                                                                                        self._expected.append(('ProvisionRefs::unit_eng', '`subregulations`'))
                                                                                                if address0 is FAILURE:
                                                                                                    self._offset = index1
                                                                                                    chunk23, max23 = None, self._offset + 13
                                                                                                    if max23 <= self._input_size:
                                                                                                        chunk23 = self._input[self._offset:max23]
                                                                                                    if chunk23 is not None and chunk23.lower() == 'subregulation'.lower():
                                                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 13], self._offset, [])
                                                                                                        self._offset = self._offset + 13
                                                                                                    else:
                                                                                                        address0 = FAILURE
                                                                                                        if self._offset > self._failure:
                                                                                                            self._failure = self._offset
                                                                                                            self._expected = []
                                                                                                        if self._offset == self._failure:
                                                                                                            self._expected.append(('ProvisionRefs::unit_eng', '`subregulation`'))
                                                                                                    if address0 is FAILURE:
                                                                                                        self._offset = index1
                                                                                                        chunk24, max24 = None, self._offset + 15
                                                                                                        if max24 <= self._input_size:
                                                                                                            chunk24 = self._input[self._offset:max24]
                                                                                                        if chunk24 is not None and chunk24.lower() == 'sub-regulations'.lower():
                                                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
                                                                                                            self._offset = self._offset + 15
                                                                                                        else:
                                                                                                            address0 = FAILURE
                                                                                                            if self._offset > self._failure:
                                                                                                                self._failure = self._offset
                                                                                                                self._expected = []
                                                                                                            if self._offset == self._failure:
                                                                                                                self._expected.append(('ProvisionRefs::unit_eng', '`sub-regulations`'))
                                                                                                        if address0 is FAILURE:
                                                                                                            self._offset = index1
                                                                                                            chunk25, max25 = None, self._offset + 14
                                                                                                            if max25 <= self._input_size:
                                                                                                                chunk25 = self._input[self._offset:max25]
                                                                                                            if chunk25 is not None and chunk25.lower() == 'sub-regulation'.lower():
                                                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                                                self._offset = self._offset + 14
                                                                                                            else:
                                                                                                                address0 = FAILURE
                                                                                                                if self._offset > self._failure:
                                                                                                                    self._failure = self._offset
                                                                                                                    self._expected = []
                                                                                                                if self._offset == self._failure:
                                                                                                                    self._expected.append(('ProvisionRefs::unit_eng', '`sub-regulation`'))
                                                                                                            if address0 is FAILURE:
                                                                                                                self._offset = index1
                                                                                                                chunk26, max26 = None, self._offset + 15
                                                                                                                if max26 <= self._input_size:
                                                                                                                    chunk26 = self._input[self._offset:max26]
                                                                                                                if chunk26 is not None and chunk26.lower() == 'sub regulations'.lower():
                                                                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
                                                                                                                    self._offset = self._offset + 15
                                                                                                                else:
                                                                                                                    address0 = FAILURE
                                                                                                                    if self._offset > self._failure:
                                                                                                                        self._failure = self._offset
                                                                                                                        self._expected = []
                                                                                                                    if self._offset == self._failure:
                                                                                                                        self._expected.append(('ProvisionRefs::unit_eng', '`sub regulations`'))
                                                                                                                if address0 is FAILURE:
                                                                                                                    self._offset = index1
                                                                                                                    chunk27, max27 = None, self._offset + 14
                                                                                                                    if max27 <= self._input_size:
                                                                                                                        chunk27 = self._input[self._offset:max27]
                                                                                                                    if chunk27 is not None and chunk27.lower() == 'sub regulation'.lower():
                                                                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                                                        self._offset = self._offset + 14
                                                                                                                    else:
                                                                                                                        address0 = FAILURE
                                                                                                                        if self._offset > self._failure:
                                                                                                                            self._failure = self._offset
                                                                                                                            self._expected = []
                                                                                                                        if self._offset == self._failure:
                                                                                                                            self._expected.append(('ProvisionRefs::unit_eng', '`sub regulation`'))
                                                                                                                    if address0 is FAILURE:
                                                                                                                        self._offset = index1
                                                                                                                        chunk28, max28 = None, self._offset + 11
                                                                                                                        if max28 <= self._input_size:
                                                                                                                            chunk28 = self._input[self._offset:max28]
                                                                                                                        if chunk28 is not None and chunk28.lower() == 'subsections'.lower():
                                                                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                                                                                                                            self._offset = self._offset + 11
                                                                                                                        else:
                                                                                                                            address0 = FAILURE
                                                                                                                            if self._offset > self._failure:
                                                                                                                                self._failure = self._offset
                                                                                                                                self._expected = []
                                                                                                                            if self._offset == self._failure:
                                                                                                                                self._expected.append(('ProvisionRefs::unit_eng', '`subsections`'))
                                                                                                                        if address0 is FAILURE:
                                                                                                                            self._offset = index1
                                                                                                                            chunk29, max29 = None, self._offset + 10
                                                                                                                            if max29 <= self._input_size:
                                                                                                                                chunk29 = self._input[self._offset:max29]
                                                                                                                            if chunk29 is not None and chunk29.lower() == 'subsection'.lower():
                                                                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                                                                                                                self._offset = self._offset + 10
                                                                                                                            else:
                                                                                                                                address0 = FAILURE
                                                                                                                                if self._offset > self._failure:
                                                                                                                                    self._failure = self._offset
                                                                                                                                    self._expected = []
                                                                                                                                if self._offset == self._failure:
                                                                                                                                    self._expected.append(('ProvisionRefs::unit_eng', '`subsection`'))
                                                                                                                            if address0 is FAILURE:
                                                                                                                                self._offset = index1
                                                                                                                                chunk30, max30 = None, self._offset + 12
                                                                                                                                if max30 <= self._input_size:
                                                                                                                                    chunk30 = self._input[self._offset:max30]
                                                                                                                                if chunk30 is not None and chunk30.lower() == 'sub-sections'.lower():
                                                                                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                                                                                                    self._offset = self._offset + 12
                                                                                                                                else:
                                                                                                                                    address0 = FAILURE
                                                                                                                                    if self._offset > self._failure:
                                                                                                                                        self._failure = self._offset
                                                                                                                                        self._expected = []
                                                                                                                                    if self._offset == self._failure:
                                                                                                                                        self._expected.append(('ProvisionRefs::unit_eng', '`sub-sections`'))
                                                                                                                                if address0 is FAILURE:
                                                                                                                                    self._offset = index1
                                                                                                                                    chunk31, max31 = None, self._offset + 11
                                                                                                                                    if max31 <= self._input_size:
                                                                                                                                        chunk31 = self._input[self._offset:max31]
                                                                                                                                    if chunk31 is not None and chunk31.lower() == 'sub-section'.lower():
                                                                                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                                                                                                                                        self._offset = self._offset + 11
                                                                                                                                    else:
                                                                                                                                        address0 = FAILURE
                                                                                                                                        if self._offset > self._failure:
                                                                                                                                            self._failure = self._offset
                                                                                                                                            self._expected = []
                                                                                                                                        if self._offset == self._failure:
                                                                                                                                            self._expected.append(('ProvisionRefs::unit_eng', '`sub-section`'))
                                                                                                                                    if address0 is FAILURE:
                                                                                                                                        self._offset = index1
                                                                                                                                        chunk32, max32 = None, self._offset + 12
                                                                                                                                        if max32 <= self._input_size:
                                                                                                                                            chunk32 = self._input[self._offset:max32]
                                                                                                                                        if chunk32 is not None and chunk32.lower() == 'sub sections'.lower():
                                                                                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                                                                                                            self._offset = self._offset + 12
                                                                                                                                        else:
                                                                                                                                            address0 = FAILURE
                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                self._failure = self._offset
                                                                                                                                                self._expected = []
                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                self._expected.append(('ProvisionRefs::unit_eng', '`sub sections`'))
                                                                                                                                        if address0 is FAILURE:
                                                                                                                                            self._offset = index1
                                                                                                                                            chunk33, max33 = None, self._offset + 11
                                                                                                                                            if max33 <= self._input_size:
                                                                                                                                                chunk33 = self._input[self._offset:max33]
                                                                                                                                            if chunk33 is not None and chunk33.lower() == 'sub section'.lower():
                                                                                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                                                                                                                                                self._offset = self._offset + 11
                                                                                                                                            else:
                                                                                                                                                address0 = FAILURE
                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                    self._failure = self._offset
                                                                                                                                                    self._expected = []
                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                    self._expected.append(('ProvisionRefs::unit_eng', '`sub section`'))
                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                self._offset = index1
        self._cache['unit_eng'][index0] = (address0, self._offset)
        return address0

    def _read_unit_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['unit_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 9
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'afdelings'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
            self._offset = self._offset + 9
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::unit_afr', '`afdelings`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 8
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'afdeling'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                self._offset = self._offset + 8
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::unit_afr', '`afdeling`'))
            if address0 is FAILURE:
                self._offset = index1
                chunk2, max2 = None, self._offset + 8
                if max2 <= self._input_size:
                    chunk2 = self._input[self._offset:max2]
                if chunk2 is not None and chunk2.lower() == 'artikels'.lower():
                    address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                    self._offset = self._offset + 8
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('ProvisionRefs::unit_afr', '`artikels`'))
                if address0 is FAILURE:
                    self._offset = index1
                    index2, elements0 = self._offset, []
                    address1 = FAILURE
                    chunk3, max3 = None, self._offset + 7
                    if max3 <= self._input_size:
                        chunk3 = self._input[self._offset:max3]
                    if chunk3 is not None and chunk3.lower() == 'artikel'.lower():
                        address1 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                        self._offset = self._offset + 7
                    else:
                        address1 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append(('ProvisionRefs::unit_afr', '`artikel`'))
                    if address1 is not FAILURE:
                        elements0.append(address1)
                        address2 = FAILURE
                        chunk4, max4 = None, self._offset + 4
                        if max4 <= self._input_size:
                            chunk4 = self._input[self._offset:max4]
                        if chunk4 is not None and chunk4.lower() == 'dele'.lower():
                            address2 = TreeNode(self._input[self._offset:self._offset + 4], self._offset, [])
                            self._offset = self._offset + 4
                        else:
                            address2 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append(('ProvisionRefs::unit_afr', '`dele`'))
                        if address2 is not FAILURE:
                            elements0.append(address2)
                        else:
                            elements0 = None
                            self._offset = index2
                    else:
                        elements0 = None
                        self._offset = index2
                    if elements0 is None:
                        address0 = FAILURE
                    else:
                        address0 = TreeNode(self._input[index2:self._offset], index2, elements0)
                        self._offset = self._offset
                    if address0 is FAILURE:
                        self._offset = index1
                        index3, elements1 = self._offset, []
                        address3 = FAILURE
                        chunk5, max5 = None, self._offset + 4
                        if max5 <= self._input_size:
                            chunk5 = self._input[self._offset:max5]
                        if chunk5 is not None and chunk5.lower() == 'deel'.lower():
                            address3 = TreeNode(self._input[self._offset:self._offset + 4], self._offset, [])
                            self._offset = self._offset + 4
                        else:
                            address3 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append(('ProvisionRefs::unit_afr', '`deel`'))
                        if address3 is not FAILURE:
                            elements1.append(address3)
                            address4 = FAILURE
                            chunk6, max6 = None, self._offset + 10
                            if max6 <= self._input_size:
                                chunk6 = self._input[self._offset:max6]
                            if chunk6 is not None and chunk6.lower() == 'hoofstukke'.lower():
                                address4 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                self._offset = self._offset + 10
                            else:
                                address4 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append(('ProvisionRefs::unit_afr', '`hoofstukke`'))
                            if address4 is not FAILURE:
                                elements1.append(address4)
                            else:
                                elements1 = None
                                self._offset = index3
                        else:
                            elements1 = None
                            self._offset = index3
                        if elements1 is None:
                            address0 = FAILURE
                        else:
                            address0 = TreeNode(self._input[index3:self._offset], index3, elements1)
                            self._offset = self._offset
                        if address0 is FAILURE:
                            self._offset = index1
                            chunk7, max7 = None, self._offset + 8
                            if max7 <= self._input_size:
                                chunk7 = self._input[self._offset:max7]
                            if chunk7 is not None and chunk7.lower() == 'hoofstuk'.lower():
                                address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                                self._offset = self._offset + 8
                            else:
                                address0 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append(('ProvisionRefs::unit_afr', '`hoofstuk`'))
                            if address0 is FAILURE:
                                self._offset = index1
                                chunk8, max8 = None, self._offset + 9
                                if max8 <= self._input_size:
                                    chunk8 = self._input[self._offset:max8]
                                if chunk8 is not None and chunk8.lower() == 'paragrawe'.lower():
                                    address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                                    self._offset = self._offset + 9
                                else:
                                    address0 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append(('ProvisionRefs::unit_afr', '`paragrawe`'))
                                if address0 is FAILURE:
                                    self._offset = index1
                                    chunk9, max9 = None, self._offset + 9
                                    if max9 <= self._input_size:
                                        chunk9 = self._input[self._offset:max9]
                                    if chunk9 is not None and chunk9.lower() == 'paragraaf'.lower():
                                        address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                                        self._offset = self._offset + 9
                                    else:
                                        address0 = FAILURE
                                        if self._offset > self._failure:
                                            self._failure = self._offset
                                            self._expected = []
                                        if self._offset == self._failure:
                                            self._expected.append(('ProvisionRefs::unit_afr', '`paragraaf`'))
                                    if address0 is FAILURE:
                                        self._offset = index1
                                        chunk10, max10 = None, self._offset + 5
                                        if max10 <= self._input_size:
                                            chunk10 = self._input[self._offset:max10]
                                        if chunk10 is not None and chunk10.lower() == 'punte'.lower():
                                            address0 = TreeNode(self._input[self._offset:self._offset + 5], self._offset, [])
                                            self._offset = self._offset + 5
                                        else:
                                            address0 = FAILURE
                                            if self._offset > self._failure:
                                                self._failure = self._offset
                                                self._expected = []
                                            if self._offset == self._failure:
                                                self._expected.append(('ProvisionRefs::unit_afr', '`punte`'))
                                        if address0 is FAILURE:
                                            self._offset = index1
                                            chunk11, max11 = None, self._offset + 4
                                            if max11 <= self._input_size:
                                                chunk11 = self._input[self._offset:max11]
                                            if chunk11 is not None and chunk11.lower() == 'punt'.lower():
                                                address0 = TreeNode(self._input[self._offset:self._offset + 4], self._offset, [])
                                                self._offset = self._offset + 4
                                            else:
                                                address0 = FAILURE
                                                if self._offset > self._failure:
                                                    self._failure = self._offset
                                                    self._expected = []
                                                if self._offset == self._failure:
                                                    self._expected.append(('ProvisionRefs::unit_afr', '`punt`'))
                                            if address0 is FAILURE:
                                                self._offset = index1
                                                chunk12, max12 = None, self._offset + 12
                                                if max12 <= self._input_size:
                                                    chunk12 = self._input[self._offset:max12]
                                                if chunk12 is not None and chunk12.lower() == 'subafdelings'.lower():
                                                    address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                    self._offset = self._offset + 12
                                                else:
                                                    address0 = FAILURE
                                                    if self._offset > self._failure:
                                                        self._failure = self._offset
                                                        self._expected = []
                                                    if self._offset == self._failure:
                                                        self._expected.append(('ProvisionRefs::unit_afr', '`subafdelings`'))
                                                if address0 is FAILURE:
                                                    self._offset = index1
                                                    chunk13, max13 = None, self._offset + 11
                                                    if max13 <= self._input_size:
                                                        chunk13 = self._input[self._offset:max13]
                                                    if chunk13 is not None and chunk13.lower() == 'subafdeling'.lower():
                                                        address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                                                        self._offset = self._offset + 11
                                                    else:
                                                        address0 = FAILURE
                                                        if self._offset > self._failure:
                                                            self._failure = self._offset
                                                            self._expected = []
                                                        if self._offset == self._failure:
                                                            self._expected.append(('ProvisionRefs::unit_afr', '`subafdeling`'))
                                                    if address0 is FAILURE:
                                                        self._offset = index1
                                                        chunk14, max14 = None, self._offset + 12
                                                        if max14 <= self._input_size:
                                                            chunk14 = self._input[self._offset:max14]
                                                        if chunk14 is not None and chunk14.lower() == 'subparagrawe'.lower():
                                                            address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                            self._offset = self._offset + 12
                                                        else:
                                                            address0 = FAILURE
                                                            if self._offset > self._failure:
                                                                self._failure = self._offset
                                                                self._expected = []
                                                            if self._offset == self._failure:
                                                                self._expected.append(('ProvisionRefs::unit_afr', '`subparagrawe`'))
                                                        if address0 is FAILURE:
                                                            self._offset = index1
                                                            chunk15, max15 = None, self._offset + 12
                                                            if max15 <= self._input_size:
                                                                chunk15 = self._input[self._offset:max15]
                                                            if chunk15 is not None and chunk15.lower() == 'subparagraaf'.lower():
                                                                address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                                self._offset = self._offset + 12
                                                            else:
                                                                address0 = FAILURE
                                                                if self._offset > self._failure:
                                                                    self._failure = self._offset
                                                                    self._expected = []
                                                                if self._offset == self._failure:
                                                                    self._expected.append(('ProvisionRefs::unit_afr', '`subparagraaf`'))
                                                            if address0 is FAILURE:
                                                                self._offset = index1
        self._cache['unit_afr'][index0] = (address0, self._offset)
        return address0

    def _read_unit_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['unit_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 8
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'articles'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
            self._offset = self._offset + 8
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::unit_fra', '`articles`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 7
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'article'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                self._offset = self._offset + 7
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::unit_fra', '`article`'))
            if address0 is FAILURE:
                self._offset = index1
                chunk2, max2 = None, self._offset + 9
                if max2 <= self._input_size:
                    chunk2 = self._input[self._offset:max2]
                if chunk2 is not None and chunk2.lower() == 'chapitres'.lower():
                    address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                    self._offset = self._offset + 9
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('ProvisionRefs::unit_fra', '`chapitres`'))
                if address0 is FAILURE:
                    self._offset = index1
                    chunk3, max3 = None, self._offset + 8
                    if max3 <= self._input_size:
                        chunk3 = self._input[self._offset:max3]
                    if chunk3 is not None and chunk3.lower() == 'chapitre'.lower():
                        address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                        self._offset = self._offset + 8
                    else:
                        address0 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append(('ProvisionRefs::unit_fra', '`chapitre`'))
                    if address0 is FAILURE:
                        self._offset = index1
                        chunk4, max4 = None, self._offset + 11
                        if max4 <= self._input_size:
                            chunk4 = self._input[self._offset:max4]
                        if chunk4 is not None and chunk4.lower() == 'paragraphes'.lower():
                            address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                            self._offset = self._offset + 11
                        else:
                            address0 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append(('ProvisionRefs::unit_fra', '`paragraphes`'))
                        if address0 is FAILURE:
                            self._offset = index1
                            chunk5, max5 = None, self._offset + 10
                            if max5 <= self._input_size:
                                chunk5 = self._input[self._offset:max5]
                            if chunk5 is not None and chunk5.lower() == 'paragraphe'.lower():
                                address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                self._offset = self._offset + 10
                            else:
                                address0 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append(('ProvisionRefs::unit_fra', '`paragraphe`'))
                            if address0 is FAILURE:
                                self._offset = index1
                                chunk6, max6 = None, self._offset + 7
                                if max6 <= self._input_size:
                                    chunk6 = self._input[self._offset:max6]
                                if chunk6 is not None and chunk6.lower() == 'parties'.lower():
                                    address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                                    self._offset = self._offset + 7
                                else:
                                    address0 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append(('ProvisionRefs::unit_fra', '`parties`'))
                                if address0 is FAILURE:
                                    self._offset = index1
                                    chunk7, max7 = None, self._offset + 6
                                    if max7 <= self._input_size:
                                        chunk7 = self._input[self._offset:max7]
                                    if chunk7 is not None and chunk7.lower() == 'partie'.lower():
                                        address0 = TreeNode(self._input[self._offset:self._offset + 6], self._offset, [])
                                        self._offset = self._offset + 6
                                    else:
                                        address0 = FAILURE
                                        if self._offset > self._failure:
                                            self._failure = self._offset
                                            self._expected = []
                                        if self._offset == self._failure:
                                            self._expected.append(('ProvisionRefs::unit_fra', '`partie`'))
                                    if address0 is FAILURE:
                                        self._offset = index1
                                        chunk8, max8 = None, self._offset + 6
                                        if max8 <= self._input_size:
                                            chunk8 = self._input[self._offset:max8]
                                        if chunk8 is not None and chunk8.lower() == 'points'.lower():
                                            address0 = TreeNode(self._input[self._offset:self._offset + 6], self._offset, [])
                                            self._offset = self._offset + 6
                                        else:
                                            address0 = FAILURE
                                            if self._offset > self._failure:
                                                self._failure = self._offset
                                                self._expected = []
                                            if self._offset == self._failure:
                                                self._expected.append(('ProvisionRefs::unit_fra', '`points`'))
                                        if address0 is FAILURE:
                                            self._offset = index1
                                            chunk9, max9 = None, self._offset + 5
                                            if max9 <= self._input_size:
                                                chunk9 = self._input[self._offset:max9]
                                            if chunk9 is not None and chunk9.lower() == 'point'.lower():
                                                address0 = TreeNode(self._input[self._offset:self._offset + 5], self._offset, [])
                                                self._offset = self._offset + 5
                                            else:
                                                address0 = FAILURE
                                                if self._offset > self._failure:
                                                    self._failure = self._offset
                                                    self._expected = []
                                                if self._offset == self._failure:
                                                    self._expected.append(('ProvisionRefs::unit_fra', '`point`'))
                                            if address0 is FAILURE:
                                                self._offset = index1
                                                chunk10, max10 = None, self._offset + 10
                                                if max10 <= self._input_size:
                                                    chunk10 = self._input[self._offset:max10]
                                                if chunk10 is not None and chunk10.lower() == 'règlements'.lower():
                                                    address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                                    self._offset = self._offset + 10
                                                else:
                                                    address0 = FAILURE
                                                    if self._offset > self._failure:
                                                        self._failure = self._offset
                                                        self._expected = []
                                                    if self._offset == self._failure:
                                                        self._expected.append(('ProvisionRefs::unit_fra', '`règlements`'))
                                                if address0 is FAILURE:
                                                    self._offset = index1
                                                    chunk11, max11 = None, self._offset + 9
                                                    if max11 <= self._input_size:
                                                        chunk11 = self._input[self._offset:max11]
                                                    if chunk11 is not None and chunk11.lower() == 'règlement'.lower():
                                                        address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                                                        self._offset = self._offset + 9
                                                    else:
                                                        address0 = FAILURE
                                                        if self._offset > self._failure:
                                                            self._failure = self._offset
                                                            self._expected = []
                                                        if self._offset == self._failure:
                                                            self._expected.append(('ProvisionRefs::unit_fra', '`règlement`'))
                                                    if address0 is FAILURE:
                                                        self._offset = index1
                                                        chunk12, max12 = None, self._offset + 10
                                                        if max12 <= self._input_size:
                                                            chunk12 = self._input[self._offset:max12]
                                                        if chunk12 is not None and chunk12.lower() == 'reglements'.lower():
                                                            address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                                                            self._offset = self._offset + 10
                                                        else:
                                                            address0 = FAILURE
                                                            if self._offset > self._failure:
                                                                self._failure = self._offset
                                                                self._expected = []
                                                            if self._offset == self._failure:
                                                                self._expected.append(('ProvisionRefs::unit_fra', '`reglements`'))
                                                        if address0 is FAILURE:
                                                            self._offset = index1
                                                            chunk13, max13 = None, self._offset + 9
                                                            if max13 <= self._input_size:
                                                                chunk13 = self._input[self._offset:max13]
                                                            if chunk13 is not None and chunk13.lower() == 'reglement'.lower():
                                                                address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                                                                self._offset = self._offset + 9
                                                            else:
                                                                address0 = FAILURE
                                                                if self._offset > self._failure:
                                                                    self._failure = self._offset
                                                                    self._expected = []
                                                                if self._offset == self._failure:
                                                                    self._expected.append(('ProvisionRefs::unit_fra', '`reglement`'))
                                                            if address0 is FAILURE:
                                                                self._offset = index1
                                                                chunk14, max14 = None, self._offset + 8
                                                                if max14 <= self._input_size:
                                                                    chunk14 = self._input[self._offset:max14]
                                                                if chunk14 is not None and chunk14.lower() == 'sections'.lower():
                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
                                                                    self._offset = self._offset + 8
                                                                else:
                                                                    address0 = FAILURE
                                                                    if self._offset > self._failure:
                                                                        self._failure = self._offset
                                                                        self._expected = []
                                                                    if self._offset == self._failure:
                                                                        self._expected.append(('ProvisionRefs::unit_fra', '`sections`'))
                                                                if address0 is FAILURE:
                                                                    self._offset = index1
                                                                    chunk15, max15 = None, self._offset + 7
                                                                    if max15 <= self._input_size:
                                                                        chunk15 = self._input[self._offset:max15]
                                                                    if chunk15 is not None and chunk15.lower() == 'section'.lower():
                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
                                                                        self._offset = self._offset + 7
                                                                    else:
                                                                        address0 = FAILURE
                                                                        if self._offset > self._failure:
                                                                            self._failure = self._offset
                                                                            self._expected = []
                                                                        if self._offset == self._failure:
                                                                            self._expected.append(('ProvisionRefs::unit_fra', '`section`'))
                                                                    if address0 is FAILURE:
                                                                        self._offset = index1
                                                                        chunk16, max16 = None, self._offset + 16
                                                                        if max16 <= self._input_size:
                                                                            chunk16 = self._input[self._offset:max16]
                                                                        if chunk16 is not None and chunk16.lower() == 'sous-paragraphes'.lower():
                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 16], self._offset, [])
                                                                            self._offset = self._offset + 16
                                                                        else:
                                                                            address0 = FAILURE
                                                                            if self._offset > self._failure:
                                                                                self._failure = self._offset
                                                                                self._expected = []
                                                                            if self._offset == self._failure:
                                                                                self._expected.append(('ProvisionRefs::unit_fra', '`sous-paragraphes`'))
                                                                        if address0 is FAILURE:
                                                                            self._offset = index1
                                                                            chunk17, max17 = None, self._offset + 15
                                                                            if max17 <= self._input_size:
                                                                                chunk17 = self._input[self._offset:max17]
                                                                            if chunk17 is not None and chunk17.lower() == 'sous-paragraphe'.lower():
                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
                                                                                self._offset = self._offset + 15
                                                                            else:
                                                                                address0 = FAILURE
                                                                                if self._offset > self._failure:
                                                                                    self._failure = self._offset
                                                                                    self._expected = []
                                                                                if self._offset == self._failure:
                                                                                    self._expected.append(('ProvisionRefs::unit_fra', '`sous-paragraphe`'))
                                                                            if address0 is FAILURE:
                                                                                self._offset = index1
                                                                                chunk18, max18 = None, self._offset + 15
                                                                                if max18 <= self._input_size:
                                                                                    chunk18 = self._input[self._offset:max18]
                                                                                if chunk18 is not None and chunk18.lower() == 'sous-règlements'.lower():
                                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
                                                                                    self._offset = self._offset + 15
                                                                                else:
                                                                                    address0 = FAILURE
                                                                                    if self._offset > self._failure:
                                                                                        self._failure = self._offset
                                                                                        self._expected = []
                                                                                    if self._offset == self._failure:
                                                                                        self._expected.append(('ProvisionRefs::unit_fra', '`sous-règlements`'))
                                                                                if address0 is FAILURE:
                                                                                    self._offset = index1
                                                                                    chunk19, max19 = None, self._offset + 14
                                                                                    if max19 <= self._input_size:
                                                                                        chunk19 = self._input[self._offset:max19]
                                                                                    if chunk19 is not None and chunk19.lower() == 'sous-règlement'.lower():
                                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                        self._offset = self._offset + 14
                                                                                    else:
                                                                                        address0 = FAILURE
                                                                                        if self._offset > self._failure:
                                                                                            self._failure = self._offset
                                                                                            self._expected = []
                                                                                        if self._offset == self._failure:
                                                                                            self._expected.append(('ProvisionRefs::unit_fra', '`sous-règlement`'))
                                                                                    if address0 is FAILURE:
                                                                                        self._offset = index1
                                                                                        chunk20, max20 = None, self._offset + 15
                                                                                        if max20 <= self._input_size:
                                                                                            chunk20 = self._input[self._offset:max20]
                                                                                        if chunk20 is not None and chunk20.lower() == 'sous-reglements'.lower():
                                                                                            address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
                                                                                            self._offset = self._offset + 15
                                                                                        else:
                                                                                            address0 = FAILURE
                                                                                            if self._offset > self._failure:
                                                                                                self._failure = self._offset
                                                                                                self._expected = []
                                                                                            if self._offset == self._failure:
                                                                                                self._expected.append(('ProvisionRefs::unit_fra', '`sous-reglements`'))
                                                                                        if address0 is FAILURE:
                                                                                            self._offset = index1
                                                                                            chunk21, max21 = None, self._offset + 14
                                                                                            if max21 <= self._input_size:
                                                                                                chunk21 = self._input[self._offset:max21]
                                                                                            if chunk21 is not None and chunk21.lower() == 'sous-reglement'.lower():
                                                                                                address0 = TreeNode(self._input[self._offset:self._offset + 14], self._offset, [])
                                                                                                self._offset = self._offset + 14
                                                                                            else:
                                                                                                address0 = FAILURE
                                                                                                if self._offset > self._failure:
                                                                                                    self._failure = self._offset
                                                                                                    self._expected = []
                                                                                                if self._offset == self._failure:
                                                                                                    self._expected.append(('ProvisionRefs::unit_fra', '`sous-reglement`'))
                                                                                            if address0 is FAILURE:
                                                                                                self._offset = index1
                                                                                                chunk22, max22 = None, self._offset + 13
                                                                                                if max22 <= self._input_size:
                                                                                                    chunk22 = self._input[self._offset:max22]
                                                                                                if chunk22 is not None and chunk22.lower() == 'sous-sections'.lower():
                                                                                                    address0 = TreeNode(self._input[self._offset:self._offset + 13], self._offset, [])
                                                                                                    self._offset = self._offset + 13
                                                                                                else:
                                                                                                    address0 = FAILURE
                                                                                                    if self._offset > self._failure:
                                                                                                        self._failure = self._offset
                                                                                                        self._expected = []
                                                                                                    if self._offset == self._failure:
                                                                                                        self._expected.append(('ProvisionRefs::unit_fra', '`sous-sections`'))
                                                                                                if address0 is FAILURE:
                                                                                                    self._offset = index1
                                                                                                    chunk23, max23 = None, self._offset + 12
                                                                                                    if max23 <= self._input_size:
                                                                                                        chunk23 = self._input[self._offset:max23]
                                                                                                    if chunk23 is not None and chunk23.lower() == 'sous-section'.lower():
                                                                                                        address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                                                                                                        self._offset = self._offset + 12
                                                                                                    else:
                                                                                                        address0 = FAILURE
                                                                                                        if self._offset > self._failure:
                                                                                                            self._failure = self._offset
                                                                                                            self._expected = []
                                                                                                        if self._offset == self._failure:
                                                                                                            self._expected.append(('ProvisionRefs::unit_fra', '`sous-section`'))
                                                                                                    if address0 is FAILURE:
                                                                                                        self._offset = index1
        self._cache['unit_fra'][index0] = (address0, self._offset)
        return address0

    def _read_and_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['and_eng'].get(index0)
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
                self._expected.append(('ProvisionRefs::and_eng', '`and`'))
        self._cache['and_eng'][index0] = (address0, self._offset)
        return address0

    def _read_and_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['and_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'en'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::and_afr', '`en`'))
        self._cache['and_afr'][index0] = (address0, self._offset)
        return address0

    def _read_and_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['and_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'et'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::and_fra', '`et`'))
        self._cache['and_fra'][index0] = (address0, self._offset)
        return address0

    def _read_or_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['or_eng'].get(index0)
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
                self._expected.append(('ProvisionRefs::or_eng', '`or`'))
        self._cache['or_eng'][index0] = (address0, self._offset)
        return address0

    def _read_or_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['or_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'of'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::or_afr', '`of`'))
        self._cache['or_afr'][index0] = (address0, self._offset)
        return address0

    def _read_or_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['or_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'ou'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::or_fra', '`ou`'))
        self._cache['or_fra'][index0] = (address0, self._offset)
        return address0

    def _read_to_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to_eng'].get(index0)
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
                self._expected.append(('ProvisionRefs::to_eng', '`to`'))
        self._cache['to_eng'][index0] = (address0, self._offset)
        return address0

    def _read_to_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 3
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'tot'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 3], self._offset, [])
            self._offset = self._offset + 3
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::to_afr', '`tot`'))
        self._cache['to_afr'][index0] = (address0, self._offset)
        return address0

    def _read_to_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['to_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'à'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::to_fra', '`à`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 1
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'a'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                self._offset = self._offset + 1
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::to_fra', '`a`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['to_fra'][index0] = (address0, self._offset)
        return address0

    def _read_of_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_eng'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'of'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_eng', '`of`'))
        self._cache['of_eng'][index0] = (address0, self._offset)
        return address0

    def _read_of_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 3
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'van'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 3], self._offset, [])
            self._offset = self._offset + 3
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_afr', '`van`'))
        self._cache['of_afr'][index0] = (address0, self._offset)
        return address0

    def _read_of_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 2
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'de'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 2], self._offset, [])
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_fra', '`de`'))
        self._cache['of_fra'][index0] = (address0, self._offset)
        return address0

    def _read_of_this_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_this_eng'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 7
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'of this'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
            self._offset = self._offset + 7
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_this_eng', '`of this`'))
        self._cache['of_this_eng'][index0] = (address0, self._offset)
        return address0

    def _read_of_this_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_this_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 11
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'van hierdie'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
            self._offset = self._offset + 11
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_this_afr', '`van hierdie`'))
        self._cache['of_this_afr'][index0] = (address0, self._offset)
        return address0

    def _read_of_this_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_this_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 8
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'de cette'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 8], self._offset, [])
            self._offset = self._offset + 8
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_this_fra', '`de cette`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 5
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'de ce'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 5], self._offset, [])
                self._offset = self._offset + 5
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_this_fra', '`de ce`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_this_fra'][index0] = (address0, self._offset)
        return address0

    def _read_of_the_act_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_the_act_eng'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 10
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'of the Act'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
            self._offset = self._offset + 10
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_the_act_eng', '`of the Act`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 10
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'of the act'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 10], self._offset, [])
                self._offset = self._offset + 10
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_the_act_eng', '`of the act`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_the_act_eng'][index0] = (address0, self._offset)
        return address0

    def _read_of_the_act_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_the_act_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 11
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'van die Wet'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
            self._offset = self._offset + 11
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_the_act_afr', '`van die Wet`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 11
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'van die wet'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                self._offset = self._offset + 11
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_the_act_afr', '`van die wet`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_the_act_afr'][index0] = (address0, self._offset)
        return address0

    def _read_of_the_act_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_the_act_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 9
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'de la Loi'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
            self._offset = self._offset + 9
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_the_act_fra', '`de la Loi`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 9
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'de la loi'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 9], self._offset, [])
                self._offset = self._offset + 9
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_the_act_fra', '`de la loi`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_the_act_fra'][index0] = (address0, self._offset)
        return address0

    def _read_of_that_act_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_that_act_eng'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 11
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'of that Act'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
            self._offset = self._offset + 11
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_that_act_eng', '`of that Act`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 11
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'of that act'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 11], self._offset, [])
                self._offset = self._offset + 11
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_that_act_eng', '`of that act`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_that_act_eng'][index0] = (address0, self._offset)
        return address0

    def _read_of_that_act_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_that_act_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 15
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'van daardie Wet'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
            self._offset = self._offset + 15
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_that_act_afr', '`van daardie Wet`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 15
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'van daardie wet'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 15], self._offset, [])
                self._offset = self._offset + 15
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_that_act_afr', '`van daardie wet`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_that_act_afr'][index0] = (address0, self._offset)
        return address0

    def _read_of_that_act_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['of_that_act_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 12
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'de cette Loi'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
            self._offset = self._offset + 12
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::of_that_act_fra', '`de cette Loi`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 12
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == 'de cette loi'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 12], self._offset, [])
                self._offset = self._offset + 12
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::of_that_act_fra', '`de cette loi`'))
            if address0 is FAILURE:
                self._offset = index1
        self._cache['of_that_act_fra'][index0] = (address0, self._offset)
        return address0

    def _read_thereof_eng(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['thereof_eng'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 7
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'thereof'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
            self._offset = self._offset + 7
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::thereof_eng', '`thereof`'))
        self._cache['thereof_eng'][index0] = (address0, self._offset)
        return address0

    def _read_thereof_afr(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['thereof_afr'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 7
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'daarvan'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
            self._offset = self._offset + 7
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::thereof_afr', '`daarvan`'))
        self._cache['thereof_afr'][index0] = (address0, self._offset)
        return address0

    def _read_thereof_fra(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['thereof_fra'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0, max0 = None, self._offset + 7
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == 'de cela'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 7], self._offset, [])
            self._offset = self._offset + 7
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::thereof_fra', '`de cela`'))
        self._cache['thereof_fra'][index0] = (address0, self._offset)
        return address0

    def _read_dash(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['dash'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and chunk0.lower() == '-'.lower():
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::dash', '`-`'))
        if address0 is FAILURE:
            self._offset = index1
            chunk1, max1 = None, self._offset + 1
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 is not None and chunk1.lower() == '–'.lower():
                address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                self._offset = self._offset + 1
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::dash', '`–`'))
            if address0 is FAILURE:
                self._offset = index1
                chunk2, max2 = None, self._offset + 1
                if max2 <= self._input_size:
                    chunk2 = self._input[self._offset:max2]
                if chunk2 is not None and chunk2.lower() == '—'.lower():
                    address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                    self._offset = self._offset + 1
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('ProvisionRefs::dash', '`—`'))
                if address0 is FAILURE:
                    self._offset = index1
        self._cache['dash'][index0] = (address0, self._offset)
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
        if chunk0 is not None and Grammar.REGEX_2.search(chunk0):
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::comma', '[,;]'))
        self._cache['comma'][index0] = (address0, self._offset)
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
        if chunk0 is not None and Grammar.REGEX_3.search(chunk0):
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::digit', '[0-9]'))
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
        if chunk0 is not None and Grammar.REGEX_4.search(chunk0):
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::alpha_num_dot', '[a-zA-Z0-9.-]'))
        self._cache['alpha_num_dot'][index0] = (address0, self._offset)
        return address0

    def _read_alpha_num_no_trailing_dot(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['alpha_num_no_trailing_dot'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0, max0 = None, self._offset + 1
        if max0 <= self._input_size:
            chunk0 = self._input[self._offset:max0]
        if chunk0 is not None and Grammar.REGEX_5.search(chunk0):
            address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append(('ProvisionRefs::alpha_num_no_trailing_dot', '[a-zA-Z0-9-]'))
        if address0 is FAILURE:
            self._offset = index1
            index2, elements0 = self._offset, []
            address1 = FAILURE
            chunk1, max1 = None, self._offset + 1
            if max1 <= self._input_size:
                chunk1 = self._input[self._offset:max1]
            if chunk1 == '.':
                address1 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                self._offset = self._offset + 1
            else:
                address1 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append(('ProvisionRefs::alpha_num_no_trailing_dot', '\'.\''))
            if address1 is not FAILURE:
                elements0.append(address1)
                address2 = FAILURE
                chunk2, max2 = None, self._offset + 1
                if max2 <= self._input_size:
                    chunk2 = self._input[self._offset:max2]
                if chunk2 is not None and Grammar.REGEX_6.search(chunk2):
                    address2 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                    self._offset = self._offset + 1
                else:
                    address2 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('ProvisionRefs::alpha_num_no_trailing_dot', '[a-zA-Z0-9]'))
                if address2 is not FAILURE:
                    elements0.append(address2)
                else:
                    elements0 = None
                    self._offset = index2
            else:
                elements0 = None
                self._offset = index2
            if elements0 is None:
                address0 = FAILURE
            else:
                address0 = TreeNode(self._input[index2:self._offset], index2, elements0)
                self._offset = self._offset
            if address0 is FAILURE:
                self._offset = index1
        self._cache['alpha_num_no_trailing_dot'][index0] = (address0, self._offset)
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
                self._expected.append(('ProvisionRefs::WS', '" "'))
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
                    self._expected.append(('ProvisionRefs::WS', '"\\t"'))
            if address0 is FAILURE:
                self._offset = index1
                chunk2, max2 = None, self._offset + 1
                if max2 <= self._input_size:
                    chunk2 = self._input[self._offset:max2]
                if chunk2 == '\n':
                    address0 = TreeNode(self._input[self._offset:self._offset + 1], self._offset, [])
                    self._offset = self._offset + 1
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append(('ProvisionRefs::WS', '"\\n"'))
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
            self._expected.append(('ProvisionRefs', '<EOF>'))
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
