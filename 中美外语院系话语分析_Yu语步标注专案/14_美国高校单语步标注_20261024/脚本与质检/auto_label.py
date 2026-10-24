#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10 核心语步规则辅助标注器 v2（单语步优先，分阶段判定）。

阶段化判定（越靠前优先级越高）：
  A 非命题网页残片 -> OTHER
  B 联系方式 / 地址块 -> M10
  C 人员名录卡（纯人名 / 人名+职务 / 职务行 / 带竖线名片） -> M01（含邮箱电话者已在 B 归 M10）
  D 语步强特征短语（使命愿景 / 创办沿革 / 欢迎捐赠 / 办事规程） -> 对应语步
  E 加权线索打分（含历时叙事、培养课程、实绩声誉等专门线索），并列时按体裁优先序裁决
"""
import json
import os
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(BASE, "segments", "skeleton.json")
LAB = os.path.join(BASE, "labels")
OVR = os.path.join(BASE, "overrides.tsv")

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)
PHONE = re.compile(r"\(?\b\d{3}\)?[ .-]\d{3}[- .]\d{4}\b|\b\d{3}-\d{4}\b|\+\d{1,3}[ -]\d{2,4}[ -]\d{3,}")
ADDR = re.compile(r"\b(P\.?\s?O\.?\s?Box|Suite \d|Room \d|Rm\.? \d|\d+\s+(Massachusetts|Harvard|Huntington|College|Campus|"
                  r"Street|Avenue|Road|Place|Street|Yard)|Cambridge,? MA|Providence,? RI|Atlanta,? GA|New York,? NY|"
                  r"Durham,? NC|Baltimore,? MD|Boston,? MA|[A-Z]{2}\s?\d{5}(-\d{4})?)\b")
YEAR = re.compile(r"\b(1[6-9]\d\d|20[0-2]\d)\b")
PAST = re.compile(r"\b(was|were|had|began|became|received|joined|served|established|founded|created|opened|"
                  r"introduced|awarded|appointed|moved|built|acquired|published|died|retired|arrived|left|"
                  r"launched|initiated|formed|merged|renamed|organized|held|taught|wrote|completed|graduated|"
                  r"enrolled|expanded|grew|emerged|started|founded)\b", re.I)
TITLE_WORDS = re.compile(r"\b(Professor|Lecturer|Instructor|Reader|Chair|Director|Dean|Manager|Coordinator|Officer|"
                         r"Fellow|Librarian|Curator|Associate|Assistant|Adjunct|Visiting|Emerit|Postdoctoral|"
                         r"Specialist|Analyst|Administrator|Secretary|Treasurer|President|Head of|Faculty)\b")

NAV_WORDS = {
    "about", "about us", "people", "faculty", "staff", "contact", "contact us", "admissions", "apply",
    "giving", "give", "news", "events", "calendar", "directory", "search", "menu", "home", "read more",
    "learn more", "overview", "mission", "history", "vision", "leadership", "administration", "research",
    "academic programs", "undergraduate", "graduate", "courses", "students", "alumni", "resources",
    "library", "libraries", "news & events", "in memoriam", "support us", "visit", "instagram",
    "facebook", "twitter", "youtube", "linkedin", "newsletter", "subscribe", "share", "print",
    "executive committee", "advisory board", "leadership council", "faculty affiliates", "fellows",
    "current fellows", "past fellows", "visiting scholars", "mailing address", "office hours",
    "all programs", "majors", "minors", "certificates", "people directory", "faculty directory",
    "department of", "programs", "departments", "centers", "institutes", "our people", "our faculty",
    "our students", "our alumni", "student life", "careers", "faq", "faqs", "forms", "policies",
}

CUES = {
    "M01": [(2.2, r"\b(consists? of|comprises?|is composed of|is made up of|is divided into|is organized into|"
                   r"is governed|composed of faculty|steering committee|executive committee|advisory board|"
                   r"leadership council|working group|subcommittee|is chaired|committee members|"
                   r"reports? to|oversees?|serves? as (chair|director|secretary))\b")],
    "M02": [(2.5, r"\b(founded|established|founding|chartered|renamed|predecessor|traces? (its|the)|"
                   r"origins?|since its inception|first (class|course|professor|chair|program|degree)|"
                   r"timeline|anniversary|commemorat|in memoriam|passed away|obituary|tribute|legacy|"
                   r"bequeath|heritage|milestone|early history|was named after|in honor of)\b"),
            (1.1, r"\b(in|since|during|by|from)\s+(the\s+)?(1[6-9]\d\d|20[0-2]\d)\b")],
    "M03": [(2.6, r"\b(our mission|mission statement|mission of|our vision|vision (of|statement|is)|values|"
                   r"committed to|commitment to|dedicated to|strives? to|we believe|our (goal|purpose)|"
                   r"guiding principle|inclusiv|diversity,? equity|antiracis|anti-racis|land acknowledgment|"
                   r"social justice|public good|equitable|belonging|will continue|plans? to expand|"
                   r"strategic (plan|vision|priorit|framework)|we acknowledge|traditional homelands|"
                   r"indigenous (peoples|lands)|our (values|principles)|equity and inclusion)\b")],
    "M04": [(2.0, r"\b(research (interests?|areas?|fields?|agenda|projects?|clusters?|groups?|centers?)|"
                   r"areas? of (study|specialization|inquiry|research)|fields? of (study|inquiry)|"
                   r"scholars? working|methodolog|interdisciplinary|the study of)\b"),
            (0.9, r"\b(disciplinary|scholarship|intellectual|inquiry|theoretical (framework|approach)|"
                   r"humanities|critical (thinking|analysis)|research)\b")],
    "M05": [(2.4, r"\b(majors?|minors?|concentrations?|degree (programs?|requirements?)|curricul|"
                   r"course (offerings|work|requirements?|descriptions?)|courses?( in| on| include| are| like)|"
                   r"seminar|pedagog|teaching (methods?|philosophy)|students? (learn|will learn|develop|"
                   r"are trained|gain|acquire)|language (study|instruction|classes|courses|program)|"
                   r"certificate|requirements? for the|core (courses?|requirements?)|electives?)\b")],
    "M06": [(2.2, r"\b(faculty (members?|size|positions?|lines?)|full-time|part-time|student[- ]faculty ratio|"
                   r"library|holdings?|collections?|archives?|labs?\b|laborator|equipment|"
                   r"fellowships?|scholarships?|financial aid|stipends?|tuition|resources?|"
                   r"support (services?|for students)|advising|mentoring|wellness|counseling|"
                   r"fellowship|scholarship|grant|stipend|financial support)\b"),
            (1.8, r"\b\d[\d,]*\s+(interdisciplinary\s+)?(faculty|staff|students?|teachers?|librarians?|"
                  r"postdocs?|graduate students?)\b")],
    "M07": [(2.0, r"\b(ranked|ranking|top \d|No\.\s?\d+|awards?|prizes?|honors?|winner|won |recognized|acclaim|"
                   r"prestig|distinction|renowned|leading|publications?|published|placement|career outcomes?|"
                   r"alumni (have|who|work)|graduates? (have|go on|work|are|pursue)|employed|employment|"
                   r"Nobel|Pulitzer|Guggenheim|MacArthur|Rhodes|Fulbright|"
                   r"gone on to|have become|career (paths?|fields?|outcomes?)|placement record|"
                   r"distinguished alumni|our alumni|alumni (network|community))\b"),
            (1.6, r"\b(professor of|scholar of|author of|editor of|recipient of)\b")],
    "M08": [(2.2, r"\b(partner(ship)?s?|collaborat|consortium|exchange (program|agreement|students)|"
                   r"study abroad|abroad|overseas|joint (program|degree)|dual degree|internship|"
                   r"outreach|community (engagement|partners?|service|programs?)|public (service|programming)|"
                   r"agreements? with|affiliat|co-?sponsor)\b")],
    "M09": [(2.8, r"\b(welcome (to|from)|we (warmly |cordially )?(invite|welcome)|join us|"
                   r"your (gift|support|contribution)|donate|giving|make a gift|give today|support (us|our)|"
                   r"thank (you|our)|we thank|grateful|please (consider|join|explore|visit)|"
                   r"prospective students|we look forward|you (will|can|'ll) )\b")],
    "M10": [(2.6, r"\b(office hours?|contact|email|phone|fax|mailing address|directions|parking|"
                   r"hours of operation|appointment|deadline|apply by|applications? (are|must|due|open)|"
                   r"eligib|prerequisite|must (be|submit|complete|have|provide)|polic(y|ies)|procedures?|"
                   r"forms?|register|registration|visa|fee|when:|where:|zoom|RSVP|subscribe|newsletter|FAQs?)\b")],
}

STRONG = [
    ("M09", re.compile(r"\b(welcome to|we (warmly |cordially )?invite|make a gift|donate|give today|"
                       r"join us|we look forward|thank you for|grateful to our)\b", re.I)),
    ("M03", re.compile(r"\b(our mission|mission statement|our vision|vision statement|"
                       r"we are committed to|land acknowledgment|statement of (inclusion|commitment|solidarity))\b", re.I)),
    ("M02", re.compile(r"\b(was founded in|was established in|founded in|established in|renamed|merged with|"
                       r"in memoriam|passed away|commemorat|anniversary of)\b", re.I)),
    ("M10", re.compile(r"(office hours|mailing address|@\w+\.\w+|deadline|applications? (are|must|due)|"
                       r"register (now|here|for)|RSVP)", re.I)),
]

PRIORITY = ["M05", "M06", "M07", "M02", "M08", "M01", "M10", "M03", "M09", "M04"]
PROC_Q = re.compile(r"\b(appl(y|ication)|deadline|requirement|advisor|tuition|cost|funding|financial aid|visa|"
                    r"housing|eligib|register|visit|tours?|contact|submit|credits?|exam|GRE|TOEFL|transcript)\b", re.I)


def norm(t):
    return re.sub(r"\s+", " ", t.replace("\n", " | ")).strip()


def is_nav(u):
    s = u.strip()
    low = s.lower().strip(" :.-–—&|")
    if len(s) > 55 or re.search(r"[.!?]$", s):
        return False
    if low in NAV_WORDS:
        return True
    if re.fullmatch(r"(19|20)\d\d(–|-)?((19|20)\d\d)?", low):
        return True
    if re.fullmatch(r"[\d\W_]+", s):
        return True
    return False


HEAD_HEADS = re.compile(r"^(Our |The |Department|Center|Centre|Program|Faculty|Staff|Students?|Alumni|"
                         r"Leadership|Administration|Committee|Board|Council|Fellows?|Courses?|Programs?|"
                         r"Research|Resources|Library|Collections?|Mission|Vision|History|Contact|Events?|News|"
                         r"Opportunities|Requirements?|Funding|Awards?|Publications?|Giving|Support|People|"
                         r"Directory|Admissions|Apply|Visit|About|Academics?|Curriculum|Language|Languages|"
                         r"Undergraduate|Graduate|Financial|Forms?|Polic|Services?|Community|Outreach|"
                         r"Partners?|Affiliations|Spotlight|Publications|Journals?|Series|Lectures?|Seminars?)")


def is_section_label(u):
    """裸小节标题 / 目录标签：无谓语、无句末标点、非人名。"""
    s = u.strip()
    if len(s) > 62 or re.search(r"[.!?]$", s) or EMAIL.search(s):
        return False
    if re.search(r"\b(is|are|was|were|has|have|had|will|can|offers|provides|includes|serves|works|teaches|"
                 r"conducts|houses|grants|supports|founded|established)\b", s, re.I):
        return False
    if len(s.split()) > 7:
        return False
    if re.fullmatch(r"[A-Z0-9&/,:\-’' ]{4,}", s) and len(s.split()) >= 1:   # 全大写标题
        return True
    if s.lower().strip(" :.-–—&|") in NAV_WORDS:
        return True
    if HEAD_HEADS.match(s):
        return True
    if re.match(r"^(Vision|Mission|History|About|Overview|Contact|Events|News)\b", s):
        return True
    return False


NOT_NAME = set("""our the and of for in on at to with a an
program programs studies study department departments center centers centre centres institute institutes
school schools college colleges university universities faculty staff students student alumni
prize prizes award awards fellowship fellowships grant grants waiver waivers fee fees registration
research teaching learning language languages literature literatures history arts sciences humanities
meet about overview mission vision values news events contact giving support apply admissions
leadership administration committee board council office offices resources library libraries
publications journal journals series lecture lectures seminar seminars events workshop workshops
initiative initiatives project projects conference conferences fund funds foundation institute
summer spring fall winter annual report reports review reviews bulletin newsletter
director directors dean deans chair chairs professor professors lecturer lecturers instructor
graduate undergraduate doctoral master masters bachelor minor majors minors concentration concentrations
east west north south asia africa europe america american asian african european pacific global
studies center center's hall building room floor campus""".split())


