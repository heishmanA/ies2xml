class IesRow(dict[str, object]):
    
    def __init__(self, *args, **kwargs):
        """Represents a row found in the ies file
        """
        super().__init__(*args, **kwargs)
        self.class_id: int = 0
        self.class_name: str = ""
        self.user_scr_dict: dict[str, bool] = {} # Information about string values and if they use SCR
        
        