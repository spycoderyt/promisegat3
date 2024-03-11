import pandas as pd
import os


def get_targets_from_file(filename):
    targets = set()
    df = pd.read_csv(filename, header=None)
    for index, row in df.iterrows():
        if row[0] == "Common Target Pref Name":
            targets.add(row[1])
            break
    return targets


def get_all_targets(folder_path):
    files = 0
    all_targets = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            targets = get_targets_from_file(os.path.join(folder_path, filename))
            all_targets.update(targets)
            files += 1
    return all_targets


def write_targets_to_file(targets, output_filename):
    with open(output_filename, "w") as output_file:
        for target_name in sorted(targets):  # Sort to have consistent order
            output_file.write(target_name + "\n")
