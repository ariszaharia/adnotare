import pandas as pd
import os

FISIERE = {
    "iunie_2025":     "../1.surse_date/SES1.xlsx",
    "sesiunea2_2025": "../1.surse_date/SES2.xlsx",
}

frames = []

for sesiune, path in FISIERE.items():
    df_ses = pd.read_excel(path, dtype={
        "Cod unic candidat": int,
        "Unitate (SIIIR)": str,
        "Unitate (SIRUES)": str,
        "Promoție": str,        
    })
    df_ses["exam_session"] = sesiune
    frames.append(df_ses)
    print(f"{sesiune}: {len(df_ses)} randuri")

df = pd.concat(frames, ignore_index=True)

for col in df.select_dtypes(include=["object", "str"]).columns:
    df[col] = df[col].str.strip()
df = df.replace({"": None})

for col in ["NOTA_EA", "NOTA_EB", "NOTA_EC", "NOTA_ED"]:
    count = df[col].isin([-1, -2]).sum()
    df[col] = df[col].where(~df[col].isin([-1, -2]), other=None)
    print(f"  {col}: {count} valori convertite in NULL")


# SCHOOLS
schools = (
    df[["Unitate (SIIIR)", "Unitate (SIRUES)", "Mediu candidat"]]
    .drop_duplicates(subset=["Unitate (SIIIR)"])
    .reset_index(drop=True)
    .rename(columns={
        "Unitate (SIIIR)": "siiir_code",
        "Unitate (SIRUES)": "sirues_code",
        "Mediu candidat": "residency_area",
    })
)
schools.insert(0, "school_id", range(1, len(schools) + 1))
school_map = schools.set_index("siiir_code")["school_id"].to_dict()
print(f"schools: {len(schools)} inregistrari")


# SPECIALIZATIONS
specializations = (
    df[["Specializare", "Profil", "Fileira"]]
    .drop_duplicates()
    .reset_index(drop=True)
    .rename(columns={
        "Specializare": "specialization_name",
        "Profil": "profile",
        "Fileira": "track",
    })
)
specializations.insert(0, "specialization_id", range(1, len(specializations) + 1))
spec_map = specializations.set_index(
    ["specialization_name", "profile", "track"]
)["specialization_id"].to_dict()
print(f"specializations: {len(specializations)} inregistrari")


# EXAM_SUBJECTS
subjects_rows = []
for col, code in [("Subiect ea", "ea"), ("Subiect eb", "eb"),
                  ("Subiect ec", "ec"), ("Subiect ed", "ed")]:
    for val in df[col].dropna().unique():
        val = str(val).strip()
        if val:
            subjects_rows.append({"exam_code": code, "subject_name": val})

exam_subjects = (
    pd.DataFrame(subjects_rows)
    .drop_duplicates(subset=["exam_code", "subject_name"])
    .reset_index(drop=True)
)
exam_subjects.insert(0, "subject_id", range(1, len(exam_subjects) + 1))
subj_map = exam_subjects.set_index(["exam_code", "subject_name"])["subject_id"].to_dict()
print(f"exam_subjects: {len(exam_subjects)} inregistrari")


# CANDIDATES
candidates = df[[
    "Cod unic candidat", "Sex", "Forma de învățământ", "Clasa",
    "Promoție", "Limba modernă", "Unitate (SIIIR)", "Specializare", "Profil", "Fileira"
]].copy()

candidates["school_id"] = candidates["Unitate (SIIIR)"].map(school_map)
candidates["specialization_id"] = candidates.apply(
    lambda r: spec_map.get((r["Specializare"], r["Profil"], r["Fileira"])),
    axis=1
)

candidates = (
    candidates
    .rename(columns={
        "Cod unic candidat": "candidate_id",
        "Sex": "sex",
        "Forma de învățământ": "education_form",
        "Clasa": "class",
        "Promoție": "promotion_year",
        "Limba modernă": "modern_language",
    })
    [["candidate_id", "sex", "education_form", "class", "promotion_year",
      "modern_language", "school_id", "specialization_id"]]
    .drop_duplicates(subset=["candidate_id"], keep="first")
    .reset_index(drop=True)
)
print(f"candidates: {len(candidates)} inregistrari")


# EXAM_RESULTS
results = df.copy()

probe = {
    "Subiect ea": "ea",
    "Subiect eb": "eb",
    "Subiect ec": "ec",
    "Subiect ed": "ed",
}

for coloana_excel, cod_proba in probe.items():
    def get_subject_id(valoare, cod=cod_proba):
        if pd.isna(valoare):
            return None
        return subj_map.get((cod, str(valoare).strip()))

    results[f"subject_{cod_proba}_id"] = results[coloana_excel].apply(get_subject_id)

results = (
    results
    .rename(columns={
        "Cod unic candidat": "candidate_id",
        "NOTA_EA": "grade_ea",           "NOTA_EB": "grade_eb",
        "NOTA_EC": "grade_ec",           "NOTA_ED": "grade_ed",
        "STATUS_EA": "status_ea",        "STATUS_EB": "status_eb",
        "STATUS_EC": "status_ec",        "STATUS_ED": "status_ed",
        "CONTESTATIE_EA": "contest_ea",  "NOTA_CONTESTATIE_EA": "contest_grade_ea",
        "CONTESTATIE_EB": "contest_eb",  "NOTA_CONTESTATIE_EB": "contest_grade_eb",
        "CONTESTATIE_EC": "contest_ec",  "NOTA_CONTESTATIE_EC": "contest_grade_ec",
        "CONTESTATIE_ED": "contest_ed",  "NOTA_CONTESTATIE_ED": "contest_grade_ed",
        "PUNCTAJ DIGITALE": "digital_score",
        "Medie": "final_average",
        "STATUS": "final_status",
    })
    [["candidate_id",
      "subject_ea_id", "subject_eb_id", "subject_ec_id", "subject_ed_id",
      "exam_session",
      "grade_ea", "grade_eb", "grade_ec", "grade_ed",
      "status_ea", "status_eb", "status_ec", "status_ed",
      "contest_ea", "contest_grade_ea",
      "contest_eb", "contest_grade_eb",
      "contest_ec", "contest_grade_ec",
      "contest_ed", "contest_grade_ed",
      "digital_score", "final_average", "final_status"]]
)
results.insert(0, "exam_result_id", range(1, len(results) + 1))
print(f"exam_results: {len(results)} inregistrari")
restantieri = results.groupby("candidate_id")["exam_session"].count()
print(f"  candidati in ambele sesiuni: {len(restantieri[restantieri > 1])}")

