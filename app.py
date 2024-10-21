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
    
def dict_sum(w, weights, default):
    b = 0
    for item, amount in w.items():
        if item in weights:
            b += amount / weights[item]
        else:
            b += amount / default
    return b

def string_num_cut_and_pretty(num):
    ans = str(num)
    if "." in ans:
        split_num = ans.split(".")
        split_num[1] = split_num[1][:2]
        ans = ".".join(split_num)
    return ans

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
        change_in_resources_percent = dict_sum(difference_tree, weights, 1000) / dict_sum(default_tree, weights, 1000) * 100
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

        all_recipes.append(info)
        
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
