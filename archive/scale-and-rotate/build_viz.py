"""Inject real run data into the visual explainer."""
import json

data = json.dumps(json.load(open("viz2d-data.json")), separators=(",", ":"))
html = open("viz/_template.html").read().replace("__DATA__", data)
open("viz/amplification.html", "w").write(html)
print(f"wrote viz/amplification.html ({len(html)//1024} KB)")
