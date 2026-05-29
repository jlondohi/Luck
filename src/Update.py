import sys
import requests
from tqdm import tqdm
import zipfile
import os
import logging

#--------------------------------------
#               Functions
#--------------------------------------
def download(url, dest_folder, version):
    zip_path = os.path.join(dest_folder, f'{version}.zip')
    try:
        #Download with progress bar
        response = requests.get(url, stream=True, timeout=30)
        total = int(response.headers.get('content-length', 0))

        with open(zip_path, 'wb') as file, tqdm(
            desc='Downloading update',
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

    except Exception as e:
        logging.error(f'Error during download: {e}')
        return
    
    else:
        logging.info('Complete download. Decompressing ...')
        decompressing(zip_path, version)


def decompressing(zip_path, version):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(f'{version}')

    # PENDING. Aquí puedes decidir si:
    # - Reemplazas archivos antiguos
    # - Ejecutas un nuevo instalador
    # - Solo informas al usuario

    logging.info('Completed extraction')

#--------------------------------------
#               Program
#--------------------------------------
#Defining parameters entered from the system
url = sys.argv[1]
dest_folder = sys.argv[2]
version = sys.argv[3]
logging.info('')
download(url, dest_folder, version)