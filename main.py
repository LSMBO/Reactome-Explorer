# python main.py -mode proteins -accessions test_input_proteins.txt
# python main.py -mode metabolites -accessions test_input_metabolites.txt
# Generate and override Reactome_Pathways.json, Reactome_Pathways_Maps.html and Reactome_Pathways_Maps.xlsx

import argparse
import ujson
import src.metabolites as metabo
import src.proteins as prot
import tqdm as tqdm

parser = argparse.ArgumentParser()
parser.add_argument("-mode", choices=["metabolites", "proteins"], required=True)
parser.add_argument("-accessions", required=True)
parser.add_argument("--output-html", default="./Reactome_Pathways_Maps.html", required=False)
parser.add_argument("--output-excel", default="./Reactome_Pathways_Maps.xlsx", required=False)
parser.add_argument("--output-json", default="./Reactome_Pathways.json", required=False)

args = parser.parse_args()

output_data = {}

with open(args.accessions, "r") as f:
    accessions = [line.strip() for line in f.readlines()]
        
for accession in tqdm.tqdm(accessions):
    if args.mode == "metabolites":
        output_data[accession] = metabo.search_reactome_metabolite(accession)
    elif args.mode == "proteins":
        output_data[accession] = prot.search_reactome_protein(accession)

for accession, reactome_data in output_data.items():
    if args.mode == "metabolites":
        output_data[accession]["pathways_maps"] = metabo.get_metabolite_maps(reactome_data)
    elif args.mode == "proteins":
        output_data[accession]["pathways_maps"] = prot.get_protein_maps(accession, reactome_data)

with open(args.output_json, "w") as f:
    ujson.dump(output_data, f, indent=2)

if args.mode == "metabolites":
    metabo.create_html(output_data, args.output_html)
    metabo.create_excel(output_data, args.output_excel)
elif args.mode == "proteins":
    prot.create_html(output_data, args.output_html)
    prot.create_excel(output_data, args.output_excel)
