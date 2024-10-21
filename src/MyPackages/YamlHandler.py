import yaml

#=================================================================
### Creating a yaml handler to load and save system configuration
#=================================================================
class YamlHandler:
    def __init__(self, name_yaml):
        self.name_yaml = name_yaml
        self.index = {}
        self.load()
    
    def load(self):
        try:
            with open(self.name_yaml, "r", encoding="utf-8") as archivo:
                self.index = yaml.safe_load(archivo)
        except FileNotFoundError:
            print(f"The file {self.name_yaml} was not found.")
        except yaml.YAMLError:
            print(f"Error decoding JSON YAML {self.name_yaml}.")
    
    def save(self):
        try:
            with open(self.name_yaml, "w", encoding="utf-8") as archivo:
                yaml.dump(self.index, archivo, indent=4, allow_unicode=True, sort_keys=False)
        except Exception as exc:
            print(f"Error saving parameters: {exc}.")
    
    def getNested(self, *keys):
        nasted = self.index
        for key in keys:
            nasted = nasted.get(key, {})
        if nasted == {}:
            nasted = ""
        return nasted
