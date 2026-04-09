import json
import os

def truncate_values(data, max_len=40):
    """Recursively traverses a JSON object and truncates long strings."""
    if isinstance(data, dict):
        return {key: truncate_values(value, max_len) for key, value in data.items()}
    elif isinstance(data, list):
        return [truncate_values(item, max_len) for item in data]
    elif isinstance(data, str):
        if len(data) > max_len:
            return data[:max_len] + "... [TRUNCATED]"
        return data
    else:
        return data # ints, bools, None, etc.

if __name__ == "__main__":
    input_file = "sample_email.json"
    output_file = "truncated_email.json"
    
    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}. Are you in the backend/ folder?")
    else:
        with open(input_file, "r") as f:
            raw_data = json.load(f)
            
        clean_data = truncate_values(raw_data)
        
        with open(output_file, "w") as f:
            json.dump(clean_data, f, indent=4)
            
        print(f"✅ Success! Data truncated and saved to {output_file}")