import json

def read_json_file(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def create_url_screenshot_dict_from_json(data):
    url_screenshot_dict = {}
    for entry in data:
        url_screenshot_dict[entry["url"]] = entry["screenshotUrl"]
    return url_screenshot_dict

def read_txt_lines(txt_path: str) -> list[str]:
    with open(txt_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def create_url_screenshot_dict_from_txt(lines: list[str]) -> dict[str, list[str]]:
    url_dict = {}
    for line in lines:
        if " - " not in line:
            continue

        key, value = line.split(" - ", 1)

        if key not in url_dict:
            url_dict[key] = []

        url_dict[key].append(value)

    return url_dict

# Test block
if __name__ == "__main__":
    # Specify your file path here
    file_path = "jsons/image_screenshot_test_big3.json"
    data = read_json_file(file_path)
    url_screenshot_dict = create_url_screenshot_dict_from_json(data)

    # Print the output to verify
    print("URL -> Screenshot URL mapping:")
    print(url_screenshot_dict)