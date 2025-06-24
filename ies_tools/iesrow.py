class IesRow(dict[str, object]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_id: int = 0
        self.class_name: str = ""
        self.user_scr_dict: dict[str, bool] = {} # Information about string values and if they use SCR

    def get_int_32(self, name: str) -> int:
        return int(self.get_float(name))
    
    def get_float(self, name:str) -> float:
        if name not in self:
            print(f'$Field "{name}" not found.')
            exit()
        
        value = self[name]
        
        if isinstance(value, float):
            return value
        else:
            print(f'$Field "{name}" is not numeric value')
            exit()
        
        