import os
import random
import pandas as pd


def get_other_folders(target_name,target_pdb_path):
    return [
        d
        for d in os.listdir(target_pdb_path)
        if os.path.isdir(os.path.join(target_pdb_path, d)) and d != target_name
    ]


def write_to_output(inchikey_path, filepath, label, mod_list, training_data_path):
    with open(training_data_path, "a") as output:
        output.write(f"{inchikey_path}\t{filepath}\t{label}\n")
        mod_list.append(filepath)


def process_target_folder(target_name, inchikey_path, mod_list, training_data_path,target_pdb_path):
    target_folder_cnt=0
    target_folder = os.path.join(target_pdb_path, target_name)
    print(f"doing at {target_folder}")
    if os.path.exists(target_folder):
        for file in os.listdir(target_folder):
            filepath = os.path.join(target_folder, file)
            write_to_output(inchikey_path, filepath, 1, mod_list, training_data_path)
            print(f"Writing to output for {inchikey_path} and {filepath}")
            target_folder_cnt+=1
    return target_folder_cnt

def process_other_folders(target_name, inchikey_path, mod_list, training_data_path, target_pdb_path):
    other_folder_cnt=0
    other_folders = get_other_folders(target_name, target_pdb_path)
    random_other_folders = random.sample(other_folders, 5)  # Randomly choose 5 other folders
    for other_folder in random_other_folders:
        other_folder_path = os.path.join(target_pdb_path, other_folder)
        files = os.listdir(other_folder_path)
        if files:  # Check if the list is not empty
            random_file = random.choice(files)
            filepath = os.path.join(other_folder_path, random_file)
            write_to_output(inchikey_path, filepath, 0, mod_list, training_data_path)
            other_folder_cnt+=1
    return other_folder_cnt

def process_csv_file(csv_path, name_map, targets, mod_list, training_data_path,target_pdb_path):
    target_name = None
    inchikey = None
    matches = 0
    df = pd.read_csv(csv_path, header=None)
    target_name_table = df[df[0] == "Common Target Pref Name"]
    if not target_name_table.empty:
        target_name = target_name_table.iloc[0, 1]
    else:
        target_name = None
    inchikey_table = df[df[0] == "Standard Inchi Key(RDKit)"]
    if not inchikey_table.empty:
        inchikey = inchikey_table.iloc[0, 1]
    else:
        inchikey = None

    same_folder_cnt=0
    other_folder_total_cnt=0
    if target_name is not None and inchikey is not None:
        print(f"target_name={target_name}, inchikey={inchikey}")
        matches += 1
        inchikey_path = f"sdf_files/{inchikey}.pdb"
        try:
            target_name = name_map[target_name]
        except KeyError:
            pass
        same_folder_cnt += process_target_folder(target_name, inchikey_path, mod_list, training_data_path,target_pdb_path)
        other_folder_total_cnt += process_other_folders(target_name, inchikey_path, mod_list, training_data_path,target_pdb_path)
    # else:
    # print(f"No match for {target_name} or {inchikey}")
    return matches,same_folder_cnt,other_folder_total_cnt
