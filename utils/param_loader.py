import json
import os
from utils.version_manager import version_manager

def load_param_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_param(strategy_type: str, param_id: str, symbol: str, mode: str = 'in_sample') -> dict:
    """
    Loads a specific parameter set from a JSON log file.

    It constructs the path to the parameter log file based on the strategy,
    symbol, and mode (in_sample or out_sample), using versioned directories.

    Args:
        strategy_type (str): The strategy type (e.g., 'RSI').
        param_id (str): The specific parameter ID to load.
        symbol (str): The stock symbol (e.g., 'AAPL').
        mode (str): The directory to look in, either 'in_sample' or 'out_sample'.
                    Defaults to 'in_sample'.

    Returns:
        dict: The dictionary of parameters for the given param_id.
              Returns an empty dictionary if not found.
    """
    # 使用版本管理器取得當前版本
    current_version = version_manager.get_current_version()
    if not current_version:
        print("WARNING: No current version found. Please run M1-M5 workflow first.")
        return {}
    
    if mode == 'in_sample':
        # M6/M7 always use out_sample params, but this maintains compatibility
        param_dir = version_manager.get_version_path(current_version, "in_sample_params")
    elif mode == 'out_sample':
        # For M6/M7 simulation, we use parameters from the validation phase
        param_dir = version_manager.get_version_path(current_version, "out_sample_params")
    else:
        raise ValueError("Mode must be either 'in_sample' or 'out_sample'")

    param_log_path = os.path.join(param_dir, f'param_log_{strategy_type}_{symbol}.json')

    try:
        with open(param_log_path, 'r', encoding='utf-8') as f:
            all_params = json.load(f)
        
        # The param_log file is a list of dictionaries
        for param_set in all_params:
            if param_set.get('id') == param_id:
                return param_set
        
        print(f"WARNING: param_id '{param_id}' not found in {param_log_path}")
        return {}

    except FileNotFoundError:
        print(f"ERROR: Parameter log file not found at {param_log_path}")
        return {}
    except Exception as e:
        print(f"ERROR: Failed to load param_id '{param_id}'. Reason: {e}")
        return {} 