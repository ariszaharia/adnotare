-- 1. Numar inregistrari per tabela
SELECT 'schools' AS tabela, COUNT(*) AS total FROM schools
UNION ALL SELECT 'specializations', COUNT(*) FROM specializations
UNION ALL SELECT 'exam_subjects', COUNT(*) FROM exam_subjects
UNION ALL SELECT 'candidates', COUNT(*) FROM candidates
UNION ALL SELECT 'exam_results', COUNT(*) FROM exam_results;


-- 2. Distributie pe sesiuni
SELECT exam_session, COUNT(*) AS nr_rezultate
FROM exam_results
GROUP BY exam_session;


-- 3. Verificare integritate FK
SELECT 
  (SELECT COUNT(*) FROM candidates c LEFT JOIN schools s ON c.school_id = s.school_id WHERE c.school_id IS NOT NULL AND s.school_id IS NULL) AS candidates_cu_school_invalid,
  (SELECT COUNT(*) FROM candidates c LEFT JOIN specializations sp ON c.specialization_id = sp.specialization_id WHERE c.specialization_id IS NOT NULL AND sp.specialization_id IS NULL) AS candidates_cu_specialization_invalid,
  (SELECT COUNT(*) FROM exam_results r LEFT JOIN candidates c ON r.candidate_id = c.candidate_id WHERE c.candidate_id IS NULL) AS results_cu_candidate_invalid,
  (SELECT COUNT(*) FROM exam_results r LEFT JOIN exam_subjects s ON r.subject_ea_id = s.subject_id WHERE r.subject_ea_id IS NOT NULL AND s.subject_id IS NULL) AS results_cu_subject_ea_invalid;


-- 4. JOIN complet pe toate 5 tabelele
SELECT c.candidate_id, c.sex, sp.specialization_name, sp.profile, sp.track,
       sc.siiir_code, sc.residency_area, r.exam_session, se.subject_name AS materie_ea,
       r.grade_ea, r.final_average, r.final_status
FROM exam_results r
JOIN candidates c ON r.candidate_id = c.candidate_id
JOIN specializations sp ON c.specialization_id = sp.specialization_id
JOIN schools sc ON c.school_id = sc.school_id
LEFT JOIN exam_subjects se ON r.subject_ea_id = se.subject_id
ORDER BY r.exam_result_id
LIMIT 10;


-- 5. Verificare -1 si -2 convertite in NULL
SELECT COUNT(*) AS note_invalide
FROM exam_results
WHERE grade_ea IN (-1, -2) OR grade_eb IN (-1, -2)
   OR grade_ec IN (-1, -2) OR grade_ed IN (-1, -2);


-- 6. Statistici note
SELECT ROUND(AVG(grade_ea), 2) AS media_la_romana,
       ROUND(AVG(grade_ec), 2) AS media_la_proba_obligatorie,
       ROUND(AVG(grade_ed), 2) AS media_la_alegere,
       ROUND(AVG(final_average), 2) AS media_finala,
       MIN(final_average) AS nota_minima,
       MAX(final_average) AS nota_maxima
FROM exam_results
WHERE final_status = 'Promovat';


-- 7. Distributie status final
SELECT final_status, COUNT(*) AS nr_candidati
FROM exam_results
GROUP BY final_status
ORDER BY nr_candidati DESC;


-- 8. Distributie urban vs rural
SELECT sc.residency_area, COUNT(*) AS nr_candidati
FROM candidates c
JOIN schools sc ON c.school_id = sc.school_id
GROUP BY sc.residency_area;


-- 9. Candidati restantieri (in ambele sesiuni)
SELECT COUNT(*) AS candidati_in_ambele_sesiuni
FROM (SELECT candidate_id FROM exam_results
      GROUP BY candidate_id
      HAVING COUNT(DISTINCT exam_session) = 2);


-- 10. Distributie status_ea (verificare coloana status preluata din Excel)
SELECT status_ea, COUNT(*) AS nr
FROM exam_results
GROUP BY status_ea
ORDER BY nr DESC;