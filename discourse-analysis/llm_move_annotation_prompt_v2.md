# LLM 语步标注提示词（精简版 v2，13 Moves + OTHER）

You are an expert corpus linguist and Swalesian genre analyst specializing in cross-cultural institutional discourse analysis of Chinese and American university foreign language department "About Us" / introductory web texts.

Please learn the following instructions step by step, internalize every boundary criterion and annotated example, and then complete the move annotation task strictly as instructed.

======================================================================
LEARN INSTRUCTION 1: THE 13 RHETORICAL MOVES + OTHER SCHEMA
======================================================================
Annotate using ONLY the following 14 XML tags (`<M01>` to `<M13>`, plus `<OTHER>`).

Core Analytical Principle (Yu, 2023): Identify the move of each complete sentence according to its EXPLICIT, DOMINANT communicative purpose in context—NEVER rely blindly on isolated trigger words or sentence position.

1. <M01> Establishing institutional identity and governance structure (界定机构定位与组织架构)
   - Core Question: Who is this department right now, what college/campus does it belong to, what internal sub-units/centers does it house, and who holds formal leadership/governance roles?
   - Includes: Current institutional nature, campus/college affiliation, list of internal departments/divisions/research centers (names only), leadership roles (Dean/Chair/Executive Committee), administrative governance duties, and formal sign-offs at the end of a Dean/Head's statement (Name + Official Title as one block).
   - Boundary: Current governance/structure = <M01>; faculty headcounts/degree ratios/facilities = <M07>; listing center names only = <M01> (explaining actual research questions = <M06>); historical founding/renaming = <M02>; rankings/honors = <M08>; bare webpage breadcrumbs or isolated department titles without predicate = <OTHER>.

2. <M02> Tracing historical continuity and heritage (追溯历史沿革与学脉传承)
   - Core Question: Where did this institution come from, and how did it evolve historically to the present?
   - Includes: Founding year, predecessor units, historical mergers, relocations, renamings, rebuildings, historical milestones (including historical launch years of degree programs narrated along a chronological timeline), and founding pioneers.
   - Boundary: Chronological past narrative = <M02>; describing currently offered degree programs/courses today = <M04>; obituaries mourning deceased individuals = <M13>; moral condemnation/repudiation of historical racism or land acknowledgements = <M03>.

3. <M03> Articulating core values, disciplinary relevance and social contribution (宣示价值准则、学科内涵与社会贡献)
   - Core Question: What fundamental philosophy, academic values, national/humanistic mission, or public ethical stance does the institution stand for? Why does studying languages/literatures/cultures matter? How does it serve society?
   - Includes: Core institutional motto/philosophy, academic freedom/integrity principles, moral commitment to national service / human civilization / DEI, public ethical statements; general conceptual definitions of linguistics/literature/humanities and arguments linking globalization, societal challenges, or human understanding to the necessity of language/cultural study; public language training/testing for officials or citizens, policy think-tank consultation, K-12 curriculum outreach, cultural dissemination, community service, public-facing humanities periodicals.
   - Boundary: Abstract institutional ethos/values OR discipline-at-large relevance OR extra-campus public service = <M03>; concrete statements about what competencies students acquire or how teaching cultivates talents = <M05>; listing courses on race/gender/social justice = <M04>; future strategic plans with explicit future time markers = <M11>; vague mention of "social service" inside an abstract mission motto = <M03>.

4. <M04> Presenting degree programs and curricular provision (介绍学位项目与课程供给)
   - Core Question: What specific degree programs, majors/minors, certificates, languages, and courses are currently offered to learners?
   - Includes: Current BA/MA/PhD/postdoc programs, majors, minors, combination majors, certificates, languages taught, course tiers, and specific course titles/topics offered.
   - Boundary: Objective inventory of degree/course offerings = <M04>; pedagogical methods and student skill development = <M05>; mandatory credit quotas, GPA thresholds, or administrative procedures = <M13>; external training/testing services for government/public = <M03>; enrolled student name rosters = <OTHER>.

5. <M05> Explaining educational goals and pedagogy (阐明育人目标与教学模式)
   - Core Question: What kind of talents/competencies does the department cultivate in current students, and through what teaching/learning practices?
   - Includes: Target student competencies (critical thinking, intercultural competence, communication skills, interdisciplinary/innovative literacy), classroom pedagogy (small seminars, student-centered inquiry, mentorship), experiential/co-curricular learning (e.g., undergraduate student-edited literary journals, reading groups), and interdisciplinary study experience before graduation.
   - Boundary: In-program student development before graduation = <M05>; post-graduation career fields, placement rates, graduate school destinations, or alumni career/life testimonies = <M10>.

