import json
import csv

def merge_dicts(default, override):
    """
    Recursively merge two dictionaries.
    Override values replace default values when the key is present.
    If the value associated with a key is itself a dictionary, the merge is done recursively.
    """
    for key, value in override.items():
        # If both values associated with the key are dictionaries, merge recursively
        if isinstance(value, dict) and key in default and isinstance(default[key], dict):
            merge_dicts(default[key], value)
        else:
            # Otherwise, overwrite the value with the one from override
            default[key] = value
    return default


def parse_value(value):
    """Try to recursively parse a value as JSON if possible."""
    if isinstance(value, str):
        value = value.strip()
        if (value.startswith('{') and value.endswith('}')) or (value.startswith('[') and value.endswith(']')):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return {k: parse_value(v) for k, v in parsed.items()}
                elif isinstance(parsed, list):
                    return [parse_value(v) for v in parsed]
                return parsed
            except (json.JSONDecodeError, TypeError):
                pass
    return value

def local_get_messages():

    with open("config/config_template.json", 'r', encoding='utf-8') as json_file:
        template_data = json.load(json_file)  

    with open("config/config_local.json", 'r', encoding='utf-8') as json_file:
        env_data = json.load(json_file)

    def replace_env_values(data, env_dict):
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                new_data[key] = replace_env_values(value, env_dict)
            return new_data

        elif isinstance(data, list):
            new_list = []
            for item in data:
                new_list.append(replace_env_values(item, env_dict))
            return new_list

        elif isinstance(data, str) and data.startswith("$env_"):
            # Extract the key after "$env_"
            env_key = data[5:]  # remove the '$env_' prefix
            return env_dict.get(env_key, data)  # return the found value or the original value if key is absent

        else:
            # Value that is neither dict, nor list, nor str starting with "$env_"
            return data

    final_config = replace_env_values(template_data,env_data)


    default_job_message = final_config["default_job_message"]
    default_agent_message = final_config["default_agent_message"]

    with open("config/data_agent.csv") as file_data_agent:
        reader_data_agent = csv.DictReader(file_data_agent)  # Read CSV as dictionary
        try:
            dict_list_data_agent = [{k: parse_value(v) for k, v in row.items()} for row in reader_data_agent]  # Conversion
        except:
            pass

    with open("config/data_job.csv") as file_data_job:
        reader_data_job = csv.DictReader(file_data_job)  # Read CSV as dictionary
        try:
            dict_list_data_job = [{k: parse_value(v) for k, v in row.items()} for row in reader_data_job]  # Conversion
        except:
            pass
    try:
        final_data_agent = merge_dicts(default_agent_message, dict_list_data_agent[0] )
    except:
        final_data_agent = default_agent_message
    try:
        final_data_job = merge_dicts(default_job_message, dict_list_data_job[0] )
    except:
        final_data_job = default_job_message


    return [final_data_agent,final_data_job]
