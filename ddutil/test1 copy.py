import re

text = "[ERROR] symbol: class MyOtherClass"
regex = r"symbol:\s+class\s+(\w+)"

match = re.search(regex, text)
if match:
    class_name = match.group(1)
    print("Type: class, Name: " + class_name)