def is_name_only(u):
    s = u.strip()
    if re.search(r"[.?!:;]", s) or EMAIL.search(s) or re.search(r"\d", s):
        return False
    toks = s.replace(",", " ").split()
    if not (2 <= len(toks) <= 5):
        return False
    if all(t.isupper() for t in toks if len(t) > 1):
        return False          # 全大写 = 栏目名，不是人名
    small = {"de", "van", "der", "von", "bin", "al", "da", "di", "la", "el"}
    for t in toks:
        if t.lower() in small:
            continue
        if t.lower().strip(".,") in NOT_NAME:
            return False
        if not re.fullmatch(r"[A-Z][A-Za-z’'\-\.]*", t):
            return False
    return True


def is_person_card(u):
    """人名+职务，或带竖线的名片，或纯职务行。"""
    s = u.strip()
    if s.startswith("-") or s.startswith("•"):
        return False
    if "|" in s:
        parts = [p.strip() for p in s.split("|") if p.strip()]
        if not parts:
            return False
        if TITLE_WORDS.search(s) or any(is_name_only(p) for p in parts if len(p.split()) <= 5):
            return EMAIL.search(s) is None and PHONE.search(s) is None
    if is_name_only(s):
        return True
    if TITLE_WORDS.match(s) and 2 <= len(s.split()) <= 16 and not re.search(r"[.!?]$", s):
        return True
    m = re.match(r"^[A-Z][A-Za-z’'.\-]+(?: [A-Z][A-Za-z’'.\-]+){1,3}, ", s)
    if m and TITLE_WORDS.search(s) and len(s.split()) <= 22:
        return True
    return False


