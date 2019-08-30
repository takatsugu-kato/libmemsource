"""
This modules is to handle mxliff file
"""

import re
from lxml import etree

class Mxliff():
    """
    Object handling mxliff file

    Args:
        path (str): path of the mxliff file
    """

    def __init__(self, path):
        self.source_language = ""
        self.target_language = ""
        self.trans_unit_count = 0
        self.path = path
        self.tree = etree.parse(path)
        etree.register_namespace('xliff', 'urn:oasis:names:tc:xliff:document:1.2')
        etree.register_namespace('m', 'http://www.memsource.com/mxlf/2.0')
        self.root = self.tree.getroot()
        self.namespace = {
            'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
            'm': 'http://www.memsource.com/mxlf/2.0'
        }
        self.files = self.__get_segment()
        self.__set_language()

    def __set_language(self):
        """
        Set language code from mxliff file to this class const
        """

        files = self.root.findall('xliff:file', self.namespace)
        self.source_language = files[0].get('source-language')
        self.target_language = files[0].get('target-language')

    def __get_segment(self):
        """
        Create File obcject from mxliff file

        Returns:
            File: File objects
        """
        trans_unit_count = 0
        files = []
        for file in self.root.findall('xliff:file', self.namespace):
            file_obj = File(file.get('original'))
            for trans_unit_element in file.findall('xliff:body/xliff:group/xliff:trans-unit', self.namespace):
                trans_unit_obj = TransUnit(trans_unit_element.get('id'))
                trans_unit_obj.source = self.__create_seg_obj(trans_unit_element, "source")
                trans_unit_obj.set_only_tag_flag()
                trans_unit_obj.target = self.__create_seg_obj(trans_unit_element, "target")
                trans_unit_obj.metadata = self.__create_metadata(trans_unit_element)
                trans_unit_count = trans_unit_count + 1
                file_obj.trans_units.append(trans_unit_obj)
            files.append(file_obj)
        self.trans_unit_count = trans_unit_count
        return files

    def __create_seg_obj(self, trans_unit_element, tag):
        """
        Creale Segment object from etree.Element

        Args:
            trans_unit_element (etree.Element): Element object of etree
            tag (str): tag name (source, seg-source, target)

        Returns:
            Segment: Segment object in this class
        """

        element = trans_unit_element.find('xliff:'+tag, self.namespace)

        seg_obj = Segment()
        seg_obj.string = self.__convert_element_to_string(element)
        return seg_obj

    def __create_metadata(self, trans_unit_element):
        elements = trans_unit_element.findall('m:tunit-metadata/m:mark', self.namespace)
        marks = dict()
        for element in elements:
            mark_obj = Mark()
            if element.find('m:type', self.namespace) is not None:
                mark_obj.type = self.__clean_element_string(etree.tostring(element.find('m:type', self.namespace), encoding='unicode'))
            mark_obj.content = self.__clean_element_string(etree.tostring(element.find('m:content', self.namespace), encoding='unicode'))
            marks[element.get('id')] = mark_obj
        return marks


    def __convert_element_to_string(self, element):
        """
        Convert Element object to string

        Args:
            element (etree.Element): Element object of etree

        Returns:
            str: plain text of Element
        """

        string = etree.tostring(element, encoding='unicode')
        return self.__clean_element_string(string)

    def back_to_xlf(self):
        """
        Generate to xlf file from File object
        """

        for file in self.files:
            for trans_unit in file.trans_units:
                new_target_element = self.__create_xml_string_for_element(trans_unit.target)
                condition = ('xliff:file[@original="{0}"]/xliff:body/xliff:group/xliff:trans-unit[@id="{1}"]'
                             .format(file.original, trans_unit.trans_unit_id))
                trans_unit_element = self.root.find(condition, self.namespace)
                target = trans_unit_element.find('xliff:target', self.namespace)
                trans_unit_element.remove(target)
                trans_unit_element.append(new_target_element)
        self.tree.write(self.path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def __clean_element_string(string):
        """
        Clean the string of Element

        Args:
            string (str): plain text of Element

        Returns:
            str: string of deleted xml tag
        """
        string = string.strip()
        string = re.sub('<.*?>', "", string, flags=re.DOTALL)
        return string

    @staticmethod
    def __create_xml_string_for_element(segment_obj):
        """
        Create xml string for segment element

        Args:
            segment_obj (Segment): Segment object in this class

        Returns:
            str: xml string
        """
        xml_string = '<target>{0}</target>'.format(segment_obj.string)
        tree = etree.fromstring(xml_string)
        return tree

class File():
    """
    Object of <file> tag in mxliff
    """

    def __init__(self, original):
        self.original = original
        self.trans_units = []


class TransUnit():
    """
    Object of <trans-unit> tag in mxliff
    """

    def __init__(self, trans_unit_id):
        self.trans_unit_id = trans_unit_id
        self.source = ""
        self.target = ""
        self.mt_processed = False
        self.only_tag = False
        self.metadata = dict()

    def set_only_tag_flag(self):
        """
        Set only_tag flag using source string
        """
        source_temp = self.source.string
        # delete format tags
        repatter = re.compile(r'{([0-9]+)&gt;(.*?)&lt;\1}')
        while repatter.search(source_temp):
            source_temp = repatter.sub('\\2', source_temp, count=1)

        # delete placeholder tags
        repatter = re.compile(r'{([0-9]+)}')
        source_temp = repatter.sub("", source_temp)
        source_temp = source_temp.rstrip()
        if source_temp == "":
            self.only_tag = True


class Segment():
    """
    Object of <source> and <target> tag in mxliff
    """

    def __init__(self):
        self.string = ""

class Mark():
    """
    Object of mark in tunit-unitmeta in mxliff
    """

    def __init__(self):
        self.type = ""
        self.content = ""
