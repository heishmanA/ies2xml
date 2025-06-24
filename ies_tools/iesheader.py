class IesHeader:
    def __init__(self):
        self.id_space:str|None = ""
        self.key_space: str|None = None
        self.Version:int | None = None
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
        self.row_count += 1