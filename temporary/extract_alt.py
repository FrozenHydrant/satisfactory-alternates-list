import xml.etree.ElementTree as ET
import sys
import json
# https://stackoverflow.com/questions/5501118/python-elementtree-cannot-use-absolute-path-on-element

def clean_name(name):
    name = name.lower().replace(" ", "_")
    return name

def clean_amount(amount):
    s = ""
    for c in amount:
        try:
            if c != '.':
                c = int(c)
            s += str(c)       
        except:
            pass
    return float(s)

def main():
    buildings = {"Assembler": 15, "Constructor": 4, "Smelter": 4, "Foundry": 16, "Manufacturer": 55, "Refinery": 30, "Blender": 75, "Particle Accelerator": 1000, "Quantum Encoder": 1000}
    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    all_items = []
    
    for child in root:
        all_ingredients = {}
        print(child.tag, child.attrib)
        
        # Ingredients
        top = child[1][0]
        inputs = {}
        if len(top) > 0:
              for item in top:
                  item_name = item.find("*[@class='item-name']").text
                  item_amount = item.find("*[@class='item-amount']").text
                  inputs[clean_name(item_name)] = clean_amount(item_amount)
        else:
            continue

        # Building
        top = child[2][0]
        if top[0].text in buildings:
            energy = buildings[top[0].text]
        else:
            continue

        top = child[3][0]
        item = top[0]
        item_name = clean_name(item.find("*[@class='item-name']").text)
        item_amount = clean_amount(item.find("*[@class='item-amount']").text)
        item_minute = clean_amount(item.find("*[@class='item-minute']").text)
        time = (item_amount / item_minute) * 60
        print(item_minute)

        all_ingredients = {"input": inputs, "output": item_amount, "energy": energy, "time": time, "output_name": item_name}

        # Name
        print(child[0].text)
        all_ingredients["name"] = child[0].text

        all_items.append(all_ingredients)

    with open(sys.argv[2], "w") as output:
        output.write(json.dumps(all_items))

if __name__ == '__main__':
    main()
