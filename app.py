import streamlit as st
import json

# ------------------------
# Load API keys
# ------------------------
with open("keys.json") as f:
    API_KEYS = json.load(f)  # Example: ["a1b2c3d4e5f6g7h8"]

# ------------------------
# Load crops dataset
# ------------------------
with open("crops_2000_weather.json") as f:
    CROPS = json.load(f)

st.set_page_config(page_title="Crop API", layout="wide")

# ------------------------
# Robust query param extraction
# ------------------------
def get_query_param(name):
    raw = st.query_params.get(name)
    if isinstance(raw, list):
        return raw[0].strip()
    elif isinstance(raw, str):
        return raw.strip()
    else:
        return None

api_key = get_query_param("apikey")
category = get_query_param("category")
temp_range = get_query_param("temperature")

# ------------------------
# Debug prints (optional)
# ------------------------
st.write("Loaded API keys:", API_KEYS)
st.write("Detected API key:", api_key)
st.write("Category filter:", category)
st.write("Temperature filter:", temp_range)

# ------------------------
# Authentication
# ------------------------
if api_key is None:
    st.json({"error": "Missing API key. Use ?apikey=your_key"})
elif api_key not in API_KEYS:
    st.json({"error": "Invalid API key"})
else:
    data = CROPS.copy()  # Start with full dataset

    # ------------------------
    # Filter by category
    # ------------------------
    if category and category in data:
        data = {category: data[category]}

    # ------------------------
    # Filter by temperature range (overlap)
    # ------------------------
    if temp_range:
        try:
            tmin, tmax = map(int, temp_range.split("-"))
            for cat in data:
                filtered = []
                for crop in data[cat]:
                    trange = crop.get("temperature_range", "")
                    if "-" in trange:
                        cmin, cmax = map(int, trange.split("-"))
                        # Include crops whose range overlaps requested range
                        if cmax >= tmin and cmin <= tmax:
                            filtered.append(crop)
                data[cat] = filtered
        except Exception:
            st.json({"error": "Invalid temperature format. Use min-max. Example: 20-25"})
            st.stop()

    st.json(data)
