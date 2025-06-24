import xml.etree.ElementTree as ET
import struct
from pathlib import Path
from ies_tools.columntype import ColumnType as CT
from ies_tools.iesheader import IesHeader
from ies_tools.iesrow import IesRow
from ies_tools.iescolumn import IesColumn
from ies_tools.propertyaccess import PropertyAccess as PA

class XMLTools:
    """Tools to make reading XML and creating an object that will contain column and row information
    """
    
    # Unused variables will be removed
    __NT = "_NT"
    __CP = "CP_"
    __ROOT_NAME = "idspace"
    __CATEGORY_ELEMENT:str = "Category"
    __CLASS_ELEMENT:str = "Class"
    __CLASS_ID: str = "ClassId"
    __CLASS_NAME: str = "ClassName"
    __ID_SPACE_NAME:str = "id"
    __KEY_SPACE_NAME:str = "keyid"
    __VERSION:str = "Version"
    __USE_CLASS_ID:str = "UseClassId"
    __DECLARATION_INDEX:str = "DeclarationIndex"
    
    __PROPERTY_ACCESS_DICT = {
         "EP_": PA.EP,
         "CP_": PA.CP,
         "VP_": PA.VP,
         "CT_": PA.CT,
    }
    
    def __init__(self):
        self.__header_name_length: int = 0x40
        self.__column_size: int = 136
        self.__size_position: int = (2 * self.__header_name_length + 2 * struct.calcsize('h')) # h = format code for short
        self.__default_string: str = "None"
        self.__default_num: float = 0.0
        self.header = IesHeader()
        self.columns: list[IesColumn] = []
        self.rows: list[IesRow] = []
        self.tree = None
        self.file_name = ""
    
    def is_value_numeric(self, value: str) -> bool:
        """Verify if the given value is number

        Args:
            value (str): the string to verify

        Returns:
            bool: true if the string is numeric, false otherwise
        """
        if len(value) == 0:
            return False
        
        if value.startswith('-'):
            return True
        # Verifying that each character in the string is a space, dot, or digit
        return all(c == ' ' or c == '.' or ('0' <= c <= '9') for c in value)
        
    
    def load_xml(self, file: Path):
        if not file.name.endswith(".xml"):
            print(f'Incorrect file type passed to read_xml(self, file) {file.name}')
            return None
        self.tree = ET.parse(file)
        self.file_name = file.name
    
    def load_xml_rows(self):
        self.rows.clear()
        # Yes, this is duplicate code. I'll need to figure out why I was getting an error so I can reduce this
        class_elements: list[ET.Element[str]] = []
        if self.tree == None:
            print(f'Parsing did not work correctly for {self.file_name}. Please verify the file is in the correct format')
            return

        root = self.tree.getroot()
        category = root.find(self.__CATEGORY_ELEMENT)
        class_elements: list[ET.Element[str]] = []
        
        if category is not None:
            class_elements.extend(category.findall(self.__CLASS_ELEMENT))
        else:
            class_elements.extend(root.findall(self.__CLASS_ELEMENT))
        
        for element in class_elements:
            row = IesRow()
            for column in self.columns:
                key = column.name
                attribute = element.get(key)
                if attribute == None:
                    if column.isNumber():
                        row[key] = 0.0
                    else:
                        row[key] = ""
                        row.user_scr_dict[key] = False
                else:
                    if column.isNumber():
                        if self.is_value_numeric(attribute) == False:
                            print(f'There was an error in this file where expected value should be numeric. Key = {key} - Need to figure out how to display the lines')
                            exit()
                        row[key] = float(attribute)
                    else:
                        row[key] = attribute if attribute != None else ""
                        # forcing attribute to be uppercase in case there's some sort of lowercase value
                        row.user_scr_dict[key] = "SCR_" in attribute.upper() or "SCP" in attribute.upper()
                
                    if key == self.__CLASS_ID:
                        row.class_id = int(attribute)
                    elif key == self.__CLASS_NAME:
                        row.class_name = attribute
            self.rows.append(row)
        
        self.header.column_count = len(self.columns)
        self.header.number_of_column_count = sum(column.isNumber() for column in self.columns)
        self.header.number_of_str_column_count = self.header.column_count - self.header.number_of_column_count
    
    def load_xml_columns(self):
        """Loads the IES column information from the xml

        Args:
            file (Path): The file to be loaded
        """
        
        
        if self.tree == None:
            print(f'Parsing did not work correctly for {self.file_name}. Please verify the file is in the correct format')
            return

        root = self.tree.getroot()
        
        # Get header information
        self.header.id_space = root.get(self.__ID_SPACE_NAME)
        
        if (self.header.id_space == None):
            print(f'{self.file_name} missing id')
            return None
        self.header.key_space =  root.get(self.__KEY_SPACE_NAME) if root.get(self.__KEY_SPACE_NAME) else None
        
        # Check to verify if Category exists in the xml or not
        # Need to verify this so we know where the children of idspace exist
        category = root.find(self.__CATEGORY_ELEMENT)
        class_elements: list[ET.Element[str]] = []
        
        if category is not None:
            class_elements.extend(category.findall(self.__CLASS_ELEMENT))
        else:
            class_elements.extend(root.findall(self.__CLASS_ELEMENT))
        
        # Iterate over all attributes of each element to verify column types
        column_types = {}
        for element in class_elements:
            for property_name, property_value in element.attrib.items():
                type = CT.str
                if property_name.startswith(self.__CP):
                    type = CT.calc
                elif property_value.isdigit():
                    type = CT.number
                
                if property_name in column_types:
                    # Possible inconsistent data
                    if column_types[property_name] != type:
                        column_types[property_name] = CT.str
                else:
                    column_types[property_name] = type
        
        # clear out columns in case any have been left in
        self.columns.clear()
        # iterate all elements to get column infomration
        for element in class_elements:
            self.header.increase_row_count()
            for property_name, property_value in element.attrib.items():
                if any(col.name == property_name for col in self.columns):
                    continue
                # name_length was never used in the original implementation so it has been removed
                name: str = property_name
                access = PA.SP
                sync: bool  = False
                # Getting the first 3 characters of the name
                # This is just a better way than writing tons of if statements
                
                property_access_key = name[0:3]
                if property_access_key in self.__PROPERTY_ACCESS_DICT:
                    access = self.__PROPERTY_ACCESS_DICT[property_access_key]
                    name = property_access_key
                
                if self.__NT in property_name:      
                    sync = True
                    name = name[0: name.index(self.__NT)]
                
                column = IesColumn()
                column.name = property_name
                column.column_type = column_types[property_name] if property_name in column_types else CT.str
                column.property_access = access
                column.sync = sync
                
                if property_name == self.__CLASS_ID:
                    self.header.use_class_id = True
                
                self.columns.append(column)
                
            self.header.column_count = len(self.columns)
            self.header.number_of_column_count = sum(column.isNumber() for column in self.columns)
            self.header.number_of_str_column_count = self.header.column_count - self.header.number_of_column_count


        
        
                    