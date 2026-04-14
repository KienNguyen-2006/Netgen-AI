import os

import numpy as np
import pandas as pd

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file) -> str:
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath


def load_dataset(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath)


def get_dataset_info(df: pd.DataFrame) -> dict:
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "shape": df.shape,
        "sample": df.head(10).to_dict(orient="records"),
    }


def _truncate_value(val, max_len=60):
    s = str(val)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


def get_schema_prompt(df: pd.DataFrame) -> str:
    """Build a compact schema + sample representation for the AI prompt."""
    schema_lines = [f"- {col}: {dtype}" for col, dtype in df.dtypes.items()]
    schema_text = "\n".join(schema_lines)

    sample = df.head(2).copy()
    for col in sample.columns:
        sample[col] = sample[col].apply(lambda v: _truncate_value(v))

    sample_json = sample.to_json(orient="records", indent=2)
    return f"Schema:\n{schema_text}\n\nSample rows:\n{sample_json}"


def append_rows(original_path: str, new_rows: list[dict]) -> str:
    """Append generated rows to the original CSV and save as a new file."""
    original_df = pd.read_csv(original_path)
    new_df = pd.DataFrame(new_rows)

    for col in original_df.columns:
        if col in new_df.columns:
            new_df[col] = new_df[col].astype(original_df[col].dtype, errors="ignore")

    combined_df = pd.concat([original_df, new_df], ignore_index=True)

    base = os.path.splitext(os.path.basename(original_path))[0]
    output_filename = f"{base}_augmented.csv"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    combined_df.to_csv(output_path, index=False)

    return output_path


def paginate_df(df: pd.DataFrame, page: int, per_page: int = 25) -> dict:
    total = len(df)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "records": df.iloc[start:end].to_dict(orient="records"),
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


def compare_datasets(original_df: pd.DataFrame, generated_df: pd.DataFrame,
                     max_columns: int = 5) -> dict:
    """Simplified comparison of original vs generated rows.

    Picks the top numeric columns with the most variation, computes a
    representative value for each, and returns an easy-to-read result.
    """
    if generated_df.empty:
        return {"rows": [], "summary": "No generated rows to compare."}

    orig_numeric = original_df.select_dtypes(include="number")
    gen_numeric = generated_df.select_dtypes(include="number")
    common = list(set(orig_numeric.columns) & set(gen_numeric.columns))

    # Pick columns with actual variation, sorted by std descending
    ranked = sorted(
        [c for c in common if orig_numeric[c].std() > 1e-9],
        key=lambda c: orig_numeric[c].std(),
        reverse=True,
    )
    selected = ranked[:max_columns]

    rows = []
    bad = 0
    for col in selected:
        o_val = orig_numeric[col].mean()
        g_val = gen_numeric[col].mean()

        if o_val is None or g_val is None or not np.isfinite(o_val) or not np.isfinite(g_val):
            continue

        diff = round(abs(g_val - o_val) / (abs(o_val) + 1e-6) * 100, 2)
        if diff > 30:
            bad += 1

        rows.append({
            "column": col,
            "original": round(o_val, 4),
            "generated": round(g_val, 4),
            "diff": diff,
        })

    total = len(rows)
    if total == 0:
        summary = "No comparable columns found."
    elif bad == 0:
        summary = "Generated data looks good — values are close to the original."
    elif bad <= total // 2:
        summary = f"Mostly good — {bad} of {total} columns differ by more than 30%."
    else:
        summary = f"Some values differ significantly — {bad} of {total} columns are off by more than 30%."

    return {"rows": rows, "summary": summary}
