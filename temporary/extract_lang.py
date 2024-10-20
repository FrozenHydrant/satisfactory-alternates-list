import xml.etree.ElementTree as ET
import sys
import json

# Simple and dirty method to get English item names.
def clean_name(name):
    name = name.lower().replace(" ", "_")
    return name

def main():
    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    all_items = {}
    
    for child in root:
        all_ingredients = {}
        print(child.tag, child.attrib)
        
        # Ingredients
        top = child[1][0]
        if len(top) > 0:
              for item in top:
                  item_name = item.find("*[@class='item-name']").text
                  all_items[clean_name(item_name)] = item_name
        else:
            continue

        top = child[3][0]
        if len(top) > 0:
            for item in top:
                  item_name = item.find("*[@class='item-name']").text
                  all_items[clean_name(item_name)] = item_name

    with open(sys.argv[2], "w") as output:
        output.write(json.dumps(all_items))

if __name__ == '__main__':
    main()
