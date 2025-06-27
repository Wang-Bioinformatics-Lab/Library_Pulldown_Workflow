import sys
import argparse
import pandas as pd
import requests
import random
import json

try:
    from rdkit import Chem
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
except:
    pass

# debugging
import requests_cache
requests_cache.install_cache('gnps_cache')
    
def get_inchikey(smiles, inchi):
    inchikey_from_smiles = ""
    inchikey_from_inchi = ""
    try:
        if len(smiles) > 5:
            inchikey_from_smiles = str(Chem.MolToInchiKey(Chem.MolFromSmiles(smiles)))
        else:
            inchikey_from_smiles = ""
    except:
        inchikey_from_smiles = ""

    try:
        if len(inchi) > 5:
            inchikey_from_inchi = str(Chem.InchiToInchiKey(inchi))
        else:
            inchikey_from_inchi = ""
    except:
        inchikey_from_inchi = ""

    if len(inchikey_from_smiles) > 2 and len(inchikey_from_inchi) > 2:
        return inchikey_from_smiles, inchikey_from_inchi

    if len(inchikey_from_smiles) > 2:
        return inchikey_from_smiles, ""

    if len(inchikey_from_inchi) > 2:
        return inchikey_from_inchi, ""

    return "", ""

def get_formula(smiles, inchi):
    formula_from_smiles = ""
    formula_from_inchi = ""
    try:
        if len(smiles) > 5:
            formula_from_smiles = str(CalcMolFormula(Chem.MolFromSmiles(smiles)))
        else:
            formula_from_smiles = ""
    except:
        formula_from_smiles = ""

    try:
        if len(inchi) > 5:
            formula_from_inchi = str(CalcMolFormula(Chem.MolFromInchi(inchi)))
        else:
            formula_from_inchi = ""
    except:
        formula_from_inchi = ""

    if len(formula_from_smiles) > 2 and len(formula_from_inchi) > 2:
        return formula_from_smiles, formula_from_inchi

    if len(formula_from_smiles) > 2:
        return formula_from_smiles, ""

    if len(formula_from_inchi) > 2:
        return formula_from_inchi, ""

    return "", ""

# Enriching GNPS Library data with structures and formulas
def gnps_library_enrich_structures(all_GNPS_list):
    from tqdm import tqdm

    all_spectra = []
    for spectrum in tqdm(all_GNPS_list):
        smiles = spectrum["Smiles"]
        inchi =  spectrum["INCHI"]

        if len(smiles) < 5 and len(inchi) < 5:
            inchikey_from_smiles = ""
            inchikey_from_inchi = ""
            formula_from_smiles = ""
            formula_from_inchi = ""
        else:
            if "InChI=" not in inchi and len(inchi) > 10:
                inchi = "InChI=" + inchi

            # TODO: We gotta fix this and also just get rid of rdkit from the dependencies
            inchikey_from_smiles, inchikey_from_inchi = get_inchikey(smiles, inchi)
            formula_from_smiles, formula_from_inchi = get_formula(smiles, inchi)

        spectrum_object = spectrum
        spectrum_object["InChIKey_smiles"] = inchikey_from_smiles
        spectrum_object["InChIKey_inchi"] = inchikey_from_inchi
        spectrum_object["Formula_smiles"] = formula_from_smiles
        spectrum_object["Formula_inchi"] = formula_from_inchi
        spectrum_object["url"] = "https://gnps.ucsd.edu/ProteoSAFe/gnpslibraryspectrum.jsp?SpectrumID=%s" % spectrum["spectrum_id"]

        all_spectra.append(spectrum_object)

    return all_spectra

