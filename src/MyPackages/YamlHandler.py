import yaml, os
import logging

#=================================================================
### Creating a yaml handler to load and save system configuration
#=================================================================
class YamlHandler:
    """
    Handler for loading and saving YAML configuration files, with support for nested value retrieval.

    Attributes:
        yaml_path (str): Path to the YAML file.
        index (dict): Loaded YAML data.
        defaultValue (any): Default value to return when a nested key is missing or empty.

    Methods:
        __init__(self, yaml_path=''): Initializes the YamlHandler and loads the YAML file if it exists.
        load(self, *args): Loads the YAML file from disk.
        save(self, *args): Saves the current index to the YAML file.
        getNested(self, *keys): Retrieves a nested value from the index, returning defaultValue if missing or empty.
    """
    def __init__(self, yaml_path=''):
        """
        Initializes the YamlHandler and loads the YAML file if it exists.

        Args:
            yaml_path (str, optional): Path to the YAML file. Defaults to ''.
        """
        self.yaml_path = yaml_path
        self.index = {}
        self.defaultValue = ''
        if os.path.exists(yaml_path):
            self.load()
    
    def load(self, *args):
        """
        Loads the YAML file from disk into the index attribute.

        Args:
            *args: Additional arguments (unused).

        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as file:
                self.index = yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f'The file {self.yaml_path} was not found.')
            return False
        except yaml.YAMLError:
            logging.error(f'Error decoding JSON YAML {self.yaml_path}.')
            return False
        else:
            return True
    
    def save(self, *args):
        """
        Saves the current index dictionary to the YAML file.

        Args:
            *args: Additional arguments (unused).

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            with open(self.yaml_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.index, file, indent=4, allow_unicode=True, sort_keys=False)
        except Exception as exc:
            logging.error(f'Error saving parameters: {exc}.')
            return False
        else:
            return True
    
    def getNested(self, *keys):
        """
        Retrieves a nested value from the index dictionary.

        If any key is missing, its value is None, an empty list, or an empty dict,
        returns self.defaultValue.

        Args:
            *keys: Sequence of keys to traverse the nested dictionary.

        Returns:
            any: The nested value or self.defaultValue if not found or empty.
        """
        nested = self.index
        for key in keys:
            if not isinstance(nested, dict) or key not in nested:
                return self.defaultValue
            nested = nested[key]
            if nested in (None, [], {}):
                return self.defaultValue
        return nested
