import pandas as pd
import os

FISIERE = {
    "iunie 2025":  "../1.surse_date/SES1.xlsx",
    "august 2025": "../1.surse_date/SES2.xlsx",
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


