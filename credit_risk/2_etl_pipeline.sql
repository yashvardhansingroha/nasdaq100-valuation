-- Lending Club credit-risk ETL: clean analytical views
-- Run against mn_analytics_db after 1_data_ingestion.py

CREATE OR REPLACE VIEW vw_clean_loan_data AS
SELECT
    id,
    loan_amnt,
    int_rate,
    installment,
    grade,
    home_ownership,
    verification_status,
    annual_inc,
    dti,
    purpose,
    revol_util,
    revol_bal,
    total_acc,
    open_acc,
    pub_rec,
    delinq_2yrs,
    mort_acc,
    issue_d,

    -- Target Variable (0 = Safe, 1 = Default)
    CASE
        WHEN loan_status = 'Fully Paid' THEN 0
        WHEN loan_status IN ('Charged Off', 'Default') THEN 1
        ELSE NULL
    END AS default_flag,

    -- Feature Engineering: Employment Length
    CASE
        WHEN emp_length = '< 1 year' THEN 0
        WHEN emp_length = '10+ years' THEN 10
        ELSE CAST(SUBSTRING(emp_length FROM '[0-9]+') AS NUMERIC)
    END AS emp_length_years,

    -- Feature Engineering: Term Months
    CAST(SUBSTRING(term FROM '[0-9]+') AS INT) AS term_months,

    -- Vintage year for cohort analysis (issue_d is typically Mon-YYYY)
    CASE
        WHEN issue_d ~ '^[A-Za-z]{3}-[0-9]{4}$'
            THEN CAST(RIGHT(issue_d, 4) AS INT)
        WHEN issue_d ~ '^[0-9]{4}'
            THEN CAST(LEFT(issue_d, 4) AS INT)
        ELSE NULL
    END AS vintage_year
FROM
    loan_data_raw
WHERE
    loan_status IN ('Fully Paid', 'Charged Off', 'Default')
    AND annual_inc IS NOT NULL
    AND dti IS NOT NULL;


-- Portfolio segmentation by Lending Club grade
CREATE OR REPLACE VIEW vw_grade_segments AS
SELECT
    grade,
    COUNT(*) AS loan_count,
    SUM(loan_amnt) AS total_exposure,
    AVG(default_flag::NUMERIC) AS observed_default_rate,
    AVG(dti) AS avg_dti,
    AVG(int_rate) AS avg_int_rate,
    AVG(annual_inc) AS avg_annual_inc
FROM
    vw_clean_loan_data
WHERE
    default_flag IS NOT NULL
GROUP BY
    grade
ORDER BY
    grade;


-- Vintage × grade default cohorts
CREATE OR REPLACE VIEW vw_vintage_cohorts AS
SELECT
    vintage_year,
    grade,
    COUNT(*) AS loan_count,
    SUM(loan_amnt) AS total_exposure,
    AVG(default_flag::NUMERIC) AS observed_default_rate,
    AVG(dti) AS avg_dti,
    AVG(int_rate) AS avg_int_rate
FROM
    vw_clean_loan_data
WHERE
    default_flag IS NOT NULL
    AND vintage_year IS NOT NULL
GROUP BY
    vintage_year,
    grade
ORDER BY
    vintage_year,
    grade;
