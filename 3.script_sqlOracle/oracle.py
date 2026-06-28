import sys
import os
import math
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "../2.curatare_date"))


SCHEMA_SQL = """
CREATE TABLE schools (
    school_id      NUMBER PRIMARY KEY,
    siiir_code     VARCHAR2(50) NOT NULL UNIQUE,
    sirues_code    VARCHAR2(50),
    residency_area VARCHAR2(100)
);

CREATE TABLE specializations (
    specialization_id   NUMBER PRIMARY KEY,
    specialization_name VARCHAR2(500),
    profile             VARCHAR2(100),
    track               VARCHAR2(100)
);

CREATE TABLE exam_subjects (
    subject_id   NUMBER PRIMARY KEY,
    exam_code    VARCHAR2(10)  NOT NULL,
    subject_name VARCHAR2(500) NOT NULL
);

CREATE TABLE candidates (
    candidate_id      NUMBER PRIMARY KEY,
    sex               VARCHAR2(10),
    education_form    VARCHAR2(100),
    class             VARCHAR2(200),
    promotion_year    VARCHAR2(20),
    modern_language   VARCHAR2(200),
    school_id         NUMBER,
    specialization_id NUMBER,
    CONSTRAINT fk_cand_school FOREIGN KEY (school_id)        REFERENCES schools(school_id),
    CONSTRAINT fk_cand_spec   FOREIGN KEY (specialization_id) REFERENCES specializations(specialization_id)
);

CREATE TABLE exam_results (
    exam_result_id   NUMBER PRIMARY KEY,
    candidate_id     NUMBER NOT NULL,
    subject_ea_id    NUMBER,
    subject_eb_id    NUMBER,
    subject_ec_id    NUMBER,
    subject_ed_id    NUMBER,
    exam_session     VARCHAR2(50),
    grade_ea         NUMBER,
    grade_eb         NUMBER,
    grade_ec         NUMBER,
    grade_ed         NUMBER,
    status_ea        VARCHAR2(100),
    status_eb        VARCHAR2(100),
    status_ec        VARCHAR2(100),
    status_ed        VARCHAR2(100),
    contest_ea       VARCHAR2(10),
    contest_grade_ea NUMBER,
    contest_eb       VARCHAR2(10),
    contest_grade_eb NUMBER,
    contest_ec       VARCHAR2(10),
    contest_grade_ec NUMBER,
    contest_ed       VARCHAR2(10),
    contest_grade_ed NUMBER,
    digital_score    NUMBER,
    final_average    NUMBER,
    final_status     VARCHAR2(100),
    CONSTRAINT fk_res_candidate  FOREIGN KEY (candidate_id)  REFERENCES candidates(candidate_id),
    CONSTRAINT fk_res_subject_ea FOREIGN KEY (subject_ea_id) REFERENCES exam_subjects(subject_id),
    CONSTRAINT fk_res_subject_eb FOREIGN KEY (subject_eb_id) REFERENCES exam_subjects(subject_id),
    CONSTRAINT fk_res_subject_ec FOREIGN KEY (subject_ec_id) REFERENCES exam_subjects(subject_id),
    CONSTRAINT fk_res_subject_ed FOREIGN KEY (subject_ed_id) REFERENCES exam_subjects(subject_id)
);
"""


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
        return str(int(val)) if val.is_integer() else repr(val)
    s = str(val)
    for ch in ["'", '"', '\u201c', '\u201d', '\u201e', '\u2018', '\u2019']:
        s = s.replace(ch, "''")
    return f"'{s}'"


def genereaza_inserts(df, table_name, batch_size=500):
    if df is None or len(df) == 0:
        return ""
    cols = list(df.columns)
    cols_sql = ", ".join(cols)
    parts = []
    rows = df.to_dict(orient="records")
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        values_lines = ["  (" + ", ".join(val_to_sql(r[c]) for c in cols) + ")" for r in batch]
        parts.append(f"INSERT INTO {table_name} ({cols_sql}) VALUES\n" + ",\n".join(values_lines) + ";\n")
    return "\n".join(parts) + "\n"


def exporta_tot(schools, specializations, exam_subjects, candidates, exam_results,
                sql_path="../3.script_sqlOracle/bac_rezultate_2025_oracle.sql"):
    folder = os.path.dirname(sql_path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    parts = [SCHEMA_SQL]
    parts.append(genereaza_inserts(schools,         "schools"))
    parts.append(genereaza_inserts(specializations, "specializations"))
    parts.append(genereaza_inserts(exam_subjects,   "exam_subjects"))
    parts.append(genereaza_inserts(candidates,      "candidates"))
    parts.append(genereaza_inserts(exam_results,    "exam_results"))
    parts.append("COMMIT;\n")

    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    print(f"SQL generat: {sql_path} ({os.path.getsize(sql_path):,} bytes)")


if __name__ == "__main__":
    from curatare_date import schools, specializations, exam_subjects, candidates, results
    exporta_tot(schools, specializations, exam_subjects, candidates, results)