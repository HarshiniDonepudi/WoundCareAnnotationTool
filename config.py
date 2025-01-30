class Config:
    DATABRICKS_HOST = "adb-94787086326342.2.azuredatabricks.net"
    DATABRICKS_TOKEN = "dapi1a22cc52fad21a8558c08631fe9ae11a-3"
    DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/d914971383124532"

    
    WOUND_ASSESSMENT_TABLE = "wcr_wound_detection.wcr_wound.joined_wound_assessments"
    
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
