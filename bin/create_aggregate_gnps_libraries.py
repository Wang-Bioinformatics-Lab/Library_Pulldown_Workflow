import argparse
import os
import json

from process_gnps_libraries import get_all_gnps_libraries

def main():
    parser = argparse.ArgumentParser(description='Test write out a file.')
    parser.add_argument('input_folder')
    parser.add_argument('output_folder')

    args = parser.parse_args()

    # lets get the libraries from the api 
    gnps_libraries_list = get_all_gnps_libraries()

    NON_PROPOGATED_TYPE = ["GNPS", "IMPORT"]
    PROPOGATED_TYPE = ["GNPS-PROPOGATED"]

    output_mgf_all = open(os.path.join(args.output_folder, "ALL_GNPS.mgf"), "w")
    output_msp_all = open(os.path.join(args.output_folder, "ALL_GNPS.msp"), "w")
    output_mgf_non_propogated = open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED.mgf"), "w")
    output_msp_non_propogated = open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED.msp"), "w")

    output_split_file_count = 1
    output_split_spectra_count = 0
    output_split_mgf_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_SPLIT_{}.mgf".format(output_slit_mgf_file_count)), "w")
    output_split_msp_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_SPLIT_{}.msp".format(output_split_file_count)), "w")

    # non propogated split
    output_split_non_propogated_file_count = 1
    output_split_non_propogated_spectra_count = 0
    output_split_mgf_non_propogated_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED_SPLIT_{}.mgf".format(output_split_mgf_non_propogated_file_count)), "w")
    output_split_msp_non_propogated_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED_SPLIT_{}.msp".format(output_split_file_count)), "w")

    # for us to write the JSON file
    non_propogated_spectra_list = []
    propogated_spectra_list = []

    for library in gnps_libraries_list:
        # reading the json
        input_library_json = json.load(open(os.path.join(args.input_folder, f"{library['library']}.json")))

        print(library, len(input_library_json))

        if library['type'] in NON_PROPOGATED_TYPE:
            print ("Writing Non Propogated Library")

            for spectrum in input_library_json:
                non_propogated_spectra_list.append(spectrum)
                propogated_spectra_list.append(spectrum)

                output_split_spectra_count += 1
                output_split_non_propogated_spectra_count += 1

            # lets append the MGF file to the merged one
            with open(os.path.join(args.input_folder, f"{library['library']}.mgf"), "r") as mgf_file:
                for line in mgf_file:
                    output_mgf_non_propogated.write(line)
                    output_mgf_all.write(line)

                    output_split_mgf_all_file.write(line)
                    output_split_mgf_non_propogated_all_file.write(line)
                
                output_mgf_non_propogated.write("\n\n")
                output_mgf_all.write("\n\n")

                output_split_mgf_all_file.write("\n\n")
                output_split_mgf_non_propogated_all_file.write("\n\n")

            # lets append the MSP file to the merged one
            with open(os.path.join(args.input_folder, f"{library['library']}.msp"), "r") as msp_file:
                for line in msp_file:
                    output_msp_non_propogated.write(line)
                    output_msp_all.write(line)

                    output_split_msp_all_file.write(line)
                    output_split_msp_non_propogated_all_file.write(line)
                
                output_msp_non_propogated.write("\n\n")
                output_msp_all.write("\n\n")

                output_split_msp_all_file.write("\n\n")
                output_split_msp_non_propogated_all_file.write("\n\n")
        
        elif library['type'] in PROPOGATED_TYPE:
            for spectrum in input_library_json:
                propogated_spectra_list.append(spectrum)

                output_split_spectra_count += 1

            # lets append the MGF file to the merged one
            with open(os.path.join(args.input_folder, f"{library['library']}.mgf"), "r") as mgf_file:
                for line in mgf_file:
                    output_mgf_all.write(line)

                    output_split_mgf_all_file.write(line)
                
                output_mgf_all.write("\n\n")

                output_split_mgf_all_file.write("\n\n")

            # lets append the MSP file to the merged one
            with open(os.path.join(args.input_folder, f"{library['library']}.msp"), "r") as msp_file:
                for line in msp_file:
                    output_msp_all.write(line)

                    output_split_msp_all_file.write(line)
                
                output_msp_all.write("\n\n")

                output_split_msp_all_file.write("\n\n")

        # Checking if the split exceeds 100K MS/MS spectra
        if output_split_spectra_count >= 100000:
            output_split_file_count += 1
            output_split_spectra_count = 0

            output_split_mgf_all_file.close()
            output_split_msp_all_file.close()

            output_split_mgf_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_SPLIT_{}.mgf".format(output_split_file_count)), "w")
            output_split_msp_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_SPLIT_{}.msp".format(output_split_file_count)), "w")

        if output_split_non_propogated_spectra_count >= 100000:
            output_split_non_propogated_file_count += 1
            output_split_non_propogated_spectra_count = 0

            output_split_mgf_non_propogated_all_file.close()
            output_split_msp_non_propogated_all_file.close()

            output_split_mgf_non_propogated_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED_SPLIT_{}.mgf".format(output_split_non_propogated_file_count)), "w")
            output_split_msp_non_propogated_all_file = open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED_SPLIT_{}.msp".format(output_split_non_propogated_file_count)), "w")


    # writing out the json file
    with open(os.path.join(args.output_folder, "ALL_GNPS.json"), "w") as propogated_json_file:
        json.dump(propogated_spectra_list, propogated_json_file, indent=4)

    with open(os.path.join(args.output_folder, "ALL_GNPS_NO_PROPOGATED.json"), "w") as non_propogated_json_file:
        json.dump(non_propogated_spectra_list, non_propogated_json_file, indent=4)


if __name__ == "__main__":
    main()