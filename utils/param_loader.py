import json
 
def load_param_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f) 