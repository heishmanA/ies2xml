import xml.etree.ElementTree as ET
import struct
import os
import io
from ies_tools.binarywriter import BinaryWriterTools
from pathlib import Path
from ies_tools.columntype import ColumnType as CT
from ies_tools.iesheader import IesHeader
from ies_tools.iesrow import IesRow
from ies_tools.iescolumn import IesColumn
from ies_tools.propertyaccess import PropertyAccess as PA

class XMLTools:
    """
        A tool for reading the ies xml data and converting that information back into .ies format
    """
    
    # Unused variables will be removed
    __NT = "_NT"
    __CP = "CP_"
    __ROOT_NAME = "idspace"
    __CATEGORY_ELEMENT:str = "Category"
    __CLASS_ELEMENT:str = "Class"
    __CLASS_ID: str = "ClassID"
    __CLASS_NAME: str = "ClassName"
    __ID_SPACE_NAME:str = "id"
    __KEY_SPACE_NAME:str = "keyid"
    
    # Just an easy way to access the different property enum types because I'm lazy
    __PROPERTY_ACCESS_DICT = {
         "EP_": PA.EP,
         "CP_": PA.CP,
         "VP_": PA.VP,
         "CT_": PA.CT,
    }
    
    # Each of the following functions were made to
    # simulate the type conversion used in the original C# code
    # each flag represents the respective data type
    def __get_ushort__(self, val):
        """
        Packs the given value as an unsigned short (2 bytes) in little-endian format.
        
        Args:
            val (int): The value to encode.
        
        Returns:
            bytes: A 2-byte little-endian representation of the unsigned short.
        """
        return struct.pack('<H', val)

    def __get_short__(self, val):
        """
        Packs the given value as a signed short (2 bytes) in little-endian format.

        Args:
            val (int): The value to encode.

        Returns:
            bytes: A 2-byte little-endian representation of the signed short.
        """
        return struct.pack('<h', val)

    def __get_int__(self, val):
        """
        Packs the given value as a signed integer (4 bytes) in little-endian format.

        Args:
            val (int): The integer value to encode.

        Returns:
            bytes: A 4-byte little-endian representation of the signed integer.
        """
        return struct.pack('<i', val)

    def __get_uint_32__(self, val):
        """
        Packs the given value as an unsigned 32-bit integer (4 bytes) in little-endian format.

        Args:
            val (int): The value to encode.

        Returns:
            bytes: A 4-byte little-endian representation of the unsigned integer.
        """
        return struct.pack('<I', val)

    def __get_uint_8__(self, val):
        """
        Packs the given value as an unsigned 8-bit integer (1 byte).

        Args:
            val (int): The value to encode (must be between 0 and 255).

        Returns:
            bytes: A 1-byte representation of the unsigned 8-bit value.
        """
        return struct.pack('<B', val)

    def __get_float__(self, val):
        """
        Packs the given value as a 32-bit floating point number (4 bytes) in little-endian format.

        Args:
            val (float): The float value to encode.

        Returns:
            bytes: A 4-byte little-endian representation of the float.
        """
        return struct.pack('<f', val)

    
    def __init__(self):
        self.__header_name_length: int = 0x40
        self.__column_size: int = 136
        self.__size_position: int = (2 * self.__header_name_length + 2 * struct.calcsize('<h')) # h = format code for short
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
        """ Loads the xml file information

        Args:
            file (Path): The file path containing the xml file to load
        """
        
        if not file.name.endswith(".xml"):
            print(f'Incorrect file type passed to read_xml(self, file) {file.name} - Skipping this file')
            return None
        self.tree = ET.parse(file)
        self.file_name = file.name
    
    def load_xml_rows(self):
        """ Loads the IES row information from the xml file
        """
        self.rows.clear()
        # Yes, this is duplicate code. I'll need to figure out why I was getting an error so I can reduce this
        class_elements: list[ET.Element[str]] = []
        if self.tree == None:
            print(f'Parsing did not work correctly for {self.file_name}. Please verify the file is in the correct format')
            return

        root = self.tree.getroot()
        if root.tag != self.__ROOT_NAME:
            print(f'{root.tag} does not match {self.__ROOT_NAME} - Skipping this file')
            return
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
        self.header.column_count = 0
        self.header.row_count = 0
        self.header.number_of_column_count = 0
        self.header.number_of_str_column_count = 0
        
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
                simple_name: str = property_name
                access = PA.SP
                sync: bool  = False
                # Getting the first 3 characters of the name
                # This is just a better way than writing tons of if statements
                
                property_access_key = simple_name[0:3]
                if property_access_key in self.__PROPERTY_ACCESS_DICT:
                    access = self.__PROPERTY_ACCESS_DICT[property_access_key]
                    simple_name = property_access_key
                
                if self.__NT in property_name:      
                    sync = True
                    simple_name = simple_name[0: simple_name.index(self.__NT)]
                
                if property_name not in column_types:
                    type = CT.str
                
                column = IesColumn()
                column.column = simple_name # almost forgot  this bad boy
                column.name = property_name
                column.column_type = column_types[property_name] if property_name in column_types else CT.str
                column.property_access = access
                column.sync = sync
                
                if column.isNumber():
                    column.declaration_index = sum(c.isNumber() for c in self.columns)
                    
                else:
                    column.declaration_index = sum(not c.isNumber() for c in self.columns)
                
                if property_name == self.__CLASS_ID:
                    self.header.use_class_id = True
                
                self.columns.append(column)
                
            self.header.column_count = len(self.columns)
            self.header.number_of_column_count = sum(column.isNumber() for column in self.columns)
            self.header.number_of_str_column_count = self.header.column_count - self.header.number_of_column_count
    
        
        
    def create_ies(self, directory: str):
        columns = self.columns
        # This simulates the C# LINQ sort from the original C# implementation
        # First sort the columns by whether they are a number, then by their declaration index
        sorted_columns = sorted(columns, key=lambda column: (0 if column.isNumber() else 1, column.declaration_index))

        rows = self.rows
        row_count = len(rows)
        column_count = len(columns)
        number_of_column_count = sum(column.isNumber() for column in columns)
        string_column_count = column_count - number_of_column_count
        
        filename = self.file_name[0: self.file_name.index('.xml')] + ".ies"
        full_path = os.path.join(directory, filename)
        idspace = self.header.id_space
        keyspace = self.header.key_space if self.header.key_space else ""
        # used for padding
        null_padding_short = self.__get_ushort__(0)
        
        if idspace == None or len(idspace) == 0:
            # id space should not be missing
            print(f'Error writing to {filename} - Missing idspace. Verify the idspace exists or has been converted correctly before trying again')
            return
        
        with open(full_path, 'wb+') as raw_f:
            # Pylance will say this is an error, but will run fine at runtime (i hope)
            buffer = io.BufferedRandom(raw_f) # type: ignore
            bwt = BinaryWriterTools(buffer)
            bwt.write_fixed_string(idspace, self.__header_name_length)
            bwt.write_fixed_string(keyspace, self.__header_name_length)
            # According to what I was told the keyspace is deleted and not needed so skipping it
            
            buffer.write(self.__get_ushort__(self.header.Version))
            buffer.write(null_padding_short)
            buffer.write(self.__get_uint_32__(self.header.info_size))
            buffer.write(self.__get_uint_32__(self.header.data_size))
            buffer.write(self.__get_uint_32__(self.header.total_size))
            buffer.write(self.__get_uint_8__(1)  if self.header.use_class_id == True else self.__get_uint_8__(0))
            buffer.write(self.__get_uint_8__(0))
            buffer.write(self.__get_ushort__(row_count))
            buffer.write(self.__get_ushort__(column_count))
            buffer.write(self.__get_ushort__(number_of_column_count))
            buffer.write(self.__get_ushort__(string_column_count))
            buffer.write(null_padding_short)
            for c in columns:
                bwt.write_xored_fixed_string(c.column, self.__header_name_length)
                bwt.write_xored_fixed_string(c.name, self.__header_name_length)
                buffer.write(self.__get_ushort__(c.column_type.value))
                buffer.write(self.__get_ushort__(c.property_access.value))
                buffer.write(self.__get_ushort__(c.sync))
                buffer.write(self.__get_ushort__(c.declaration_index))
            # end loop
            rows_start = buffer.tell()
            cols = [c.name for c in sorted_columns]

            # This must where my error is
            for row in rows:
                buffer.write(self.__get_int__(row.class_id))
                bwt.write_xor_lp_str(row.class_name)
                
                for c in sorted_columns:

                    value = row[c.name]
                    if value is None:
                        if c.isNumber():
                            buffer.write(self.__get_float__(0))
                        else:
                            buffer.write(self.__get_ushort__(0))
                    else:
                        if c.isNumber():
                            buffer.write(self.__get_float__(value)) # type: ignore
                        else:
                            bwt.write_xor_lp_str(str(value))
                # end sorted loop
                # Iterating over all the columns where the column is not a number
                
                for c in [col for col in sorted_columns if col.isNumber() == False]:
                    val = row.user_scr_dict.get(c.name)
                    
                    # This handles both when user scr is true or false and when user scr is none (not found in dict)
                    buffer.write(self.__get_uint_8__(1) if val is True else self.__get_uint_8__(0))
                # end loop
            # end loop
            self.header.info_size = column_count * self.__column_size
            self.header.data_size = buffer.tell() - rows_start
            self.header.total_size = buffer.tell()
            buffer.seek(self.__size_position)
            buffer.write(self.__get_uint_32__(self.header.info_size))
            buffer.write(self.__get_uint_32__(self.header.data_size))
            buffer.write(self.__get_uint_32__(self.header.total_size))
            buffer.flush()
            buffer.seek(0, io.SEEK_END)
            
            
# Testing for debugging
xml = XMLTools()
file_path = 'xml_files/tpitem.xml'
p = Path(file_path)
xml.load_xml(p)
xml.load_xml_columns()
xml.load_xml_rows()
xml.create_ies('out')