# Getting all the spectrum peaks for the library spectrum
def gnps_library_enrich_peaks(all_GNPS_list):
    import copy
    from tqdm import tqdm

    api_url = "http://externalstructureproxy-web:5000/"

    try:
        # checking the heartbeat
        r = requests.get(api_url + "heartbeat")
        r.raise_for_status()  # Raise an error for bad responses
    except:
        api_url = "https://external.gnps2.org/"

    output_list = []
    for spectrum in tqdm(all_GNPS_list):
        new_spectrum = copy.deepcopy(spectrum)
        try:
            # We first try to get it locally
            spectrum_peaks_url = "{}/gnpsspectrum?SpectrumID={}".format(api_url, spectrum["spectrum_id"])
            r = requests.get(spectrum_peaks_url)
            spectrum_json = r.json()
            new_spectrum["peaks_json"] = spectrum_json["spectruminfo"]["peaks_json"]
            new_spectrum["annotation_history"] = spectrum_json["annotations"]
            output_list.append(new_spectrum)

        except KeyboardInterrupt:
            raise
        except:
            continue

    return output_list

# now we will actually format and output
def _output_library_files(library_spectra_list_with_peaks, output_folder, library_name):
    if len(library_spectra_list_with_peaks) > 0:
        with open(os.path.join(output_folder, "{}.mgf".format(library_name)), "wb") as output_file:
            output_file.write(get_full_mgf_string(library_spectra_list_with_peaks).encode("ascii", "ignore"))

        with open(os.path.join(output_folder, "{}.msp".format(library_name)), "wb") as output_file:
            output_file.write(get_full_msp_string(library_spectra_list_with_peaks).encode("ascii", "ignore"))

        with open(os.path.join(output_folder, "{}.json".format(library_name)), "w") as output_file:
            output_file.write(json.dumps(library_spectra_list_with_peaks, indent=4))

def get_full_mgf_string(all_json_list):
    mgf_string_list = []

    for spectrum in all_json_list:
        mgf_string_list.append(json_to_mgf(spectrum))

    return "\n".join(mgf_string_list)


def get_full_msp_string(all_json_list):
    msp_string_list = []
    
    for spectrum in all_json_list:
        try:
            msp_string = json_to_msp(spectrum)
            if msp_string is not None:
                msp_string_list.append(msp_string)
        except KeyboardInterrupt:
            raise
        except:
            pass

    return "\n".join(msp_string_list)

def json_to_mgf(json_spectrum):
    #print(json_spectrum["SpectrumID"])
    
    if int(json_spectrum["Library_Class"]) > 4:
        #print("CHALLENGE OR UNKNOWN CLASS, SKIPPING: " + json_spectrum["Library_Class"] + "\t" + json_spectrum["SpectrumID"])
        return ""
    
    mgf_string = "BEGIN IONS\n"
    mgf_string += "PEPMASS=" + json_spectrum["Precursor_MZ"] + "\n"
    mgf_string += "CHARGE=" + json_spectrum["Charge"] + "\n"
    mgf_string += "MSLEVEL=2" + "\n"
    mgf_string += "SOURCE_INSTRUMENT=" + json_spectrum["Ion_Source"] + "-" + json_spectrum["Instrument"] + "\n"
    mgf_string += "FILENAME=" + json_spectrum["source_file"] + "\n"
    mgf_string += "SEQ=*..*" + "\n"
    mgf_string += "IONMODE=" + json_spectrum["Ion_Mode"] + "\n"
    mgf_string += "ORGANISM=" + json_spectrum["library_membership"] + "\n"
    mgf_string += "NAME=" + json_spectrum["Compound_Name"] + " " + json_spectrum["Adduct"] + "\n"
    
    mgf_string += "PI=" + json_spectrum["PI"] + "\n"
    mgf_string += "DATACOLLECTOR=" + json_spectrum["Data_Collector"] + "\n"
    mgf_string += "SMILES=" + json_spectrum["Smiles"] + "\n"
    mgf_string += "INCHI=" + json_spectrum["INCHI"] + "\n"
    mgf_string += "INCHIAUX=" + json_spectrum["INCHI_AUX"] + "\n"
    mgf_string += "PUBMED=" + json_spectrum["Pubmed_ID"] + "\n"
    mgf_string += "SUBMITUSER=" + json_spectrum["submit_user"] + "\n"
    
    
    mgf_string += "LIBRARYQUALITY=" + json_spectrum["Library_Class"] + "\n"
    mgf_string += "SPECTRUMID=" + json_spectrum["SpectrumID"] + "\n"
    mgf_string += "SCANS=" + json_spectrum["scan"] + "\n"
    
    peaks_json = json_spectrum["peaks_json"]
    
    if len(peaks_json) < 1000000:
        peaks_object = json.loads(peaks_json)
        for peak in peaks_object:
            if peak[1] > 0:
                mgf_string += str(peak[0]) + "\t" + str(peak[1]) + "\n"
    # else:
    #     print("SKIPPING: " + json_spectrum["SpectrumID"] + " " + str(len(peaks_json)))
    
    mgf_string += "END IONS\n\n"
    
    return mgf_string

