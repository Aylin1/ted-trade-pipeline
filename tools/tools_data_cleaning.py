import pandas as pd
import numpy as np
from functools import reduce
import re
from fuzzywuzzy import fuzz, process


def standardize_publication_date(df, date_col='publication_date'):
    """
    Cleans and converts publication dates to datetime, handling:
    - Timezone info in parentheses (e.g., (UTC+02), (UTC))
    - Two-digit or four-digit years
    - Day-first formats (DD/MM/YY or DD/MM/YYYY)
    Adds a 'publication_year' column.
    """
    df = df.copy()
    
    # 1. Remove any timezone info in parentheses, e.g., (UTC), (UTC+02), (UTC-01)
    df[date_col] = df[date_col].astype(str).str.replace(r"\s*\(UTC(?:[+-]\d{2})?\)", "", regex=True).str.strip()
    
    # 2. Convert to datetime (dayfirst=True for DD/MM/YYYY)
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    
    # 3. Warn if parsing failed
    if df[date_col].isna().any():
        print(f"Warning: {df[date_col].isna().sum()} dates could not be parsed in {date_col}")
    
    # 4. Add publication_year column
    df['publication_year'] = df[date_col].dt.year
    
    return df



def basic_fix_encoding(df):
    replacements = {
        "Ã¼": "ü", "Ã¶": "ö", "Ã¤": "ä",
        "ÃŸ": "ß", "Ã": "ß",
        "Ã": "Ü", "Ã": "Ö", "Ã": "Ä",
        "â€“": "–", "â€”": "—",
        "â€ž": "„", "â€œ": "“", "â€": "”",
        "â€™": "’", "â€˜": "‘",
        "â€¢": "•", "â€¦": "…",
        "Â": ""
    }
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].apply(
            lambda x: (
                str(x) if not isinstance(x, str) else
                reduce(lambda t, kv: t.replace(*kv), replacements.items(), x)
            )
            if pd.notna(x) else x
        )
    return df

def missing_winner_summary(df, winner_col='winner_name', year_col='publication_year'):
    """
    Calculates missing winner names per year and their proportion.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset containing winner names and publication year.
    winner_col : str
        Column name for winner names.
    year_col : str
        Column name for publication year.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns: publication_year, missing_count, total_count, missing_percentage
    """
    # Count missing winner names per year
    missing_winners_by_year = (
        df[df[winner_col].isna() | (df[winner_col].astype(str).str.strip() == '')]
        .groupby(year_col)
        .size()
        .reset_index(name="missing_count")
    )

    # Total rows per year
    total_by_year = df.groupby(year_col).size().reset_index(name="total_count")

    # Merge and calculate percentage
    missing_summary = missing_winners_by_year.merge(total_by_year, on=year_col, how="right")
    missing_summary["missing_count"] = missing_summary["missing_count"].fillna(0).astype(int)
    missing_summary["missing_percentage"] = (
        missing_summary["missing_count"] / missing_summary["total_count"] * 100
    ).round(2)

    return missing_summary.sort_values(year_col)


def fill_missing_from_df(base_df, source_df, key_col="notice_publication_number", columns_to_fill=None):
    """
    Fill missing values in base_df using non-null values from source_df, 
    matched by a key column (e.g. 'notice_publication_number').
    Optionally displays which rows were updated.

    Parameters:
        base_df (pd.DataFrame): The main DataFrame to be enriched.
        source_df (pd.DataFrame): The DataFrame providing additional data.
        key_col (str): Column name used to match rows.
        columns_to_fill (list): List of columns to fill in base_df.
                               If None, fills all shared columns.
        show_changes (bool): Whether to display the rows that were updated.

    Returns:
        df (pd.DataFrame): Updated DataFrame with filled values.
        filled_changes (pd.DataFrame): Rows and columns where values were filled.
    """
    df = base_df.copy()

    if columns_to_fill is None:
        columns_to_fill = list(set(base_df.columns) & set(source_df.columns))
    
    if key_col not in df.columns or key_col not in source_df.columns:
        raise KeyError(f"'{key_col}' must exist in both DataFrames.")

    # Select only relevant columns from source_df
    source_subset = source_df[[key_col] + columns_to_fill].drop_duplicates(subset=[key_col])

    # Merge source data
    df = df.merge(source_subset, on=key_col, how="left", suffixes=("", "_src"))

    filled_records = []

    # Fill missing values only where base_df is null and source_df is not null
    for col in columns_to_fill:
        src_col = f"{col}_src"
        if src_col in df.columns:
            mask = df[col].isna() & df[src_col].notna()
            filled_rows = df.loc[mask, [key_col, col, src_col]].copy()
            filled_rows.rename(columns={src_col: "filled_from"}, inplace=True)
            if not filled_rows.empty:
                filled_rows["column_filled"] = col
                filled_records.append(filled_rows)
            # Fill missing values
            df.loc[mask, col] = df.loc[mask, src_col]
            df.drop(columns=[src_col], inplace=True, errors="ignore")

    # Combine all filled rows into one DataFrame
    filled_changes = pd.concat(filled_records, ignore_index=True) if filled_records else pd.DataFrame(columns=[key_col, "column_filled", "filled_from"])

    return df, filled_changes