def is_contact(u):
    s = u.strip()
    if EMAIL.search(s) or PHONE.search(s):
        return True
    if re.match(r"^(Mailing Address|Address|Contact|Office|Phone|Fax|Email|E-mail|Tel)\b", s, re.I):
        return True
    if ADDR.search(s) and (re.search(r"\b\d{5}\b", s) or re.search(r"(Street|Avenue|Road|Suite|Room|Building)", s)):
        return True
    return False


def is_pub_title(u):
    s = u.strip()
    if re.search(r"(Press|University Press|Journal of|Review\b)", s) and not re.search(r"\b(is|are|was|were)\b", s):
        return True
    if re.match(r"^[\"“].+[\"”]", s) and len(s.split()) < 25:
        return True
    if re.match(r"^[A-Z][^.!?]{5,80}: [A-Z]", s) and not re.search(r"\b(is|are|was|were|offers?)\b", s):
        return True
    return False


def score(u):
    sc = {k: 0.0 for k in CUES}
    for mv, cues in CUES.items():
        for w, pat in cues:
            hits = re.findall(pat, u, re.I)
            if hits:
                sc[mv] += w * min(len(hits), 3) ** 0.6
    return sc


def classify(u):
    """返回 (语步, 判定路径)。路径：det=确定性规则，strong=强特征，score=加权打分，fallback=弱兜底。"""
    s = norm(u).strip()
    if not s:
        return "OTHER", "det"
    if re.fullmatch(r"[-–•*\s\d.)]+", s):
        return "OTHER", "det"
    # B 联系方式 / 地址块 -> M10
    if is_contact(s):
        return "M10", "det"
    # A 非命题网页残片 -> OTHER
    if re.match(r"^(Download|Click here|Read more|Learn more|Share|Print|Subscribe)\b", s, re.I) and len(s.split()) <= 12:
        return "OTHER", "det"
    if re.match(r"^(For more information|More information|See also|Learn more|Read the full|Click)", s, re.I):
        return "M10", "det"
    if is_section_label(s):
        if not re.search(r"\b(mission|vision|welcome|donate|giving)\b", s, re.I) or len(s.split()) <= 3:
            return "OTHER", "det"
    if re.match(r"^(Research Interests?|Areas? of (Focus|Interest|Study)|Current Research|Selected Publications|"
                r"Publications|Books?|Recent (Work|Publications))\b", s, re.I):
        return ("M04" if re.match(r"^(Research|Areas|Current)", s, re.I) else "M07"), "det"
    # C 人员名录卡 -> M01（纯人名 / 人名+职务 / 职务行 / 竖线名片）
    if is_person_card(s):
        return "M01", "det"
    # C2 职称/头衔碎片（名单页常见）-> M01
    if TITLE_WORDS.search(s) and not re.search(r"[.!?]$", s) and len(s.split()) <= 20 \
            and not re.search(r"\b(is|are|was|were|has|have|offers?|provides?|includes?|serves?)\b", s):
        return "M01", "det"
    # C3 年份开头的时间轴条目 -> M02
    if re.match(r"^(1[6-9]\d\d|20[0-2]\d)(–|-|:)", s) or re.match(r"^\d{4}s?[,:]", s):
        return "M02", "det"
    # D 语步强特征
    for mv, pat in STRONG:
        if pat.search(s):
            return mv, "strong"
    # 高频修辞/事务句式定向修正
    if re.search(r"\b(support (the|our) (department|center|institute|program|school|library)|"
                 r"make (a|your) (gift|donation)|donate (now|today|to)|ways to give)\b", s, re.I):
        return "M09", "det"
    if re.search(r"\b(we are (seeking|searching for)|the (successful|ideal) candidate|job (posting|opening)|"
                 r"position (is|will)|apply (by|through|online)|application (deadline|materials|process)|"
                 r"interested in (becoming|applying)|to apply|eligib)\b", s, re.I):
        return "M10", "det"
    if re.search(r"\b(learn more|read more|visit (our|the) .{0,40}(page|site|website)|"
                 r"for (more )?(details|information),? (visit|see|contact)|click here|see our)\b", s, re.I):
        return "M09", "det"
    if re.match(r"^(What|How|Who|Why|When|Where) (is|are|does|do|can|should)\b", s) and \
            re.search(r"\b(program|degree|course|major|minor|apply|admission|curriculum)\b", s, re.I):
        return "M05", "det"
    # FAQ / 程序性问句
    if s.endswith("?"):
        return ("M10" if PROC_Q.search(s) else "M04"), "det"
    if is_pub_title(s):
        return "M07", "det"
    sc = score(s)
    best = max(sc, key=lambda k: (sc[k], -PRIORITY.index(k)))
    top = sc[best]
    # E 兜底
    if top < 0.9:
        if PAST.search(s) and (YEAR.search(s) or re.search(r"\b(first|early|originally)\b", s, re.I)):
            return "M02", "det"
        if re.search(r"\b(courses?|teach|students?|seminars?|curriculum)\b", s, re.I):
            return "M05", "fallback"
        if re.search(r"\b(research|scholars?|stud(y|ies)|disciplines?|fields?)\b", s, re.I):
            return "M04", "fallback"
        return ("OTHER" if len(s.split()) <= 6 else "M04"), "fallback"
    # 历时叙事：过去时 + 年份/首任/早期 -> M02
    if PAST.search(s) and (YEAR.search(s) or sc["M02"] > 0):
        return "M02", "det"
    return best, "score"


