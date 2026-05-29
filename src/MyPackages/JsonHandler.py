import json
import logging

#=================================================================
### Creating a json handler to load and save system configuration
#=================================================================
class JsonHandler:
    """
    Handler for loading and saving JSON configuration files.

    Attributes:
        parent (object): Parent object, if any.
        json_path (str): Path to the JSON file.
        index (dict): Loaded JSON data.

    Methods:
        __init__(self, json_path, parent=None): Initializes the JsonHandler and loads the JSON file.
        load(self, *args): Loads the JSON file from disk.
        save(self, *args): Saves the current index to the JSON file.
    """
    def __init__(self, json_path, parent=None):
        """
        Initializes the JsonHandler and loads the JSON file.

        Args:
            json_path (str): Path to the JSON file.
            parent (object, optional): Parent object. Defaults to None.
        """
        self.parent = parent
        self.json_path = json_path
        self.index = {}
        self.load()
    
    def load(self, *args):
        """
        Loads the JSON file from disk into the index attribute.

        Args:
            *args: Additional arguments (unused).
        """
        try:
            with open(self.json_path, 'r') as file:
                self.index = json.load(file)
        except FileNotFoundError:
            logging.error(f'The file {self.json_path} was not found.')
        except json.JSONDecodeError:
            logging.error(f'Error decoding JSON file {self.json_path}.')
    
    def save(self, *args):
        """
        Saves the current index dictionary to the JSON file.

        Args:
            *args: Additional arguments (unused).
        """
        try:
            with open(self.json_path, 'w') as file:
                json.dump(self.index, file, indent=4)
        except Exception as exc:
            logging.error(f'Error saving: {exc}')
