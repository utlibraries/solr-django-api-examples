# pylint: disable=too-many-nested-blocks
"""
Finding Aid Parsing logic.
"""
import xmltodict
import xml.etree.ElementTree as ET

# from taro.taro_manager.display_json import DisplayJson
from taro.taro_manager.utilities import return_xml_values_as_text


class ParsedFindingAid:
    namespace = "{urn:isbn:1-931666-22-9}"
    fields_to_parse = {"title": {"element": "titleproper", "parent_element": "titlestmt"},
                       "abstract": {"element": "abstract", "parent_element": "did"},
                       "taro_identifier": {"element": "eadid", "parent_element": "eadheader"},
                       "creators": {"element": ["corpname", "persname", "famname"],
                                    "parent_element": f"archdesc/{namespace}did/{namespace}origination"},

                       "languages": {"element": "language", "parent_element": "langmaterial"},
                       "geographic_areas": {"element": "geogname",
                                            "parent_element": "controlaccess"},
                       "subject_topics": {"element": "subject", "parent_element": "controlaccess"},
                       "subject_organizations": {"element": "corpname", "parent_element":
                           "controlaccess"},
                       "subject_persons": {"element": ["persname", "famname"], "parent_element":
                           "controlaccess"}
                       }

    single_valued_fields = ["title", "abstract", "digital", "taro_identifier"]

    def __init__(self, xml_file):
        xml_file.seek(0)
        ET.register_namespace('', self.namespace)
        self.xml_file = xml_file
        self.tree = self.clean_tree(ET.parse(self.xml_file))
        # self.display_json = DisplayJson(self.tree)
        self.root = self.tree.getroot()
        self.fields, self.multivalue_fields = self.parse_fields()
        self.get_all_content()
        self.get_json()
        self.get_display_fields()
        self.is_digital()
        self.get_dates()

    def clean_tree(self, tree):
        """
        There are some things that we want to clean in tree. For now, we want to remove all lb tags.
        :param tree:
        :return: cleaned tree
        """
        for parent in tree.findall(f'.//{self.namespace}lb/..'):
            for element in parent.findall(f'{self.namespace}lb'):
                tail = element.tail.strip() if element.tail else ""
                parent.remove(element)
                parent.text = parent.text.strip() + " " if parent.text else ""
                parent.text = parent.text + tail
        return tree

    def parse_fields(self):
        fields = dict()
        multivalue_fields = dict()

        for field, elements in self.fields_to_parse.items():
            values = []

            if type(elements['element']) == list:
                for element in elements['element']:
                    values = self.grab_all_current_and_children_text(values, elements, element)
            else:
                values = self.grab_all_current_and_children_text(values, elements,
                                                                 elements['element'])

                # Title can also be found in a sibling node <subtitle>
                if field == "title":
                    values = self.grab_all_current_and_children_text(values, elements, 'subtitle')

            if field in self.single_valued_fields:
                fields[field] = ' '.join([str(elem) for elem in values])
            else:
                multivalue_fields[field] = values
        return fields, multivalue_fields

    def grab_all_current_and_children_text(self, values, elements, element):
        for nodes in self.tree.findall(f".//{self.namespace}{elements['parent_element']}/"
                                       f"{self.namespace}{element}"):
            text = " ".join([t.strip() for t in nodes.itertext()])
            values.append(self._text_cleanup(text))
        return values

    def remove_namespace(self, text):
        return text.replace(self.namespace, "")

    def get_all_content(self):
        """
        Returns all a string of all values (not tags or attributes) pulled from
        the xml file. String has had any line breaks or unnecessary whitespaces
        removed.
        """
        self.xml_file.seek(0)
        self.fields['all_content'] = return_xml_values_as_text(self.xml_file.read())

    def get_json(self):
        """
        Creates the json version of finding aid to save to database.
        """
        self.xml_file.seek(0)
        self.fields['json'] = xmltodict.parse(self.xml_file.read())

    def get_display_fields(self):
        """
        Creates a custom json with only display-related content and tags.
        """
        self.fields['display_fields'] = self.display_json.create_json_for_display(self.tree)

    @staticmethod
    def _text_cleanup(text):
        """
        Cleans up text, removing any stacked whitespaces, line breaks,
        tabs, etc.
        """
        return " ".join(str(text).split())

    def is_digital(self):
        """
        Checks for existence of dao tag.
        """
        digital = self.tree.find(f'.//{self.namespace}dao')
        if digital != None:
            self.fields['digital'] = True
        else:
            self.fields['digital'] = False

    def get_dates(self):
        self.multivalue_fields['start_dates'] = list()
        self.multivalue_fields['end_dates'] = list()
        for archdesc in self.root.findall(f'{self.namespace}archdesc'):
            did = archdesc.find(f'{self.namespace}did')
            unitdates = did.findall(f'{self.namespace}unitdate')
            for unitdate in unitdates:
                try:
                    dates = unitdate.attrib['normal'].split("/")
                    cleaned_dates = []
                    for date in dates:
                        if len(str(date)) > 4:
                            cleaned_dates.append(str(date)[0:4])
                        else:
                            cleaned_dates.append(date)
                    start_date = cleaned_dates[0]
                    self.multivalue_fields['start_dates'].append(start_date)
                    if len(dates) == 2:
                        end_date = cleaned_dates[1]
                        self.multivalue_fields['end_dates'].append(end_date)
                except KeyError:
                    pass