def compare_name_lists(df_full, df_subset, column="buyer_name", notice_col="notice_publication_number", threshold=90):
    """
    Compare names in df_full[column] vs df_subset[column] using fuzzy matching.
    Adds notice_publication_number from both df_full and df_subset.

    Parameters:
        df_full (pd.DataFrame): Full DataFrame (e.g., curated_df)
        df_subset (pd.DataFrame): Subset DataFrame (e.g., buyers with non-null buyer_type)
        column (str): Column to compare (default 'buyer_name')
        notice_col (str): Column in both DataFrames representing the unique notice ID
        threshold (int): Minimum similarity score (0–100) to include

    Returns:
        pd.DataFrame: Pairs of similar names with similarity scores and notice_publication_number
                      Columns: ['Subset_Name', 'Subset_Notice',
                                'Full_Name', 'Full_Notice', 'Similarity']
    """
    # Ensure the notice column exists
    if notice_col not in df_full.columns or notice_col not in df_subset.columns:
        raise KeyError(f"Column '{notice_col}' must exist in both DataFrames")

    # Get unique subset names
    names_subset = df_subset[column].dropna().unique()

    matches = []
    full_names_list = df_full[column].dropna().to_list()
    
    for name in names_subset:
        similar = process.extract(name, full_names_list, scorer=fuzz.token_sort_ratio, limit=None)
        for match_name, score in similar:
            if threshold <= score <= 100:
                # Get notice numbers for both names (take first if multiple)
                subset_notice = df_subset.loc[df_subset[column] == name, notice_col].values[0]
                full_notice = df_full.loc[df_full[column] == match_name, notice_col].values[0]
                
                matches.append((name, subset_notice, match_name, full_notice, score))

    result_df = pd.DataFrame(
        matches,
        columns=["Subset_Name", "Subset_Notice", "Full_Name", "Full_Notice", "Similarity"]
    )

    result_df.sort_values(by="Similarity", ascending=False, inplace=True)
    result_df.reset_index(drop=True, inplace=True)

    return result_df


def unify_similar_names(df, column="buyer_name", threshold=90):
    """
    Unify similar names in a DataFrame using fuzzy matching with normalization.
    Handles suffixes like 'GmbH', 'KG', 'Co.', etc., and ensures consistent grouping.

    Parameters:
        df (pd.DataFrame): Input DataFrame
        column (str): Column containing the names to unify
        threshold (int): Minimum similarity (0–100) for grouping

    Returns:
        df (pd.DataFrame): Updated DataFrame
        replacements_df (pd.DataFrame): Mapping of original → canonical names
    """
    df = df.copy()

    # Normalize text for better comparison
    def normalize_text(s):
        if pd.isna(s):
            return ""
        s = str(s).lower().strip()

        # Remove legal suffixes and common company forms
        s = re.sub(r"\b(gmbh|co\.|kg|ag|ug|mbh|inc|ltd|sarl|bv|oy|kgaa|company|vertrieb|technik|handel|betriebsausrüstung)\b", "", s)

        # Remove punctuation and normalize spaces
        s = re.sub(r"[^a-z0-9äöüß\s&.\-]", "", s)
        s = re.sub(r"\s+", " ", s).strip()

        return s

    df["_normalized_name"] = df[column].apply(normalize_text)
    unique_names = df["_normalized_name"].dropna().unique().tolist()

    canonical_map = {}
    processed = set()

    # Fuzzy group similar names 
    for name in unique_names:
        if name in processed or not name:
            continue
        matches = process.extract(name, unique_names, scorer=fuzz.token_sort_ratio, limit=None)
        group = [match for match, score in matches if score >= threshold]
        processed.update(group)

        # Choose canonical: prefer shortest or most "base-like" name
        canonical = sorted(group, key=lambda x: (len(x), x))[0]
        for g in group:
            canonical_map[g] = canonical

    # Replace normalized names with canonical forms 
    df["_canonical_name"] = df["_normalized_name"].map(canonical_map).fillna(df["_normalized_name"])

    # Map back to original-style names: choose representative original for each canonical
    representative_map = {}
    for canonical in df["_canonical_name"].unique():
        subset = df.loc[df["_canonical_name"] == canonical, column]
        # Prefer the shortest original that contains canonical text
        rep = sorted(subset, key=len)[0]
        representative_map[canonical] = rep

    df[column] = df["_canonical_name"].map(representative_map).fillna(df[column])

    # Prepare replacement DataFrame 
    replacements_df = df[[column, "_normalized_name"]].drop_duplicates()
    replacements_df = replacements_df.rename(columns={"_normalized_name": "canonical_name"})
    replacements_df = replacements_df[replacements_df[column] != replacements_df["canonical_name"]]

    print(f"Unified {len(replacements_df)} names (threshold={threshold}).")
    print(f"Unique count before: {len(unique_names)}, after: {df[column].nunique()}")

    df.drop(columns=["_normalized_name", "_canonical_name"], inplace=True, errors="ignore")

    return df, replacements_df
