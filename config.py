class Config:
    DATABRICKS_HOST = "adb-94787086326342.2.azuredatabricks.net"
    DATABRICKS_TOKEN = "dapi1a22cc52fad21a8558c08631fe9ae11a-3"
    DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/d914971383124532"

    
    WOUND_TABLE = "wcr_wound_detection.wcr_wound.wcr_annotation_initial"
    

    CATEGORY_COLORS = {
        "INSECT BITE": "#FF0000",            # Red
        "DOG BITE": "#FF4500",               # Orange Red
        "CAT BITE": "#FF6347",               # Tomato
        "HUMAN BITE": "#FF7F50",             # Coral
        "BITE (OTHER)": "#FF8C00",           # Dark Orange
        "SURGICAL": "#800080",               # Purple
        "AUTOIMMUNE": "#9370DB",             # Medium Purple
        "TRAUMA": "#FF1493",                 # Deep Pink
        "INFECTIOUS ABCESS": "#8B0000",      # Dark Red
        "CYST LESION": "#DA70D6",            # Orchid
        "VASCULITUS": "#0000FF",             # Blue
        "MALIGNANT": "#000080",              # Navy
        "MASD": "#4169E1",                   # Royal Blue
        "CHRONIC SKIN ULCER": "#1E90FF",     # Dodger Blue
        "PRESSURE / DEVICE RELATED PRESSURE": "#00BFFF",  # Deep Sky Blue
        "DIABETIC SKIN ULCER (FOOT)": "#00FF00",         # Green
        "DIABETIC SKIN ULCER (NON-FOOT)": "#32CD32",     # Lime Green
        "BURN": "#FFA500",                   # Orange
        "STOMA": "#8B4513",                  # Saddle Brown
        "FISTULA/SINUS TRACT": "#A0522D",    # Sienna
        "DERMATOLOLICAL": "#6B8E23",         # Olive Drab
        "CALCIPHYLAXIS": "#556B2F",          # Dark Olive Green
        "NOT A WOUND": "#808080",            # Gray
        "RADIATION WOUND": "#4B0082",        # Indigo
        "EDEMA RELATED": "#483D8B"           # Dark Slate Blue
    }
    ETIOLOGY_OPTIONS = [
     "INSECT BITE",
        "DOG BITE",
        "CAT BITE",
        "HUMAN BITE",
        "BITE (OTHER)",
        "SURGICAL",
        "AUTOIMMUNE",
        "TRAUMA",
        "INFECTIOUS ABCESS",
        "CYST LESION",
        "VASCULITUS",
        "MALIGNANT",
        "MASD",
        "CHRONIC SKIN ULCER",
        "PRESSURE / DEVICE RELATED PRESSURE",
        "DIABETIC SKIN ULCER (FOOT)",
        "DIABETIC SKIN ULCER (NON-FOOT)",
        "BURN",
        "STOMA",
        "FISTULA/SINUS TRACT",
        "DERMATOLOLICAL",
        "CALCIPHYLAXIS",
        "NOT A WOUND",
        "RADIATION WOUND",
        "EDEMA RELATED"
        # Add more from spreadsheet
    ]
    
    BODY_LOCATIONS = [
        "HEAD",
        "NECK",
        "LOWER EXTREMITY",
        "TORSO ABDOMEN",
        "TORSO BACK",
        "BUTTOCKS SACRUM",
        "PERINEUM"
    ]
