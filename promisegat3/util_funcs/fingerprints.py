import numpy as np
import os
import pickle
from Bio import SeqIO
import pandas as pd
from numpy import linalg as LA

max_residues = 2000


def dump_dictionary(dictionary, file_name):
    with open(file_name, "wb") as f:
        pickle.dump(dict(dictionary), f)


def parse_PDB(file_name):
    """
    Parse a PDB file to extract atomic coordinates and atom types.
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(file_name, "r", encoding="latin1") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_name, "rb") as f:  # Open as binary
                binary_content = f.read()
                # Assuming the content is in 'latin1' encoding. Change as necessary.
                lines = binary_content.decode("latin1", errors="replace").splitlines()

    coords = []
    atoms = []  # renamed from amino to atoms for clarity
    for line in lines:
        if line.startswith("ATOM") or line.startswith("HETATM"):
            x = float(line[30:38].strip())
            y = float(line[38:46].strip())
            z = float(line[46:54].strip())
            atom_type = line[
                12:16
            ].strip()  # Extract the atom type instead of the amino acid
            coords.append([x, y, z])
            atoms.append(atom_type)

    return coords, atoms


def parse_PDB_proteins(pdb_name, uniprot_id, user_chain, pdb_path):
    without_chain = False
    mdl = False
    # print("recevied ")

    try:
        if not user_chain == "0":
            for record in SeqIO.parse(pdb_name + ".pdb", "pdb-seqres"):
                pdb_id = record.id.strip().split(":")[0]
                chain = record.annotations["chain"]
                _, UNP_id = record.dbxrefs[0].strip().split(":")

                if UNP_id == uniprot_id:
                    chain = record.annotations["chain"]
                    if chain == user_chain:
                        break

            if not chain:
                chain = user_chain
        else:
            chain = user_chain
            without_chain = True
    except:
        chain = user_chain
    try:
        with open(pdb_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(pdb_path, "r", encoding="latin1") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(pdb_path, "rb") as f:  # Open as binary
                binary_content = f.read()
                # Assuming the content is in 'latin1' encoding. Change as necessary.
                lines = binary_content.decode("latin1", errors="replace").splitlines()

    # for ln in lines:
    #     print(ln)
    for ln in lines:
        if ln.startswith("NUMMDL"):
            mdl = True
            break

    id = []

    if mdl:
        for ln in lines:
            if ln.startswith("ATOM") or ln.startswith("HETATM"):
                id.append(ln)
            elif ln.startswith("ENDMDL"):
                break
    else:
        for ln in lines:
            if ln.startswith("ATOM") or ln.startswith("HETATM"):
                id.append(ln)

    count = 0
    seq = {}
    seq["type_atm"], seq["ind"], seq["amino"], seq["group"], seq["coords"] = (
        [],
        [],
        [],
        [],
        [],
    )

    for element in id:
        # print(element)
        type_atm = element[0:6].strip().split()[0]
        ind = int(element[6:12].strip().split()[0])
        atom = element[12:17].strip().split()[0]
        amino = element[17:21].strip().split()[0]
        chain_id = element[21]
        group_id = int(element[22:26].strip().split()[0])
        x_coord = float(element[30:38].strip().split()[0])
        y_coord = float(element[38:46].strip().split()[0])
        z_coord = float(element[46:54].strip().split()[0])

        coords = np.array([x_coord, y_coord, z_coord])
        # print(type_atm, amino, group_id, coords,chain_id)
        if not without_chain:
            # if chain_id == chain:
            seq["type_atm"].append(type_atm)
            seq["ind"].append(int(ind))
            seq["amino"].append(amino)
            seq["group"].append(int(group_id))
            seq["coords"].append(coords)

            count += 1
        else:
            seq["type_atm"].append(type_atm)
            seq["ind"].append(int(ind))
            seq["amino"].append(amino)
            seq["group"].append(int(group_id))
            seq["coords"].append(coords)

            count += 1
    # print(seq["type_atm"])
    # print(seq["amino"])
    # print(seq["group"])
    # print(seq["coords"])
    return count, seq["type_atm"], seq["amino"], seq["group"], seq["coords"], chain


def group_by_coords(group, amino, coords):
    uniq_group = np.unique(group)
    group_coords = np.zeros((uniq_group.shape[0], 3))

    group_amino = []

    np_group = np.array(group)

    for i, e in enumerate(uniq_group):
        inds = np.where(np_group == e)[0]
        group_coords[i, :] = np.mean(np.array(coords)[inds], axis=0)
        group_amino.append(amino[inds[0]])

    return group_coords, group_amino


def create_amino_acids(acids, acid_dict, amino_list):
    retval = [
        (
            acid_dict[acid_name]
            if acid_name in amino_list
            else acid_dict["MET"] if acid_name == "FME" else acid_dict["TMP"]
        )
        for acid_name in acids
    ]
    retval = np.array(retval)

    return np.array(retval)


def get_protein_graph_from_struct(group_coords, group_amino, amino_list):
    num_residues = group_coords.shape[0]

    if num_residues > max_residues:
        num_residues = max_residues

    residues = group_amino[:num_residues]

    retval = [[0 for i in range(0, num_residues)] for j in range(0, num_residues)]

    residue_type = []
    for i in range(0, num_residues):
        if residues[i] == "FME":
            residues[i] = "MET"
        elif residues[i] not in amino_list:
            residues[i] = "TMP"

        residue_type.append(residues[i])

        for j in range(i + 1, num_residues):
            x, y = group_coords[i], group_coords[j]
            retval[i][j] = LA.norm(x - y)
            retval[j][i] = retval[i][j]

    retval = np.array(retval)

    threshold = 9.5

    for i in range(0, num_residues):
        for j in range(0, num_residues):
            if retval[i, j] <= threshold:
                retval[i, j] = 1
            else:
                retval[i, j] = 0

    n = retval.shape[0]
    adjacency = retval + np.eye(n)
    degree = sum(adjacency)
    d_half = np.sqrt(np.diag(degree))
    d_half_inv = np.linalg.inv(d_half)
    adjacency = np.matmul(d_half_inv, np.matmul(adjacency, d_half_inv))
    return residue_type, np.array(adjacency)


def get_graph_from_struct(coords, atoms):
    """
    Compute an adjacency matrix based on atomic distances.
    """
    atom_list = ["H", "C", "N", "O", ...]  # Updated with expected atom types
    adj_matrix = np.zeros((len(coords), len(coords)))

    for i in range(len(coords)):
        for j in range(len(coords)):
            if i != j:
                dist = np.linalg.norm(np.array(coords[i]) - np.array(coords[j]))

                # Use a more refined condition to determine adjacency. Here, I'm using a generic threshold,
                # but you might use specific bond lengths or other criteria
                if dist < 2:
                    adj_matrix[i, j] = 1

    # Normalize the adjacency matrix
    n = adj_matrix.shape[0]
    degree = np.sum(adj_matrix, axis=1)  # compute the degree of each node
    d_half = np.sqrt(np.diag(degree))  # compute the square root of the degree matrix
    d_half_inv = np.linalg.inv(
        d_half
    )  # compute the inverse of the square root of the degree matrix
    normalized_adj_matrix = np.matmul(
        d_half_inv, np.matmul(adj_matrix + np.eye(n), d_half_inv)
    )  # normalize the adjacency matrix

    return normalized_adj_matrix


def create_fingerprints(atoms, adjacency, radius, fingerprint_dict):
    """Extract r-radius subgraphs (i.e., fingerprints)
    from a molecular graph using WeisfeilerLehman-like algorithm."""
    atoms = np.array(atoms)

    fingerprints = []
    if (len(atoms) == 1) or (radius == 0):
        fingerprints = [fingerprint_dict[a] for a in atoms]
    else:
        for i in range(len(atoms)):
            vertex = atoms[i]
            neighbors = tuple(
                set(tuple(sorted(atoms[np.where(adjacency[i] > 0.0001)[0]])))
            )
            fingerprint = (vertex, neighbors)
            fingerprints.append(fingerprint_dict[fingerprint])

    return np.array(fingerprints)


def create_protein_fingerprints(atoms, adjacency, radius, fingerprint_dict):
    """Extract r-radius subgraphs (i.e., fingerprints)
    from a molecular graph using WeisfeilerLehman-like algorithm."""

    fingerprints = []
    if (len(atoms) == 1) or (radius == 0):
        fingerprints = [fingerprint_dict[a] for a in atoms]
    else:
        for i in range(len(atoms)):
            vertex = atoms[i]
            neighbors = tuple(
                set(tuple(sorted(atoms[np.where(adjacency[i] > 0.0001)[0]])))
            )
            fingerprint = (vertex, neighbors)
            fingerprints.append(fingerprint_dict[fingerprint])
    # print(fingerprints)
    return np.array(fingerprints)


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_chem_features(csv_file):
    df = pd.read_csv(csv_file, header=None)
    chem_features = df.iloc[8:, 1:]
    chem_features = chem_features.fillna(0)

    # Convert non-numeric strings to 0
    chem_features = chem_features.applymap(
        lambda x: (
            float(x)
            if isinstance(x, str) and is_float(x)
            else (x if isinstance(x, (int, float)) else 0)
        )
    )

    chem_features = chem_features.values

    return chem_features


def save_fingerprints(
    dir_input, q_count, proteins, adjacencies, pnames, chem_features=None
):
    try:
        np.save(
            dir_input
            + "proteins_"
            + str(10 * q_count + 1)
            + "_"
            + str(10 * (q_count + 1)),
            proteins,
            allow_pickle=1,
        )
    except Exception as e:
        print(f"Failed saving proteins: {e}")
    try:
        np.save(
            dir_input
            + "adjacencies_"
            + str(10 * q_count + 1)
            + "_"
            + str(10 * (q_count + 1)),
            adjacencies,
            allow_pickle=1,
        )
    except Exception as e:
        print(f"Failed saving adjencies: {e}")

    try:
        np.save(
            dir_input
            + "pnames_"
            + str(10 * q_count + 1)
            + "_"
            + str(10 * (q_count + 1)),
            pnames,
            allow_pickle=1,
        )
    except Exception as e:
        print(f"Failed saving names: {e}")
    if chem_features is not None:
        # print(f"chemfeatures: {chem_features}")
        try:
            np.save(
                dir_input
                + "chem_features_"
                + str(10 * q_count + 1)
                + "_"
                + str(10 * (q_count + 1)),
                chem_features,
                allow_pickle=1,
            )
        except Exception as e:
            print(f"Failed saving chem features: {e}")
    # print(f"successfully saved proteins {10 * q_count + 1} to {10 * (q_count + 1)}")