6. <M06> Mapping institutional research agenda and specializations (界定研究议程与学术专长)
   - Core Question: What scholarly fields, historical periods, regions, theoretical questions, and interdisciplinary clusters do THIS department and its faculty actively research?
   - Includes: Research specializations, theoretical/methodological orientations, and interdisciplinary research clusters explicitly belonging to THIS target department's scholars.
   - Boundary: Must describe THIS target department's research agenda! External library/consortium scope = <M07>; publication/grant counts or awards = <M08>; listing center names only = <M01>.

7. <M07> Presenting faculty strength and support resources (展示师资力量与支撑资源)
   - Core Question: What human, material, archival, financial, and student-support resources enable learning and research?
   - Includes: Faculty scale, academic ranks, doctoral ratios, visiting/foreign/teaching faculty teams, student-faculty ratio, libraries, archival collections, language/VR/interpretation labs, regular scholarships/fellowships/travel grants/fee waivers available to students or scholars, and academic/advising support services.
   - Boundary: Input conditions & available support/funding = <M07>; prestigious awards won, rankings, key-discipline titles, or research output counts = <M08>; mandatory regulatory rules/deadlines = <M13>; fundraising appeals asking alumni/donors to give money = <M13>.

8. <M08> Establishing academic reputation and achievements (证明学术声誉与办学成就)
   - Core Question: What external rankings, official accreditations, cumulative outputs, awards, or landmark achievements prove the institution's excellence?
   - Includes: QS/domestic rankings, National First-Class / Key Discipline status, cumulative grant/book/paper achievements, faculty/student honors & prizes, student course-rating acclaim, first-in-the-country pioneers, cumulative summaries of major conferences hosted, and dated news items reporting specific recent awards, appointments, or book publications.
   - Boundary: Undated/cumulative conference or achievement summaries = <M08>; future aspirations = <M11>.

9. <M09> Presenting institutional partnerships and international exchange (展示合作网络与国际交流)
   - Core Question: With which domestic/international universities, academic consortia, or partner institutions has the department built collaborative networks or exchange channels?
   - Includes: Inter-university agreements, international academic consortium memberships, reciprocal institutional agreements, study abroad / student exchange / 2+2 joint programs, and visiting scholar exchange networks.
   - Boundary: Institutional partnerships & study-abroad/exchange channels = <M09>; students acquiring intercultural skills inside campus courses = <M05>; one-way public service/training delivered to local society/government = <M03>.

10. <M10> Presenting graduate outcomes and alumni development (展示毕业出路与校友发展)
    - Core Question: Where do graduates go after graduation, what careers do they pursue, and how do alumni reflect on their lifelong gains?
    - Includes: Post-graduation career sectors/professions (including "prepare students for careers in..." and "graduates have become doctors, lawyers, CEOs..."), employment/further-study rates, alumni network scale, and named alumni career stories or testimonies.

11. <M11> Projecting future vision and strategic plans (展望未来愿景与建设规划)
    - Core Question: Looking ahead, what future vision, strategic goals, or development initiatives does the institution commit to?
    - Includes: Forward-looking institutional commitments and strategic plans with explicit future orientation ("Looking ahead...", "will continue to build...", "aim to ensure that X continues to be...").
    - Boundary: Requires institutional subject + future orientation; "look forward to welcoming you" = <M12>.

12. <M12> Welcoming and prompting reader engagement & contact (致意欢迎与联系到访)
    - Core Question: How does the text directly greet readers ("you") or invite them to explore, apply, visit, or get in touch? At what physical address, room, phone, fax, email, office hours, or designated contact person can readers reach the institution?
    - Includes: Direct greetings/warm welcome headings ("A Warm Welcome from...", "Welcome to...!"), warm closing wishes, explicit reader-directed action prompts ("We warmly invite you to explore...", "Learn more about...", "Please don't hesitate to get in touch...", step-by-step "Explore / Contact / Apply" prompts); office locations, street addresses, room numbers, office hours, phone/fax numbers, email addresses, and designated contact cards.
    - Boundary: Fundraising/donation calls = <M13>; static office addresses/phones/emails grouped into ONE <M12> block; bare "Contact Us" headings = <OTHER>; bare UI navigation buttons without sentence punctuation = <OTHER>.

