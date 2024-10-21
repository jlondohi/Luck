import json

#=================================================================
### Creating a json handler to load and save system configuration
#=================================================================
class JsonHandler:
    def __init__(self, name_json, parent=None):
        self.parent = parent
        self.name_json = name_json
        self.index = {}
        self.load()
    
    def load(self):
        try:
            with open(self.name_json, "r") as archivo:
                self.index = json.load(archivo)
        except FileNotFoundError:
            print(f"The file {self.name_json} was not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON file {self.name_json}.")
    
    def save(self):
        try:
            with open(self.name_json, "w") as archivo:
                json.dump(self.index, archivo, indent=4)
        except Exception as exc:
            print(f"Error saving: {exc}")
