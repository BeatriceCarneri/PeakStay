import pandas as pd

def flatten(shelter):
    """Turn one shelter into a flat dict: id_cai, title and one key per field."""
    row = {"id_cai": shelter["id_cai"], "title": shelter["title"]}
    for f in shelter["fields"]:
        row[f["name"]] = f["value"]
    return row

df = pd.DataFrame([flatten(s) for s in shelters])
print(df.shape)
df.head()