import sys
import argparse
import pandas as pd
import requests
import random
import json
import os
import shutil

# debugging
#import requests_cache
#requests_cache.install_cache('gnps_cache')

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
    parser = argparse.ArgumentParser(description='Gets all the GNPS1 libraries with the spectrumids')
    parser.add_argument('cache_summaries_folder')
    parser.add_argument('output_summaries_folder')
    parser.add_argument('output_overall_summary')

    args = parser.parse_args()

    all_gnps_libraries = get_all_gnps_libraries()

    # DEBUG filtering to only GNPS-SUSPECTLIST	
    #all_gnps_libraries = [lib for lib in all_gnps_libraries if lib['library'] == 'MULTIPLEX-SYNTHESIS-LIBRARY-ALL-PARTITION-1']

    output_summary_list = []
    
    # shuffle order
    #shuffled = random.shuffle(all_gnps_libraries)

    for library in all_gnps_libraries:

        library_summary = {
            'library': library['library'],
        }

        print(library)
        library_name = library['library']
        print(f"Processing library: {library_name}")

        output_filename = f"{args.output_summaries_folder}/{library_name}.json"

        try:
            # DEBUGGING
            #raise Exception("Forcing error to test cache handling")
        
            entries = get_gnps_library_entries(library_name)
            
            # saving it out
            open(output_filename, 'w').write(json.dumps(entries, indent=2))

            library_summary["status"] = "updated"
            output_summary_list.append(library_summary)
        except:
            # we're going to find the file in the cache
            cache_filename = f"{args.cache_summaries_folder}/{library_name}.json"
            
            # if it exists, we will copy it over
            if os.path.exists(cache_filename):
                shutil.copyfile(cache_filename, output_filename)
                library_summary["status"] = "using_cache"
                output_summary_list.append(library_summary)
            else:
                print(f"Error processing library {library_name}. No cached file found at {cache_filename}.")
                library_summary["status"] = "missing"
                output_summary_list.append(library_summary)
                continue

    # writing this out with pandas
    output_summary_df = pd.DataFrame(output_summary_list)
    output_summary_df.to_csv(args.output_overall_summary, index=False)

        


if __name__ == "__main__":
    main()