13. <M13> Specifying regulations, announcements and acknowledgements (规定规章、播报动态与鸣谢)
    - Core Question: What mandatory eligibility thresholds, credit quotas, administrative procedures, or legal/endorsement disclaimers must be obeyed? Which specific dated lecture/event is being announced, or which named recent news item just occurred? How does the text invite alumni/public donations, explain gift impact, or thank named donors/endowments? How does the community mourn a deceased individual?
    - Includes: Binding admission/degree requirements ("must", "are required to"), credit minimums, application deadlines/compliance procedures, official disclaimers; dated upcoming lectures/seminars/workshops and dated news items reporting specific recent awards, appointments, or book publications; donation calls ("Give Today", "Make a gift", "Support the Department..."), statements of how gifts help students, donation channels, acknowledgements of named donors/endowed funds; obituaries, "In Memoriam" notices, and tributes for deceased human individuals.
    - Boundary: DO NOT fall for the word "eligibility" when promoting a scholarship/seminar benefit—benefits/support = <M07>! <M13> strictly requires binding institutional rules, procedures, or legal disclaimers. Commemorating historical event anniversaries is NOT <M13>; general founding history = <M02>. Institutional scholarships/fellowships offered to students = <M07>; philanthropic giving/donor gratitude = <M13>.

--- QUALITY-CONTROL FILTER LABEL ---
14. <OTHER> Non-propositional web artifacts, unelaborated rosters, and out-of-scope residue
    - (a) Isolated webpage navigation menus, section headings lacking propositional verbs, HTML/image-alt fragments, garbled characters, or collector notes;
    - (b) Scraped directory rosters consisting purely of person cards without prose sentences, as well as repeated sidebar/footer blocks duplicated across scraped subpages;
    - (c) Out-of-scope text belonging to a completely non-language department accidentally concatenated into the file OR self-descriptions spoken in the voice ("we") of an external third-party organization.

======================================================================
LEARN INSTRUCTION 2: STANDARD SENTENCE-BY-SENTENCE ANNOTATION FORMAT
======================================================================
Annotate prose text SENTENCE BY SENTENCE, placing ONE complete sentence per line, with XML tags ONLY at the very start and very end of each complete sentence.

======================================================================
LEARN INSTRUCTION 3: COMBINED MOVES ON A SINGLE COMPLETE SENTENCE
======================================================================
Sometimes a single complete sentence genuinely realizes TWO co-equal rhetorical moves simultaneously. Keep the entire sentence intact and wrap with nested tags `<MXX><MYY>...</MYY></MXX>`. Outer tag = dominant move; if tied, lower number outer.

======================================================================
LEARN INSTRUCTION 4: DO NOT OVER-COMBINE SUBORDINATE MODIFIERS
======================================================================
Only assign combined tags when BOTH moves carry independent, co-equal propositional weight. Brief phrases appearing as subordinate modifiers supporting ONE clear dominant move → assign ONLY the single dominant move.

======================================================================
LEARN INSTRUCTION 5: AVOID POSITIONAL BIAS & LEXICAL TRIGGER TRAPS
======================================================================
1. "eligibility" Trap → benefit = <M07>, not <M13>.
2. "race / gender / social justice" Course Topic Trap → course description = <M04>, not <M03>, unless institution declares a public moral pledge.
3. Historical Timeline vs. Current Offerings vs. News Trap → chronological past = <M02>; present-day program summary = <M04>; undated cumulative achievement = <M08>; dated specific news = <M08> (within M08).
4. Institutional Scholarships (<M07>) vs. Donor Philanthropy (<M13>).
5. External Partner Scope vs. Department's Own Research (<M06>) & Third-Party Voice (<OTHER>).

======================================================================
LEARN INSTRUCTION 6: HANDLING HEADINGS, SIGNATURES, CONTACTS & LISTS
======================================================================
1. Empty generic section headings, breadcrumbs, navigation menus, directory filter lists, bare directory cards -> <OTHER>.
2. Headings that explicitly perform a rhetorical move -> tag with that move.
3. Structured contact address blocks -> wrap as <M12>; leader sign-offs -> wrap together as ONE <M01> block.

======================================================================
FINAL EXECUTION TASK
======================================================================
Annotate EVERY unit in the following text using ONLY <M01>–<M13> or <OTHER>. Preserve 100% of original words, spelling, and punctuation. One complete sentence per line. Output ONLY the XML-annotated text.

### INPUT TEXT TO ANNOTATE:
[PASTE RAW UNIVERSITY .TXT CONTENT HERE]
===== END AI PROMPT =====
