from flask import Flask, render_template
import math
import json
import copy
# Thanks to https://www.freecodecamp.org/news/how-to-build-a-web-application-using-flask-and-deploy-it-to-the-cloud-3551c985e492/
# https://www.geeksforgeeks.org/flask-rendering-templates/
# https://stackoverflow.com/questions/62045829/make-html-text-have-2-colors-without-making-new-line
# https://www.geeksforgeeks.org/how-to-use-css-in-python-flask/
# https://stackoverflow.com/questions/6036082/call-a-python-function-from-jinja2

app = Flask(__name__)

# Calulates the (raw) resources, energy used in a recipe
def calculate_tree(w):
    all_resources = copy.copy(w["input"])
    for item in all_resources:
        all_resources[item] /= w["output"]
    total_energy = w["energy"] * w["time"] / w["output"]
    max_time = 1

    modified = True
    while modified:
        modified = False

        next_stage = {}
        for item, amount in all_resources.items():
            
            if item in default_recipes:
                modified = True
                # Update energy
                total_energy += default_recipes[item]["energy"] * default_recipes[item]["time"] * amount / default_recipes[item]["output"]
                max_time = max(max_time, default_recipes[item]["time"])
                
                # Update items tree
                for next_item in default_recipes[item]["input"]:
                    # Make item entry if not already existing
                    if next_item not in next_stage:
                        next_stage[next_item] = 0

                    # Add the amount of the next item needed in the tree
                    next_stage[next_item] += amount * default_recipes[item]["input"][next_item] / default_recipes[item]["output"]
            else:
                if item not in next_stage:
                    next_stage[item] = 0
                next_stage[item] += amount
                    
        # Update the resources to the next level of the tree
        all_resources = next_stage

    return (all_resources, total_energy / max_time)

def dict_sub(one, two):
    ans = {}
    for item, amount in one.items():
        if item in two:
            ans[item] = amount - two[item]
        else:
            ans[item] = amount

    for item, amount in two.items():
        if item not in one:
            ans[item] = -two[item]
    return ans

def translate_tree(t):
    translated_tree = {}
    for item, amount in t.items():
        translated_tree[lang[item]] = amount
    return translated_tree
    
def dict_sum(w, weights):
    b = 0
    for item, amount in w.items():
        b += amount / weights[item]
    return b

def string_num_cut_and_pretty(num):
    ans = str(num)
    if "." in ans:
        split_num = ans.split(".")
        split_num[1] = split_num[1][:2]
        ans = ".".join(split_num)
    return ans

def sorting_key(item):
    if float(item["old_energy"]) > 0:
        return float(item["materials_p"])*10 + float(item["energy_p"]) - float(item["speed_percentage"])*0.1
    else:
        # If the recipe is designed to produce energy (particularily nuclear power based ones), then the energy cost should be weighted much more heavily.
        return float(item["materials_p"])*10 + float(item["energy_p"])*5 - float(item["speed_percentage"])*0.1


@app.route("/")
def home():
    all_recipes = []
    for alternate in alternate_recipes:
        info = {}

        tree, energy = calculate_tree(alternate)

        # If we don't locate an original recipe, then we have nothing to compare to, so skip it
        if alternate["output_name"] in default_item_trees:
            default_tree = default_item_trees[alternate["output_name"]]
        else:
            continue
        difference_tree = dict_sub(tree, default_tree)
        change_in_resources_percent = dict_sum(difference_tree, weights) / dict_sum(default_tree, weights) * 100
        old_energy = default_item_powers[alternate["output_name"]]
        change_in_energy_percent = ((energy - old_energy) / abs(old_energy)) * 100
        speed = alternate["output"] * (60 / alternate["time"])
        default = default_recipes[alternate["output_name"]]
        old_speed = default["output"] * (60 / default["time"])
        speed_percentage = (-1 + speed / old_speed) * 100

        info["name"] = alternate["name"]
        info["materials_p"] = string_num_cut_and_pretty(change_in_resources_percent)
        info["energy"] = string_num_cut_and_pretty(energy)
        info["speed"] = string_num_cut_and_pretty(speed)
        info["materials"] = translate_tree(difference_tree)
        info["old_energy"] = string_num_cut_and_pretty(old_energy)
        info["energy_p"] = string_num_cut_and_pretty(change_in_energy_percent)
        info["old_speed"] = string_num_cut_and_pretty(old_speed)
        info["speed_percentage"] = string_num_cut_and_pretty(speed_percentage)
        info["output"] = lang[alternate["output_name"]]

        # Some alternate recipes were considered as default recipes, which would mean nothing changes when considered as an alternate (and should not be included)
        if abs(change_in_resources_percent) + abs(change_in_energy_percent) + abs(speed_percentage) < 1e-5:
            continue
            
        all_recipes.append(info)

    # Sort and assign different grades
    all_recipes.sort(key=sorting_key)
    amount_of_recipes = len(all_recipes)
    for i in range(0, amount_of_recipes):
        if i / amount_of_recipes < 0.1:
            all_recipes[i]["grade"] = "SS"
        elif i / amount_of_recipes < 0.2:
            all_recipes[i]["grade"] = "S"
        elif i / amount_of_recipes < 0.35:
            all_recipes[i]["grade"] = "A"
        elif i / amount_of_recipes < 0.55:
            all_recipes[i]["grade"] = "B"
        elif i / amount_of_recipes < 0.8:
            all_recipes[i]["grade"] = "C"
        else:
            all_recipes[i]["grade"] = "D"
    return render_template("home.html", entries=all_recipes, string_cut=string_num_cut_and_pretty)

default_item_trees = {}
default_item_powers = {}

if __name__ == '__main__':

    # Load information
    with open("data/default.json", "r") as opened_file:
        default_recipes = json.loads(opened_file.read())

    with open("data/alternate.json", "r") as opened_file:
        alternate_recipes = json.loads(opened_file.read())

    with open("data/weights.json", "r") as opened_file:
        weights = json.loads(opened_file.read())

    with open("lang/en_US.json", "r") as opened_file:
        lang = json.loads(opened_file.read())

    for item, info in default_recipes.items():
        default_item_trees[item], default_item_powers[item] = calculate_tree(info)
        
    app.run(debug=True)
