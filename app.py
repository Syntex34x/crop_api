import streamlit as st
import json

# ------------------------
# Load API keys
# ------------------------
try:
    with open("keys.json") as f:
        API_KEYS = json.load(f)  # Example: ["a1b2c3d4e5f6g7h8"]
except FileNotFoundError:
    st.error("keys.json file not found")
    st.stop()
except json.JSONDecodeError:
    st.error("Invalid JSON format in keys.json")
    st.stop()

# ------------------------
# Load crops dataset
# ------------------------
try:
    with open("crops_2000_weather.json") as f:
        CROPS = json.load(f)
except FileNotFoundError:
    st.error("crops_2000_weather.json file not found")
    st.stop()
except json.JSONDecodeError:
    st.error("Invalid JSON format in crops_2000_weather.json")
    st.stop()

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
# Debug prints (conditional - only show in development)
# ------------------------
debug_mode = get_query_param("debug") == "true"
if debug_mode:
    st.write("Debug Mode Enabled")
    st.write("Total API keys loaded:", len(API_KEYS))
    st.write("API key provided:", bool(api_key))
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
    # Filter by category (case-insensitive)
    # ------------------------
    if category:
        category_lower = category.lower()
        matching_key = next((k for k in data.keys() if k.lower() == category_lower), None)
        if matching_key:
            data = {matching_key: data[matching_key]}
        else:
            st.json({"error": f"Category '{category}' not found. Available categories: {list(data.keys())}"})
            st.stop()
    
    # ------------------------
    # Filter by temperature range (overlap)
    # ------------------------
    if temp_range:
        try:
            # Handle whitespace in temperature range
            temp_range = temp_range.replace(" ", "")
            if "-" not in temp_range:
                raise ValueError("Temperature range must contain '-'")
            
            tmin, tmax = map(int, temp_range.split("-"))
            
            if tmin > tmax:
                raise ValueError("Minimum temperature cannot be greater than maximum")
            
            filtered_data = {}
            total_crops_found = 0
            
            for cat in data:
                filtered = []
                for crop in data[cat]:
                    trange = crop.get("temperature_range", "")
                    if "-" in trange:
                        try:
                            # Handle whitespace in crop temperature range
                            trange = trange.replace(" ", "")
                            cmin, cmax = map(int, trange.split("-"))
                            # Include crops whose range overlaps requested range
                            if cmax >= tmin and cmin <= tmax:
                                filtered.append(crop)
                        except (ValueError, AttributeError):
                            # Skip crops with invalid temperature range format
                            continue
                
                if filtered:  # Only include categories with matching crops
                    filtered_data[cat] = filtered
                    total_crops_found += len(filtered)
            
            data = filtered_data
            
            if total_crops_found == 0:
                st.json({
                    "message": f"No crops found for temperature range {temp_range}°C",
                    "requested_range": f"{tmin}-{tmax}°C"
                })
                st.stop()
                
        except ValueError as e:
            st.json({
                "error": f"Invalid temperature format: {str(e)}. Use format: min-max (example: 20-25)"
            })
            st.stop()
        except Exception as e:
            st.json({
                "error": f"Error processing temperature range: {str(e)}"
            })
            st.stop()
    
    # ------------------------
    # Final response with metadata
    # ------------------------
    total_categories = len(data)
    total_crops = sum(len(crops) for crops in data.values())
    
    response = {
        "data": data,
        "metadata": {
            "total_categories": total_categories,
            "total_crops": total_crops,
            "filters_applied": {
                "category": category if category else None,
                "temperature_range": temp_range if temp_range else None
            }
        }
    }
    
    st.json(response)
