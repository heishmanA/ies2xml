from ies_tools.columntype import ColumnType as CT
from ies_tools.propertyaccess import PropertyAccess as PA
class IesColumn:
    """A class to represent a column in an IES file
    """
    def __init__(self):
        self.column = None
        self.name: str = ""
        self.column_type: CT = CT.str
        self.property_access: PA = PA.CP
        self.sync:bool = False
        self.declaration_index: int = 0
    
    def __str__(self)->str:
        """Overrides the original str representation to represent this column in a readable fashion

        Returns:
            str: string representation of this column
        """
        return f'{self.column}/{self.name}:{self.column_type}'

    def isNumber(self)-> bool:
        """Returns if this column type is a number

        Returns:
            bool: True if this column is a number, false otherwise
        """
        return self.column_type == CT.number
    
    def CompareTo(self, other_column: 'IesColumn') -> int:
        """ Compares thos column with another column

        Args:
            other_column (IesColumn): The other column being compared

        Returns:
            int: returns the difference based on type and declaration index
        """
        if self.column_type == other_column.column_type or not self.isNumber() and other_column.isNumber():
            self_dec_index = self.declaration_index
            other_dec_index = other_column.declaration_index
            if self_dec_index == other_dec_index:
                return 0
            elif self_dec_index > other_dec_index:
                return 1
            else:
                return -1
    
        if self.column_type.value < other_column.column_type.value:
            return -1
        
        return 1
    
        
        
    
    
        