def load_overrides():
    d = {}
    if os.path.exists(OVR):
        for line in open(OVR, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            stem, gid, lab = line.rstrip("\n").split("\t")[:3]
            d[(stem, int(gid))] = lab
    return d


def main():
    skel = json.load(open(SKEL, encoding="utf-8"))
    os.makedirs(LAB, exist_ok=True)
    ovr = load_overrides()
    for f, rec in skel.items():
        stem = f[:-4]
        labs, prev, run, paths = [], "OTHER", 0, []
        for i, u in enumerate(rec["units"]):
            if (stem, i) in ovr:
                lab, path = ovr[(stem, i)], "override"
            else:
                lab, path = classify(u)
                if path == "fallback":
                    # 上下文继承：仅在弱兜底且连续不超过 2 句、且上文非人员名录时沿用上文语步
                    if run < 2 and prev not in ("OTHER", "M01"):
                        lab = prev
                    run += 1
                else:
                    run = 0
            if lab == "M01":
                toks = s_ = norm(u).replace("|", " ").replace(",", " ").split()
                if len(toks) == 1:            # 孤立单词，多半是栏目标签
                    lab = "OTHER"
            labs.append(lab)
            paths.append(path)
            if lab != "OTHER":
                prev = lab
        with open(os.path.join(LAB, stem + ".labels.tsv"), "w", encoding="utf-8") as fh:
            fh.write("# gid\tlabel\n")
            for i, l in enumerate(labs):
                fh.write(f"{i}\t{l}\n")
        with open(os.path.join(LAB, stem + ".paths.tsv"), "w", encoding="utf-8") as fh:
            for i, pa in enumerate(paths):
                fh.write(f"{i}\t{pa}\n")
        c = Counter(labs)
        print(f"{stem:38s} units={len(labs):5d} " + " ".join(f"{k}:{c[k]}" for k in sorted(c)))


if __name__ == "__main__":
    main()
