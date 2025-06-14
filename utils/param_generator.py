import itertools
import hashlib

def generate_param_combinations(strategy_type, param_ranges):
    param_list = []
    param_map = {}
    keys = list(param_ranges.keys())
    values = [param_ranges[k] for k in keys]
    for combo in itertools.product(*values):
        param = dict(zip(keys, combo))
        param_id = f"{strategy_type}_" + hashlib.md5(str(param).encode()).hexdigest()[:8]
        param['param_id'] = param_id
        param_list.append(param)
        param_map[param_id] = param
    return param_list, param_map 