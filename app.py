import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI Talent Finder", page_icon="🎯", layout="wide")

SKILLS = [
    "Java", "Spring Boot", "Microservices", "Angular", "React", "Python",
    "Django", "Flask", "Node.js", ".NET", "C#", "SQL", "AWS", "Azure",
    "GCP", "Docker", "Kubernetes", "Jenkins", "Git", "REST API",
    "Selenium", "Playwright", "Manual Testing", "QA Automation",
    "Data Engineering", "PySpark", "Databricks", "Machine Learning",
    "Deep Learning", "Computer Vision", "NLP", "TensorFlow", "PyTorch",
    "Cybersecurity", "Network Security", "Linux", "DevOps", "ELK",
    "Elasticsearch", "Kafka", "Power BI", "Tableau"
]

def clean_text(value):
    return str(value or "").lower().replace("nodejs", "node.js")

def find_skills(text):
    source = clean_text(text)
    found = []
    for skill in SKILLS:
        pattern = re.escape(skill.lower())
        if re.search(r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])", source):
            found.append(skill)
    return found

def make_boolean(role, skills):
    role = role.strip()
    role_part = f'("{role}")' if role else '("Software Developer")'
    skill_part = " AND ".join([f'"{s}"' for s in skills[:6]])
    if skill_part:
        return f'{role_part} AND ({skill_part})'
    return role_part

st.title("🎯 AI Talent Finder")
st.caption("Smart IT Recruitment & Candidate Sourcing Assistant | Version 1.0")
st.info("This starter version analyses candidate data that you upload or enter with permission. It does not scrape LinkedIn, Naukri, Indeed or Hirist.")

with st.sidebar:
    st.header("Recruiter workspace")
    recruiter = st.text_input("Recruiter name (optional)")
    st.caption("Use authorised candidate information only. Avoid uploading sensitive personal data.")

tab1, tab2, tab3 = st.tabs(["🔎 JD Analyzer & Matching", "🧩 Boolean Search Builder", "📋 Candidate Data Template"])

