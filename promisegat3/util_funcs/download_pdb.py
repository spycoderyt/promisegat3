import requests
import json
import os
import csv
import tempfile
import re
import pandas as pd
from rdkit import Chem


def get_info_from_pubchem(inchikey):
    response = requests.get(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/{inchikey}/JSON"
    )
    if response.status_code == 200:
        return response.json()  # Access the JSON data using .json property
    else:
        return None


def get_conformer_ids_from_cid(cid):
    response = requests.get(
        f" https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/conformers/JSON"
    )
    if response.status_code == 200:
        return response.json()  # Access the JSON data using .json property
    else:
        return None


def get_sdf_from_conformer_id(conformer_id):
    response = requests.get(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/conformers/{conformer_id}/SDF"
    )
    if response.status_code == 200:
        return response.text  # Access the JSON data using .json property
    else:
        return None


def get_sdf_from_csv(csv_path):
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        inchikey = None
        for i, row in enumerate(reader):
            if i == 4:
                inchikey = row[1]
                break
        if inchikey is None:
            print("InChIKey not found in the CSV file.")
            return None
    print(inchikey)
    info = get_info_from_pubchem(inchikey)
    if info is None:
        print("Failed to retrieve information from PubChem.")
        return None

    cid = info["PC_Compounds"][0]["id"]["id"]["cid"]
    print(f"Compound ID (CID): {cid}")

    conformer_ids = get_conformer_ids_from_cid(cid)
    if conformer_ids is None:
        print("Failed to retrieve conformer IDs from PubChem.")
        return None
    print(json.dumps(conformer_ids, indent=4))

    first_conformer_id = conformer_ids["InformationList"]["Information"][0][
        "ConformerID"
    ][0]
    print(f"First Conformer ID: {first_conformer_id}")

    sdf = get_sdf_from_conformer_id(first_conformer_id)
    if sdf is None:
        print("Failed to retrieve SDF data from PubChem.")
        return None

    return sdf, inchikey


def slugify(name):
    return re.sub(r"[\W_.-]+", "-", name)


def process_sdf(sdf, pdb_file_path):
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_sdf_file:
        temp_sdf_file.write(sdf)
    mol_supplier = Chem.SDMolSupplier(temp_sdf_file.name)
    for i, mol in enumerate(mol_supplier):
        if mol is not None:
            Chem.MolToPDBFile(mol, pdb_file_path)
            print(f"Processed {pdb_file_path}")
            return True
    print("mol is none")
    return False


def process_file(root, file, list_of_failures, downloads_path, sdf_to_csv):
    name = None
    # try:
    #     with open(os.path.join(root,file),'r') as csv_file:
    #         reader = csv.reader(csv_file)
    #         for i,row in enumerate(reader):
    #             if(i==4):
    #                 name = row[1]
    #                 break
    #     pdb_file_path = f'{downloads_path}{slugify(name)}.pdb'
    #     print(pdb_file_path)
    try:
        df = pd.read_csv(os.path.join(root, file), header=None)
        name = df.iloc[4, 1]
        pdb_file_path = f"{downloads_path}{slugify(name)}.pdb"
        print(pdb_file_path)
        open(sdf_to_csv, "a").write(f"{pdb_file_path}\t{os.path.join(root,file)}\n")

    except Exception as e:
        print(f"Reading problem in file {file}: {e}")
        list_of_failures.append(name)
        return False
    if not os.path.exists(pdb_file_path):
        try:
            sdf, inchikey = get_sdf_from_csv(os.path.join(root, file))
            if sdf is not None:
                return process_sdf(sdf, pdb_file_path)
        except Exception as e:
            print(f"Problem processing SDF for file {file}: {e}")
            list_of_failures.append(name)
            return False
    else:
        print(f"File {file} already exists")
        return True


def process_directory(path, downloads_path, sdf_to_csv):
    idx = 0
    total = 0
    success = 0
    already_exist = 0
    failed = 0
    new_added = 0
    list_of_failures = []
    for root, dirs, files in os.walk(path):
        for file in files:
            idx += 1
            print(f"idx = {idx}")
            if file.endswith(".csv"):
                total += 1
                if process_file(
                    root, file, list_of_failures, downloads_path, sdf_to_csv
                ):
                    success += 1
                else:
                    failed += 1
            if idx % 50 == 0:
                print(
                    f"success = {success}, exist = {already_exist}, failed = {failed}"
                )
    print(f"success = {success}, exist = {already_exist}, failed = {failed}")
