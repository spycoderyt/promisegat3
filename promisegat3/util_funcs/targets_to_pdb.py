import requests
import pandas as pd
import tempfile
import random
from rdkit import Chem
import os 

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


def get_cids_from_csv(csv_file_path, target):
    df = pd.read_csv(csv_file_path)
    cids_column = "cid" if target == "Beta-catenin" else "cids"
    cids = df[df[cids_column] != "NULL"][cids_column].str.split("|").explode().tolist()
    random.shuffle(cids)
    return cids[:10]


def process_cid(cid, target_folder_path):
    cid_path = f"{target_folder_path}/{cid}.pdb"
    conformer_ids = get_conformer_ids_from_cid(cid)
    print(conformer_ids)
    try:
        first_conformer_id = conformer_ids["InformationList"]["Information"][0][
            "ConformerID"
        ][0]
        sdf = get_sdf_from_conformer_id(first_conformer_id)
        if sdf is not None:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_sdf_file:
                temp_sdf_file.write(sdf)
            mol_supplier = Chem.SDMolSupplier(temp_sdf_file.name)
            for i, mol in enumerate(mol_supplier):
                if mol is not None:
                    Chem.MolToPDBFile(mol, cid_path)
                    print(f"Processed {cid_path}")
        else:
            print(f"SDF IS NONE@!!!! for {cid_path}")
    except Exception as e:
        print(f"didnt work: {e}")


def process_target(target):
    print(f"Doing {target}")
    target = target.strip()
    target_folder_path = os.path.join("target_files", target)
    if not os.path.exists(target_folder_path):
        os.mkdir(target_folder_path)
    else:
        return

    csv_file_path = os.path.join("target_csv", target + ".csv")
    print(f"{csv_file_path}")

    if os.path.exists(csv_file_path):
        cids = get_cids_from_csv(csv_file_path, target)
        for cid in cids:
            process_cid(cid, target_folder_path)
    else:
        print(f"No CSV file found for target {target}")


def process_targets(target_names):
    for target in target_names:
        process_target(target)
    print("Download completed!")
