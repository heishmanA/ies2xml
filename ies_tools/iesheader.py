class IesHeader:
    def __init__(self):
        """Represents the header for the IES file
        """
        self.id_space:str|None = ""
        self.key_space: str|None = ""
        self.Version = 1
        # the following are 'longs' in the original code, but python automatically converts longs to int
        self.info_size: int = 0 # offset of data
        self.data_size: int = 0 # offset of resources
        self.total_size: int = 0 # total file size
        self.use_class_id:bool = False # set to False by default - could possibly cause issues if not checked prior to calling
        self.column_count: int = 0
        self.row_count = 0
        self.number_of_column_count = 0 # the number of "number" columns 
        self.number_of_str_column_count = 0 # the number of string columns
        
    def increase_row_count(self):
        """
            increases the row count of this - kind of redundant, but was having an issue trying to update row count
        """
        self.row_count += 1