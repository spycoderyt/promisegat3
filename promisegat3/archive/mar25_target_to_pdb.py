#the script doeosn towrk
import os
import requests
from urllib.parse import quote

def download_protein(protein_name):
    # Create a folder to store the downloaded protein
    folder_name = "downloaded_proteins"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Construct the UniProt search URL
    query = f"({protein_name}) AND (model_organism:9606)"
    encoded_query = quote(query)
    url = f"https://rest.uniprot.org/uniprotkb/search?compressed=true&format=fasta&query={encoded_query}&size=500"

    # Download the FASTA file
    response = requests.get(url)

    if response.status_code == 200:
        # Save the FASTA file
        file_name = f"{folder_name}/{protein_name}.fasta"
        with open(file_name, "wb") as file:
            file.write(response.content)

        print(f"Downloaded FASTA for protein: {protein_name}")
        print(f"Saved as: {file_name}")
    else:
        print(f"Failed to download FASTA for protein: {protein_name}")
        print(f"Status code: {response.status_code}")

# Example usage
protein_name = input("Enter the protein name: ")
download_protein(protein_name)