#output libraries into MSDial usable msp
def json_to_msp(json_spectrum):
    #print(json_spectrum["SpectrumID"])
    if int(json_spectrum["Library_Class"]) > 3:
        #print("CHALLENGE OR UNKNOWN CLASS, SKIPPING: " + json_spectrum["Library_Class"] + "\t" + json_spectrum["SpectrumID"])
        return ""

    

    # Determine inchikey
    inchi_key = json_spectrum["InChIKey_inchi"]
    if len(inchi_key) < 5 and len(json_spectrum["InChIKey_smiles"]) > 5:
        inchi_key = json_spectrum["InChIKey_smiles"]

    # Determine formula
    formula = json_spectrum["Formula_smiles"]
    if len(formula) < 5 and len(json_spectrum["Formula_inchi"]) > 5:
        formula = json_spectrum["Formula_inchi"]
    
    msp_string = "NAME: " + json_spectrum["Compound_Name"] + "\n"
    msp_string += "PRECURSORMZ: " + json_spectrum["Precursor_MZ"] + "\n"
    msp_string += "PRECURSORTYPE: " + json_spectrum["Adduct"] + "\n"
    msp_string += "FORMULA: {}\n".format(formula)
    msp_string += "Ontology: \n"
    msp_string += "INCHIKEY: {}\n".format(inchi_key)
    msp_string += "INCHI: " + json_spectrum["INCHI"] + "\n"
    msp_string += "SMILES: " + json_spectrum["Smiles"] + "\n"
    msp_string += "RETENTIONTIME: "
    msp_string += "CCS: \n"
    msp_string += "IONMODE: " + json_spectrum["Ion_Mode"] + "\n"
    msp_string += "INSTRUMENTTYPE: "  + json_spectrum["Ion_Source"] + "-" + json_spectrum["Instrument"] + "\n"
    msp_string += "INSTRUMENT: " + json_spectrum["Instrument"] + "\n"
    msp_string += "COLLISIONENERGY: \n"
    msp_string += "Comment: DB#=" + json_spectrum["SpectrumID"] + "; origin=" + "GNPS\n"

    peaks_json = json_spectrum["peaks_json"]

    if len(peaks_json) < 1000000:
        peaks_list = json.loads(peaks_json)
        peaks_list = [peak for peak in peaks_list if peak[1] > 0]

        if len(peaks_list) == 0:
            return None

        msp_string += "Num Peaks: " + str(len(peaks_list)) +  "\n"
        for peak in peaks_list:
            msp_string += str(peak[0]) + "\t" + str(peak[1]) + "\n"
    # else:
    #     print("SKIPPING: " + json_spectrum["SpectrumID"] + " " + str(len(peaks_json)))
    
    msp_string += "\n"
    
    return msp_string

def main():
    parser = argparse.ArgumentParser(description='Test write out a file.')
    parser.add_argument('input_json')
    parser.add_argument('output_folder')

    args = parser.parse_args()

    # loading the json file
    spectra_json = json.loads(open(args.input_json, 'r').read())

    # enriching with structures and formula
    spectra_list = gnps_library_enrich_structures(spectra_json["spectra"])

    # enriching with peaks
    spectra_list = gnps_library_enrich_peaks(spectra_list)

    # we'll need to save
    _output_library_files(spectra_list, args.output_folder, os.path.basename(args.input_json).replace(".json", ""))

if __name__ == "__main__":
    main()