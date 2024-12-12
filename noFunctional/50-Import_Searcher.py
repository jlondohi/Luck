import os
import ast

def extract_imports_from_file(file_path):
    """Extrae los imports de un archivo Python."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
    except Exception as e:
        print(f"Error leyendo el archivo {file_path}: {e}")
    return imports

def get_python_files_in_directory(directory):
    """Obtiene todos los archivos .py en un directorio y sus subdirectorios."""
    py_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files

def collect_all_imports(directory):
    """Recopila todos los imports de archivos .py en un directorio y sus subdirectorios."""
    python_files = get_python_files_in_directory(directory)
    all_imports = []
    
    for file in python_files:
        imports = extract_imports_from_file(file)
        all_imports.extend(imports)
    
    return all_imports

# Ruta del directorio que deseas analizar
directory_path = 'C:\\Luck\\src'

# Recopilamos todos los imports
imports = collect_all_imports(directory_path)


# Eliminando duplicados
imports_sd = list(set(imports))
lista_ord = sorted(imports_sd, key=len)

# Imprimir los imports encontrados
for imp in lista_ord:
    print(imp)