import sqlite3
import math


def val_to_sql(val):
    if val is None:
        return "NULL"
    if isinstance(val, float) and math.isnan(val):
        return "NULL"
    try:
        if pd.isna(val):
            return "NULL"
    except (TypeError, ValueError):
        pass
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return repr(val)
    s = str(val)
    s = s.replace('“', '"').replace('”', '"').replace('„', '"')
    s = s.replace('‘', "'").replace('’', "'")
    s = s.replace("'", "''")
    return f"'{s}'"


SCHEMA_SQL = """PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS schools (
    school_id      INTEGER PRIMARY KEY,
    siiir_code     TEXT NOT NULL UNIQUE,
    sirues_code    TEXT,
    residency_area TEXT
);

CREATE TABLE IF NOT EXISTS specializations (
    specialization_id   INTEGER PRIMARY KEY,
    specialization_name TEXT,
    profile             TEXT,
    track               TEXT
);

CREATE TABLE IF NOT EXISTS exam_subjects (
    subject_id   INTEGER PRIMARY KEY,
    exam_code    TEXT NOT NULL,
    subject_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id      INTEGER PRIMARY KEY,
    sex               TEXT,
    education_form    TEXT,
    class             TEXT,
    promotion_year    TEXT,
    modern_language   TEXT,
    school_id         INTEGER,
    specialization_id INTEGER,
    FOREIGN KEY (school_id)         REFERENCES schools(school_id),
    FOREIGN KEY (specialization_id) REFERENCES specializations(specialization_id)
);

CREATE TABLE IF NOT EXISTS exam_results (
    exam_result_id   INTEGER PRIMARY KEY,
    candidate_id     INTEGER NOT NULL,
    subject_ea_id    INTEGER,
    subject_eb_id    INTEGER,
    subject_ec_id    INTEGER,
    subject_ed_id    INTEGER,
    exam_session     TEXT,
    grade_ea         REAL,
    grade_eb         REAL,
    grade_ec         REAL,
    grade_ed         REAL,
    status_ea        TEXT,
    status_eb        TEXT,
    status_ec        TEXT,
    status_ed        TEXT,
    contest_ea       TEXT,
    contest_grade_ea REAL,
    contest_eb       TEXT,
    contest_grade_eb REAL,
    contest_ec       TEXT,
    contest_grade_ec REAL,
    contest_ed       TEXT,
    contest_grade_ed REAL,
    digital_score    INTEGER,
    final_average    REAL,
    final_status     TEXT,
    FOREIGN KEY (candidate_id)  REFERENCES candidates(candidate_id),
    FOREIGN KEY (subject_ea_id) REFERENCES exam_subjects(subject_id),
    FOREIGN KEY (subject_eb_id) REFERENCES exam_subjects(subject_id),
    FOREIGN KEY (subject_ec_id) REFERENCES exam_subjects(subject_id),
    FOREIGN KEY (subject_ed_id) REFERENCES exam_subjects(subject_id)
);

"""


def genereaza_inserts(df, table_name, batch_size=500):
    if df is None or len(df) == 0:
        return ""

    cols = list(df.columns)
    cols_sql = ", ".join(cols)
    parts = []
    rows = df.to_dict(orient="records")

    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        values_lines = []
        for r in batch:
            vals = [val_to_sql(r[c]) for c in cols]
            values_lines.append("  (" + ", ".join(vals) + ")")
        parts.append(
            f"INSERT INTO {table_name} ({cols_sql}) VALUES\n"
            + ",\n".join(values_lines)
            + ";\n"
        )

    return "\n".join(parts) + "\n"


def scrie_sql(schools, specializations, exam_subjects, candidates, exam_results, output_path):
    folder = os.path.dirname(output_path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    parts = [SCHEMA_SQL]
    parts.append(genereaza_inserts(schools, "schools"))
    parts.append(genereaza_inserts(specializations, "specializations"))
    parts.append(genereaza_inserts(exam_subjects, "exam_subjects"))
    parts.append(genereaza_inserts(candidates, "candidates"))
    parts.append(genereaza_inserts(exam_results, "exam_results"))
    parts.append("COMMIT;\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    print(f"SQL generat: {output_path} ({os.path.getsize(output_path):,} bytes)")


def creeaza_baza_date(sql_path, db_path):
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

    with open(sql_path, "r", encoding="utf-8") as f:
        script = f.read()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()

    print(f"Baza de date creata: {db_path} ({os.path.getsize(db_path):,} bytes)")


scrie_sql(schools, specializations, exam_subjects, candidates, results,
          "../3.script_sqlLite/bac_rezultate_2025.sql")

creeaza_baza_date("../3.script_sqlLite/bac_rezultate_2025.sql",
                  "../5.BD_SQLite/bac_rezultate_2025.db")
