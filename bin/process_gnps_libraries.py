import sys
import argparse
import pandas as pd
import requests

def get_gnps_library_entries(library_name):
    url = "https://gnps.ucsd.edu/ProteoSAFe/LibraryServlet?library={}".format(library_name)

    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    data = response.json()

    return data

def get_all_gnps_libraries():
    url = "http://external.gnps2.org/gnpslibrary.json"

    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    data = response.json()

    return data
    

def main():
    parser = argparse.ArgumentParser(description='Test write out a file.')
    parser.add_argument('output_folder')

    args = parser.parse_args()

    all_gnps_libraries = get_all_gnps_libraries()

    library_entries = []

    for library in all_gnps_libraries:
        print(library)
        library_name = library['library']
        print(f"Processing library: {library_name}")
        entries = get_gnps_library_entries(library_name)
        # for entry in entries:
        #     entry['library'] = library_name



if __name__ == "__main__":
    main()