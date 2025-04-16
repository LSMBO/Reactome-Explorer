import src.general_methods as gm
import brexcel

def search_reactome_metabolite(metabolite_name):
    reactome = {
        "names": [],
        "chebi": {},
        "pathways": {}
    }
    url = f"https://reactome.org/ContentService/search/query?query={metabolite_name}&types=Chemical%20Compound"
    data = gm.send_request(url)
    if not data:
        return reactome

    for entry in data["results"][0]['entries']:
        reactome["names"].append(entry["name"]) if entry["name"] not in reactome["names"] else None
        if "chebiId=CHEBI:" in entry["referenceURL"]:
            chebi = entry["referenceURL"].split("chebiId=CHEBI:")[1]
            if chebi not in reactome["chebi"]:
                reactome["chebi"][chebi] = entry['referenceName']
            reactome["chebi"].append(chebi) if chebi not in reactome["chebi"] else None

    for chebi in reactome["chebi"].keys():
        url = f"https://reactome.org/AnalysisService/identifier/{chebi}"
        data = gm.send_request(url)
        for pathway in data["pathways"]:
            if pathway["stId"] in reactome["pathways"]:
                chebi_list = reactome["pathways"][pathway["stId"]]["chebi"] + [chebi]
            else:
                chebi_list = [chebi]

            reactome["pathways"][pathway["stId"]] = {
                "name": pathway["name"],
                "species": pathway["species"]["name"],
                "chebi": chebi_list
            }

    return reactome

def get_metabolite_maps(metabolite_data):
    pathway_maps = []
    if "pathways" not in metabolite_data:
        return pathway_maps
    for pathway_id in metabolite_data["pathways"].keys():
        chebi_list = metabolite_data['pathways'][pathway_id]['chebi']
        for chebi in chebi_list:
            pathway_map_url = f"https://reactome.org/PathwayBrowser/#/{pathway_id}&FLG={chebi}"
            pathway_map_name = metabolite_data["pathways"][pathway_id]["name"]
            pathway_maps_species = metabolite_data["pathways"][pathway_id]["species"]
            pathway_maps.append({
                "url": pathway_map_url,
                "name": pathway_map_name,
                "species": pathway_maps_species,
                "chebi": chebi
            })
    return pathway_maps

def create_html(output_data, output_directory):
    with open(f"{output_directory}/Reactome_Pathways_Maps.html", 'w', encoding='utf-8') as f:
        f.write('<label><input type="checkbox" id="filterHumanCheckbox" onclick="filterHuman()"> Only human</label>\n')
        f.write('<script>\n')
        f.write('function filterHuman() {\n')
        f.write('  var checkbox = document.getElementById("filterHumanCheckbox");\n')
        f.write('  var lists = document.querySelectorAll("ul");\n')
        f.write('  lists.forEach(function(list) {\n')
        f.write('    var items = list.querySelectorAll("li");\n')
        f.write('    items.forEach(function(item) {\n')
        f.write('      if (checkbox.checked) {\n')
        f.write('        if (!item.textContent.includes("Homo sapiens")) {\n')
        f.write('          item.style.display = "none";\n')
        f.write('        }\n')
        f.write('      } else {\n')
        f.write('        item.style.display = "";\n')
        f.write('      }\n')
        f.write('    });\n')
        f.write('  });\n')
        f.write('}\n')
        f.write('</script>\n')
        
        for accession, reactome in output_data.items():
            sanitized_name = ''.join(c for c in accession if c.isascii())
            f.write(f"<h1>{sanitized_name}</h1>\n")
            if reactome["pathways_maps"]:
                f.write(f"<h2>CHEBI compounds found :</h2>\n<ul>")
                for chebi_id, chebi_name in reactome["chebi"].items():
                    filtered_reactome_maps = [map for map in reactome["pathways_maps"] if map["chebi"] == chebi_id]
                    total_results = len(filtered_reactome_maps)
                    total_human_results = len([map for map in filtered_reactome_maps if map["species"] == "Homo sapiens"])
                    f.write(f"<li>{chebi_name} (ID={chebi_id}) <i>{total_results} maps ({total_human_results} human)</i></li>")
                f.write("</ul>")
                
                for chebi_id, chebi_name in reactome["chebi"].items():
                    filtered_reactome_maps = [map for map in reactome["pathways_maps"] if map["chebi"] == chebi_id]
                    f.write(f"<h3>{chebi_name}</h3>\n")
                    f.write("<ul>\n")
                    for map in filtered_reactome_maps:
                        if map['chebi'] == chebi_id:
                            if map["species"] == "Homo sapiens":
                                f.write(f'<li><a style="color:darkblue;" href="{map["url"]}">{map["name"]} ({map["species"]})</a>')
                            else:
                                f.write(f'<li><a href="{map["url"]}">{map["name"]} ({map["species"]})</a>')
                            f.write('</li>\n')
                    f.write("</ul>\n")
            else:
                f.write(f"<label>Nothing found</label>\n")

def create_excel(output_data, output_directory):
    excel_data = {
        "Query": [],
        "Found": [],
        "CHEBI IDs": [],
        "CHEBI names": [],
        "Pathway names": [],
        "Pathway counts": []
    }
    for accession, reactome in output_data.items():
        sanitized_name = ''.join(c for c in accession if c.isascii())
        excel_data["Query"].append(sanitized_name)
        if reactome["pathways_maps"]:
            excel_data["Found"].append("True")
            excel_data["CHEBI IDs"].append(';'.join(list(reactome["chebi"].keys())))
            excel_data["CHEBI names"].append(';'.join(list(reactome["chebi"].values())))
            pathway_names = {}
            for map in reactome["pathways_maps"]:
                if map['name'] in pathway_names:
                    pathway_names[map['name']] += 1
                else:
                    pathway_names[map['name']] = 1
            pathway_names_str = ';'.join([f"{map} ({map_count})"for map, map_count in pathway_names.items()])
            excel_data["Pathway names"].append(pathway_names_str)
            excel_data["Pathway counts"].append(sum(pathway_names.values()))
        else:
            excel_data["Found"].append("False")
            excel_data["CHEBI IDs"].append("")
            excel_data["CHEBI names"].append("")
            excel_data["Pathway names"].append("")
            excel_data["Pathway counts"].append(0)
    
    brexcel.write_excel(excel_data, f"{output_directory}/Reactome_Pathways_Table.xlsx")