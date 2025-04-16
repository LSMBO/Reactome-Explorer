import requests
import src.general_methods as gm
import brexcel

def get_uniprot_protein_name(uniprot_accession):
    if '|' in uniprot_accession:
        uniprot_accession = uniprot_accession.split('|')[1]
    params = {
        "fields": [
            "protein_name"
        ]
    }
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_accession}"
    response = requests.get(url, params=params)
    data = response.json()
    if 'proteinDescription' not in data:
        return uniprot_accession
    return data["proteinDescription"]['recommendedName']['fullName']["value"]

def search_reactome_protein(uniprot_accession):
    reactome = {
        "name": get_uniprot_protein_name(uniprot_accession),
        "pathways": {}
    }
    url = f"https://reactome.org/ContentService/search/query?query={uniprot_accession}&types=Protein"
    data = gm.send_request(url)
    if not data:
        return reactome
    
    url = f"https://reactome.org/AnalysisService/identifier/{uniprot_accession}"
    data = gm.send_request(url)
    for pathway in data["pathways"]:
        reactome["pathways"][pathway["stId"]] = {
            "name": pathway["name"],
            "species": pathway["species"]["name"]
        }

    return reactome

def get_protein_maps(accession, protein_data):
    pathway_maps = []
    if "pathways" not in protein_data:
        return pathway_maps
    for pathway_id in protein_data["pathways"].keys():
        pathway_map_url = f"https://reactome.org/PathwayBrowser/#/{pathway_id}&FLG={accession}"
        pathway_map_name = protein_data["pathways"][pathway_id]["name"]
        pathway_maps_species = protein_data["pathways"][pathway_id]["species"]
        pathway_maps.append({
            "url": pathway_map_url,
            "name": pathway_map_name,
            "species": pathway_maps_species
        })
    return pathway_maps

def create_html(output_data, output_directory):
    with open(f"{output_directory}/Reactome_Pathways_Maps.html", 'w', encoding='utf-8') as f:
        for accession, reactome in output_data.items():
            f.write(f"<h1>{accession} ({reactome['name']})</h1>")
            if reactome["pathways_maps"]:
                f.write(f"<label>{len(reactome['pathways_maps'])} maps:</label>\n")
                f.write("<ul>\n")
                for map in reactome["pathways_maps"]:
                    f.write(f'<li><a href="{map['url']}">{map['name']} ({map['species']})</a>')
                    f.write('</li>\n')
                f.write("</ul>\n")
            else:
                f.write(f"<label>Nothing found</label>\n")

def create_excel(output_data, output_directory):
    excel_data = {
        "Query": [],
        "Found": [],
        "Protein name": [],
        "Pathway names": [],
        "Pathway counts": []
    }
    for accession, reactome in output_data.items():
        excel_data["Query"].append(accession)
        if reactome["pathways_maps"]:
            excel_data["Found"].append("True")
            excel_data["Protein name"].append(reactome["name"])
            
            pathway_names = [map["name"] for map in reactome["pathways_maps"]]
            pathway_names_str = ';'.join(pathway_names)
            excel_data["Pathway names"].append(pathway_names_str)
            excel_data["Pathway counts"].append(len(pathway_names))
        else:
            excel_data["Found"].append("False")
            excel_data["Protein name"].append("")
            excel_data["Pathway names"].append("")
            excel_data["Pathway counts"].append(0)
    
    brexcel.write_excel(excel_data, f"{output_directory}/Reactome_Pathways_Table.xlsx")


