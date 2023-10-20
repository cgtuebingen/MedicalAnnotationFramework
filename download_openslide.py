"""
This file is there to download the latest version of openslide from their website.
Only works for windows currently
"""
#TODO: Makes this work for other operating systems
import os
import requests
from bs4 import BeautifulSoup
import zipfile

openslide_url = "https://openslide.org/download/"

response = requests.get(openslide_url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    download_link = None
    for link in soup.find_all('a'):
        if link.get('href') and "openslide-win64" in link.get('href'):
            download_link = link.get('href')
            break

    if download_link:
        filename = os.path.basename(download_link)

        response = requests.get(download_link)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                file.write(response.content)

            with zipfile.ZipFile(filename) as zip_ref:
                zip_ref.extractall()

            os.remove(filename)
            os.rename(filename[:-4], "openslide")
            print(f"Openslide has been successfully downloaded.")
        else:
            print("Failed to download OpenSlide library.")
    else:
        print("Download link not found on the page.")
else:
    print("Failed to access the OpenSlide download page.")