with tab1:
    st.subheader("1. Enter the job description")
    jd = st.text_area(
        "Paste job description",
        height=190,
        placeholder="Example: Java Full Stack Developer with 5+ years experience in Java, Spring Boot, Microservices, Angular, REST API and AWS."
    )
    c1, c2 = st.columns(2)
    with c1:
        min_exp = st.number_input("Minimum experience (years)", min_value=0.0, max_value=40.0, value=5.0, step=0.5)
    with c2:
        role = st.text_input("Target role", value="Java Full Stack Developer")

    jd_skills = find_skills(jd)
    if jd:
        st.markdown("**Skills detected in JD**")
        if jd_skills:
            st.write(" · ".join(jd_skills))
        else:
            st.warning("No skills from the starter skill dictionary were detected. Add clear technology names to the JD.")

    st.divider()
    st.subheader("2. Upload candidate profiles")
    st.write("Upload a CSV with the columns shown in the Candidate Data Template tab, or use the sample file.")
    uploaded = st.file_uploader("Upload candidate CSV", type=["csv"])
    use_sample = st.checkbox("Use sample candidates for a demo", value=uploaded is None)

    candidates = None
    if uploaded is not None:
        try:
            candidates = pd.read_csv(uploaded).fillna("")
        except Exception as exc:
            st.error(f"Could not read this CSV: {exc}")
    elif use_sample:
        candidates = pd.DataFrame([
            {"name":"Candidate A","experience_years":5.5,"skills":"Java, Spring Boot, Microservices, Angular, REST API, AWS","location":"Hyderabad","linkedin_url":"https://www.linkedin.com/","github_url":"https://github.com/","availability_note":"Recruiter to verify","profile_notes":"Sample profile only"},
            {"name":"Candidate B","experience_years":4.0,"skills":"Java, Spring Boot, SQL, Docker, Jenkins","location":"Hyderabad","linkedin_url":"https://www.linkedin.com/","github_url":"https://github.com/","availability_note":"Recruiter to verify","profile_notes":"Sample profile only"},
            {"name":"Candidate C","experience_years":6.0,"skills":"Python, Django, AWS, Docker, Kubernetes, REST API","location":"Bengaluru","linkedin_url":"https://www.linkedin.com/","github_url":"https://github.com/","availability_note":"Recruiter to verify","profile_notes":"Sample profile only"}
        ])

    if candidates is not None:
        required = {"name", "experience_years", "skills"}
        missing = required - set(candidates.columns)
        if missing:
            st.error("Missing required CSV columns: " + ", ".join(sorted(missing)))
        elif st.button("✨ Match candidates to this JD", type="primary", disabled=not jd.strip()):
            jd_skill_set = set(jd_skills)
            results = []
            for _, row in candidates.iterrows():
                candidate_skills = find_skills(row.get("skills", "") + " " + row.get("profile_notes", ""))
                candidate_set = set(candidate_skills)
                matched = sorted(jd_skill_set & candidate_set)
                missing_skills = sorted(jd_skill_set - candidate_set)
                skill_score = (len(matched) / len(jd_skill_set) * 80) if jd_skill_set else 0
                try:
                    years = float(row.get("experience_years", 0) or 0)
                except (ValueError, TypeError):
                    years = 0
                exp_score = 20 if years >= min_exp else (20 * years / min_exp if min_exp else 20)
                score = round(min(100, skill_score + exp_score), 1)
                results.append({
                    "Candidate": row.get("name", "Unknown"),
                    "Match score (rule-based)": score,
                    "Experience (years)": years,
                    "Matched skills": ", ".join(matched) or "None detected",
                    "Skills to verify": ", ".join(missing_skills) or "No JD skills missing",
                    "Location": row.get("location", ""),
                    "Availability note": row.get("availability_note", "Not provided"),
                    "LinkedIn": row.get("linkedin_url", ""),
                    "GitHub": row.get("github_url", "")
                })
            output = pd.DataFrame(results).sort_values("Match score (rule-based)", ascending=False)
            st.success(f"Evaluated {len(output)} candidate profile(s).")
            st.caption("Scores are transparent rule-based indicators, not AI judgments or hiring decisions. Verify claims directly with candidates.")
            st.dataframe(output, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download shortlist CSV", output.to_csv(index=False).encode("utf-8"), "ai_talent_finder_shortlist.csv", "text/csv")

with tab2:
    st.subheader("Boolean Search String Builder")
    search_role = st.text_input("Job title", value="Java Full Stack Developer", key="bool_role")
    skill_text = st.text_input("Required skills (comma-separated)", value="Java, Spring Boot, Microservices, Angular", key="bool_skills")
    platform = st.selectbox("Search destination", ["LinkedIn / Google X-Ray", "Naukri", "Indeed", "Hirist"])
    parsed = [x.strip() for x in skill_text.split(",") if x.strip()]
    boolean_query = make_boolean(search_role, parsed)
    st.code(boolean_query, language="text")
    st.caption("Adapt syntax to the platform's current search rules and account permissions.")
    st.button("Generate search string", key="generate_boolean")
    st.download_button("Download Boolean string", boolean_query, "boolean_search.txt", "text/plain")

with tab3:
    st.subheader("Candidate CSV format")
    template = pd.DataFrame([
        {"name":"Candidate A","experience_years":5.5,"skills":"Java, Spring Boot, Microservices, Angular","location":"Hyderabad","linkedin_url":"https://www.linkedin.com/in/example","github_url":"https://github.com/example","availability_note":"Candidate-confirmed; verify date","profile_notes":"Relevant project experience summary"}
    ])
    st.dataframe(template, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download blank CSV template", template.iloc[0:0].to_csv(index=False).encode("utf-8"), "candidate_template.csv", "text/csv")
    st.markdown("""
    **How to use**
    1. Keep one candidate per row.
    2. Enter skills as comma-separated technology names.
    3. Add profile URLs only when supplied or lawfully obtained.
    4. Record availability only when the candidate has confirmed it.
    5. Do not add Aadhaar, PAN, bank details, health information or other unnecessary sensitive data.
    """)

st.divider()
st.caption("AI Talent Finder is a recruiter decision-support prototype. It does not determine whether a person is actively job-seeking, validate identity, or make hiring decisions. GitHub activity is not proof of job-seeking status or candidate quality.")
