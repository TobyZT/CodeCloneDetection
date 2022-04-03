import json

settings = {}

def value_index(value, mode="metrics"):
    global settings
    thresholds = settings[mode]["thresholds"]
    precision = settings[mode]["precision"]
    for i in range(0, len(thresholds)):
        threshold = thresholds[i]
        if value >= threshold:
            return precision[i]  # 0.97
    return 0


if __name__ == '__main__':
    f = open("threshold_setting.json", "r")
    data = f.read()
    settings = json.loads(data)
    print(value_index(0.996, "metrics"))
    print(value_index(0.992, "ast"))
