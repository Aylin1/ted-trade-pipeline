# 🌍 Public Procurement Supply Chain Mapping: Fair, Transparent, and Digital

## Overview

This project investigates the global production origins of textiles (such as hospital linens, occupational uniforms, and protective workwear) purchased by German public authorities.

By combining European public tender registries with international customs shipment data, this analysis bypasses standard transparency limitations to map the hidden, macro-level geographic footprint of institutional supply chains.

## 🎯 Key Objectives

- **Data Quality Control:** Resolve systemic gaps in pre-eForms procurement databases by mining historical award notices.
- **Database Integration:** Merge separate, unstructured datasets (EU TED notices and Trade Atlas customs logs) to track the true origin of public goods.
- **Clear Reporting:** Transform complex geospatial and commercial data into intuitive, scannable visualizations for non-technical stakeholders.

## 🛠️ Tech Stack & Methodologies

- **Language:** Python
- **Data Manipulation:** `pandas`, `numpy` (Standardizing classifications, quantitative weighting)
- **Text Processing & Linkage:** `rapidfuzz`, `re` (Algorithmic fuzzy-matching, Regex for corporate name normalization)
- **Geospatial & Visualization:** `plotly`, `pycountry` (Interactive coordinate mapping, scatter-geo flow charts)

## 📊 Key Highlights & Technical Achievements

1. **Algorithmic Fuzzy-Matching:** Built custom Python scripts (`tools_data_cleaning.py`) to unify messy corporate names, stripping legal suffixes (e.g., "GmbH & Co. KG") and applying token-sort ratios to accurately link public contract winners to global import shipment records.
2. **Quantitative Weighting:** Segmented tender documents by standard EU product codes (CPV) using a custom weighted-lots formulation. This prevented small contracts from skewing the data, revealing accurate market dominance across different garment categories.
3. **Geospatial Clustering:** Extracted latitude and longitude coordinates from the Open Supply Hub (OSH) to group fragmented factory locations into clean, city-level production clusters across South and Southeast Asia.
4. **Time-Series Filtering:** Implemented a 180-day temporal validation filter to ensure customs shipments accurately aligned with the contract publication dates.

## 📁 Repository Structure

ted-trade-pipeline/
├── README.md # Documentation and replication instructions
├── requirements.txt # Python dependencies
├── .gitignore # Ignores local caches, data pools, and outputs
├── config.py # Shared global constants (dates, filepaths, HS codes)
│
├── data/
│ ├── raw_ted/ # raw TED source files
│ │ ├── TED_06-10-2025.csv
│ │ └── TED_Data_2018-2025_colored.xlsx
│ └── tradeatlas_files/ # individual customs Excel downloads
│
├── scripts/
│ ├── **init**.py
│ └── tools_data_cleaning.py # Custom modular helper functions (tdc)
│
├── notebooks/ # Ordered execution pipeline
│ ├── 01_clean_merge_ted_data.ipynb
│ ├── 02_generate_tradeatlas_links.ipynb
│ ├── 03_process_tradeatlas_data.ipynb
│ ├── 04_analysis_countries_of_origin.ipynb
│ └── 05_analysis_textile_types.ipynb
│
└── outputs/ # Automatically created during script runtime
├── ted_only_selected_notices.xlsx
├── winner_counts_only_selected_notices.csv
├── tradeatlas_links_first2words_20firms.csv
├── merged_tradeatlas_clean.xlsx
└── germany_flows.html

## 🖼️ Visual Highlights

_(Replace these placeholder links with actual screenshots of your Plotly graphs!)_

### 1. Global Sourcing Flow Map

![Global Flow Map Placeholder](link_to_your_screenshot_1.png)
_Interactive flow map visualizing the volume of textile trade routes between Germany and manufacturing hubs._

### 2. Exporting Countries by Textile Type

![Textile Type Bar Chart Placeholder](link_to_your_screenshot_2.png)
_Stacked bar chart demonstrating the reliance on specific regions for critical goods like hospital linens and workwear._
