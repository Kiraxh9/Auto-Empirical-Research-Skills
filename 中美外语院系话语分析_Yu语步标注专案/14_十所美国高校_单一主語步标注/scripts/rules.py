# -*- coding: utf-8 -*-
"""第一遍规则初标（v4）：优先级级联 + 计分兜底，输出单一主導語步与置信度。

判据来源：06_中美高校外语院系_精炼10核心语步编码手册.csv（M01–M10 + OTHER）
"""
import re

# ---------------- 词汇表 ----------------
VERB = set("""is are was were be been being am has have had do does did will would can could may might must
offers offer offered provides provide provided includes include included consists comprise comprises serves serve
welcomes welcome invited invite joins join teaches teach taught studies study studied conducts conduct conducted
supports support supported promotes promote focuses focus focused engages engage fosters foster created create
establishes established trains train prepares prepare develops develop encourages encourage brings bring
makes make gives give helps help works work leads lead directs direct oversees oversee manages manage
pursues pursue explores explore examines examine analyzes analyze represents represent contributed contribute
hosts host holds hold dedicates dedicate commits commit strives strive aspires aspire aims aim emphasizes emphasize
announces announced presents presented enables enable allows allow began begins built builds received receives
published publishes awarded awards honors honor celebrates celebrate recognizes recognize reflect reflects
""".split())

NAV_EXACT = set("""about about-us academics admission admissions alumni apply calendar contact contact-us courses
directory donate events faculty give give-now graduate home library menu news news-events people programs
research resources staff students undergraduate graduate-program why-study welcome read-more learn-more
view-all see-all more next previous search share print skip-to-main-content back-to-top return-to-top main-menu
site-search faculty-directory student-resources financial-aid career-outcomes learning-outcomes requirements
curriculum course-list faculty-publications faculty-news student-spotlight upcoming-events past-events all-events
event-calendar contact-information mailing-address office-hours phone email fax directions parking hours
about-the-department our-faculty our-people our-programs our-research our-students faculty-staff faculty-and-staff
faculty-profiles fields-of-study academic-programs research-areas undergraduate-studies graduate-studies
prospective-students current-student alumni-friends support-us maps-directions news-events-opportunities
statement-of-commitment faculty-instructors skidmore-collection study-abroad visiting-scholars-fellows-associates
board-of-visitors resources-for-faculty funding-for-students officers read
""".split())

NOISE_PATTERNS = [
 r'^skip to\b', r'^back to\b', r'^return to\b', r'^read (more|the story|full|all)\b', r'^learn more\b',
 r'^view (all|profile|more)\b', r'^see (all|more|our)\b', r'^click here\b', r'^follow us\b',
 r'^(share|print|tweet|bookmark|email this)\b', r'^(instagram|facebook|twitter|youtube|linkedin|flickr|tiktok)\b',
 r'^(menu|search|close|toggle|previous|next|home|read|more)$', r'^[\W_]+$',
 r'^(image|photo|video|podcast|listen|watch)\s*:?\s*$',
 r'\b(pictured|left to right|photo by|image credit|credit:)\b',
 r'^\d{1,2}/\d{1,2}/\d{2,4}$', r'^(authored|written|posted|published|compiled) by\b',
 r'^(loading|javascript|your browser)\b', r'^https?://\S+$', r'^www\.\S+$', r'^©', r'^copyright\b',
 r'^all rights reserved', r'^(tags?|categories|filed under)\b', r'^(share this|share on)\b',
 r'^(explore our site|use the navigation|navigation tabs)', r'^-?\s*[A-Z][A-Za-z &]{2,40}$',
]

def words(t):
    return re.findall(r"[A-Za-z][A-Za-z'’\-]*", t)

def has_verb(t):
    return bool({w.lower() for w in words(t)} & VERB)

def is_heading(t):
    s = t.strip()
    if '\n' in s or len(words(s)) > 9 or re.search(r'[.!?]$', s):
        return False
    if has_verb(s) or re.search(r'\d{4}', s):
        return False
    if s.isupper():
        return True
    caps = [w for w in words(s) if w[:1].isupper()]
    if len(caps) >= max(1, (len(words(s)) + 1) // 2):
        return True
    return len(words(s)) <= 4

def is_noise(t):
    """纯导航/标题/残片 → OTHER。"""
    s = t.strip()
    if not s:
        return True
    low = re.sub(r'\s+', ' ', s.lower()).strip(' .:')
    if low.replace(' ', '-') in NAV_EXACT or low in NAV_EXACT:
        return True
    if len(s) <= 3 and not re.search(r'\d', s) and not re.search(r'[.!?]$', s):
        return True
    for p in NOISE_PATTERNS:
        if re.search(p, s, re.I):
            return True
    # 断句残片：以小写开头 / 结尾省略号 / 纯日期时间
    if re.match(r'^[a-z]', s) and len(words(s)) < 25:
        return True
    if s.endswith('...') or s.endswith('…'):
        return True
    if re.fullmatch(r'[\d\s,./–\-:%&]+', s):
        return True
    if re.fullmatch(r'(19|20)\d\d(?:[–-](19|20)?\d\d)?', s.strip(' .,')):
        return True
    if ADDRESS.search(s) or person_card(s) or ROLE_NAME.match(s):
        return False
    if is_heading(s) and not s.lstrip().startswith(('-', '•', '*')):
        return True
    return False

# ---------------- 级联规则 ----------------
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
PHONE = re.compile(r'(\(\d{3}\)\s?\d{3}-\d{4}|\d{3}[.-]\d{3}[.-]\d{4}|\b\d{8,}\b)')
ADDRESS = re.compile(r'\b(\d{1,5}\s*(&\s*\d/\d)?\s+[A-Z][\w.]*(\s+[A-Z][\w.]*)*\s+(Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Drive|Dr\.?|Place|Pl\.?|Lane|Way|Square|Circle)\b|[A-Z][a-z]+,\s?[A-Z]{2}\s?\d{5}|Room\s+\d|Suite\s+\d|Building\b|Box\s+\d{4,})')
DIRECT = re.compile(r'\b(turn (left|right)|head (north|south|east|west)|exit \d|off ?ramp|transfer to the|line station|subway|metro|metrorail|bus(es)? stop|from the airport|take the (green|red|blue|orange|silver|yellow) line|parking lot|pedestrian bridge)\b', re.I)
TIMELINE = re.compile(r'^\s*[-\u2022]?\s*((19|20)\d\d([–\-]\d{2,4})?\s*[:/\-–—\n]|(19|20)\d\d,\s)', re.I)
PERSON = re.compile(r"^[A-Z][\w'’\-]+(?:\s+[A-Z]\.?)?\s+[A-Z][\w'’\-]+(?:\s+[A-Z][\w'’\-]+)?\s*(\n|,|$)")
ROLE_NAME = re.compile(r'^[A-Z][A-Za-z &/\-]{3,45}:\s*[A-Z][\w\'’\-]+\s+[A-Z][\w\'’\-]+')
ALUM_MARK = re.compile(r"(?:A\.B\.|B\.A\.|Ph\.D\.|M\.A\.|M\.F\.A\.|'9\d|'0\d|AB '|class of)")
FUNDING = re.compile(r'\b(scholarships? (fund|program|award|support|for)|fellowships?|financial aid|stipend|tuition (waiver|remission|assistance|support)|graduate assistantships?|teaching assistantships?|research assistantships?|grants? (are|is|for|to)|funding (package|opportunit|support)|flas|scholarship (fund|program))\b', re.I)
GOVERN = re.compile(r'\b(approve|reject|vote|appoint(s|ed)?|oversee(s|ing)? (the )?(strategic|academic|financial)|executive committee|faculty governance|steering committee|advisory board|confers? the following privileges|renewed annually|appointment (is|of|renewal))\b', re.I)
STRATEGY = re.compile(r'^[-\u2022\d.)\s]+?(recruit|retain|expand|increase|strengthen|build|foster|enhance|deepen|double|grow|integrate|advance|promote|create|establish|launch|ensure|secure|sustain)\b', re.I)
BIOHIST = re.compile(r'\b(spent [\w\- ]{0,25}years?|spent (two |three |four |several )?decades?|studied (at|under)|received (his|her|their) (ph\.?d|doctorate|degree)|earned (his|her|their)|descended from|was born|emigrated|attended|graduated from|taught at)\b', re.I)
OUTCOMES2 = re.compile(r'\b(time[- ]to[- ]degree|completion (rate|data)|admissions? (and )?enrollment statistics|graduation rate|career outcomes?|placement (rate|record))\b', re.I)
CELEBRATE = re.compile(r'\b(celebrate|celebrating) (their|our|the) (achievements|success|work)\b|\b(their|our) (achievements|accomplishments)\b', re.I)

NUMBERED_OUTCOME = re.compile(r'^\s*[-\u2022]?\s*\d?[\).]?\s*(use|apply|demonstrate|analy[sz]e|interpret|evaluate|construct|develop|articulate|identify|compare|explain|write|read|speak|locate|situate)\b', re.I)
LINKRUN = re.compile(r'(\s/\s.*){3,}')
JOURNAL_ITEM = re.compile(r"^[-\u2022]\s*(?:[A-Z][\w'’\-]*|of|and|the|in|for)(?:\s+(?:[A-Z][\w'’\-]*|of|and|the|in|for)){0,7}\s*(?:\([A-Z]+\))?\.?$")
PROUD = re.compile(r'\b(proud to (be|support|offer|work)|at the center of conversations|tolerance, justice)\b', re.I)

DEGREE = re.compile(r'\b(major|minor|concentration|degree|program|ph\.?d\.?|m\.?a\.?|b\.?a\.?|b\.?s\.?|m\.?s\.?|certificate|curriculum|courses?|coursework|seminars?|credits?|requirements?|electives?|thesis|dissertation)\b', re.I)
OUTCOME = re.compile(r'\b(majors?|students?|graduates?)\s+(should|will|can|are able to|learn to|develop|gain|acquire|demonstrate)\b|\blearning (outcomes?|goals?|objectives?)\b|\bable to\b', re.I)
MISSION = re.compile(r'\b(our|its|the)\s+(core\s+)?(mission|vision|values?|purpose|goals?)\b|\b(we|the (department|center|centre|school|program|institute|college)( of [\w &]+)?) (is|are) (committed|dedicated|devoted) to\b|\bseeks? to (advance|promote|foster|build|create|deepen|expand)\b|\b(mission statement|vision statement|guiding principles|we (are )?(committed|dedicated|devoted) to|we believe|we value|strive to|aspires? to|in pursuit of|we champion|we affirm|diversity, equity|inclusive excellence|social justice|equity and inclusion)\b', re.I)
RESEARCH = re.compile(r'\b(research (interests?|areas?|fields?|agenda|projects?|specialt(y|ies)|focus|profile)|areas? of (study|specialization|research)|fields? of (study|inquiry)|scholars? (working|who work)|interdisciplinar|methodolog|disciplin(e|ary)|philolog|theoretical|critical (theory|race|analysis)|interrogate|analy[sz]e|theoriz|area studies)\b', re.I)
RESOURCE = re.compile(r'\b(scholarships?|fellowships?|financial aid|stipend|tuition|grants?|funding (for|package|opportunit)|library|librar(y|ies)|collections?|archives?|holdings|resources?|facilities|labs?|laborator(y|ies)|support services|advising|mentor(ship)?|faculty|professors?|ratio)\b', re.I)
PRESTIGE = re.compile(r'\b(awards?|prizes?|honors?|rank(ed|ing|s)?|top[- ]\d+|nobel|pulitzer|macarthur|guggenheim|laureate|distinction|excellence|prestigious|renowned|leading|publications?|published|monographs?|alumni|graduates? (have|go|pursue)|careers?|placement|employment)\b', re.I)
NETWORK = re.compile(r'\b(partner(ship)?s?|collaborat(e|ion|ions|ing|ive) with|consorti(um|a)|exchange (program|student|partner)|study abroad|semester abroad|summer abroad|global internship|internships? (at|with|in)|community (engagement|partnership|outreach|service)|outreach (to|program)|public humanities|k-12|joint (program|degree)|2\+2|3\+1|memorandum of understanding)\b', re.I)
WELCOME = re.compile(r'\b(welcome (to|from|you)|we (warmly )?welcome|we invite|invite you|join us|explore our|visit (us|our)|prospective students?|we look forward|apply now|request information)\b', re.I)
DONATE = re.compile(r'\b(donat(e|ion|ions|ed)|provided significant support|major (gift|donation)|\$\d+(\.\d+)? ?(million|billion)|make a gift|\$\d+(\.\d+)? ?(million|billion)? ?(gift|grant|donation)|give (today|now|online)|your gift|gifts? (to|support|fund|from)|philanthrop|generous (support|gift|donation)|thank you|endowed (fund|chair|by))\b', re.I)
EVENT = re.compile(r'\b(events?|lectures?|talks?|workshops?|symposi(um|a)|conferences?|colloqui(um|a)|seminar series|calendar|announcements?|news|rsvp|register|deadline|due (date|by)|keynote|will (speak|present|give a talk))\b', re.I)
EFFECT = re.compile(r'\b(other|additional) activities include|activities include|recent (activities|events|news)|past (events|lectures)|upcoming|register (now|here)|sign up\b', re.I)
RULE = re.compile(r'\b(must (be|have|complete|submit)|eligib(le|ility)|deadline|requirements? for (admission|the degree)|visa|i-20|toefl|ielts|transcripts?|application (fee|materials?|requirements?|deadline)|credits? required)\b', re.I)
FOUND = re.compile(r'\b(founded|was established|were established|founding|chartered|inaugurated|created in \d{4}|organized in \d{4}|opened in \d{4}|began in \d{4})\b', re.I)
PASSIVE_CREATE = re.compile(r'\b(in \d{4},?\s.{0,70}?\b(was|were)\s+(formed|created|established|founded|set up|launched|opened|founded|renamed))\b', re.I)
HISTORY = re.compile(r'\b(history|historical|heritage|legacy|tradition|predecessor|originally|formerly|renamed|merged|the late|in memoriam|memorial|tribute|commemorat|descended|born in|died in)\b', re.I)
IDENTITY = re.compile(r'\b(consists? of|comprises?|is composed of|is made up of|is divided into|is home to|is housed|is part of the|umbrella organization|comprised of|department of|center for|institute for|school of)\b', re.I)

def person_card(s):
    """人物卡/名录行：姓名 + 职称/职务（可能含邮箱）。"""
    if s.count('\n') >= 1:
        first = s.split('\n')[0].strip()
        if PERSON.match(first + ' ') or ROLE_NAME.match(first):
            return True
    if PERSON.match(s + ' ') and not re.search(r'[.!?]\s', s[:120]):
        if re.search(r"\b(Professor|Lecturer|Fellow|Director|Coordinator|Chair|Dean|Manager|Administrator|Instructor|Associate|Assistant|Advisor|Officer|Specialist|Analyst|Librarian|Registrar)\b", s):
            return True
    if ROLE_NAME.match(s):
        return True
    if ALUM_MARK.search(s) and re.match(r'^[A-Z][\w\'’\-]+ [A-Z]', s):
        return True
    if re.match(r'^[A-Z][\w\'’\-]+(?:\s+[A-Z][\w\'’\-]+)+\s*\([^)]{3,30}\),\s', s):
        return True
    return False

def classify(t):
    """返回 (label, confidence 0-2, reason)。confidence: 2=高, 1=中, 0=低（需人工复核）。"""
    s = t.strip()
    if is_noise(s):
        return 'OTHER', 2, 'noise/heading'

    # 1) 联系入口（邮箱/电话/地址/交通指引）→ M10
    if EMAIL.search(s) or (PHONE.search(s) and len(words(s)) < 40) or DIRECT.search(s):
        return 'M10', 2, 'contact'
    if ADDRESS.search(s) and len(words(s)) <= 20:
        return 'M10', 2, 'address'
    # 2) 募捐 / 欢迎邀请 → M09
    if DONATE.search(s):
        return 'M09', 2, 'donate'
    if WELCOME.search(s) and not RULE.search(s):
        return 'M09', 2, 'welcome'
    # 3) 时间线条目 / 纪年创制 → M02
    if TIMELINE.match(s) or PASSIVE_CREATE.search(s):
        return 'M02', 2, 'timeline'
    # 4) 人物卡/名录（无联系方式）→ M01
    if person_card(s) and not EVENT.search(s[:80]):
        return 'M01', 2, 'person-card'
    # 4b) 治理/人事规程 → M01（学院治理）/ M10（办事规程）
    if GOVERN.search(s):
        if re.search(r'\b(renewed|appointment|reappointment)\b', s, re.I):
            return 'M10', 1, 'appointment'
        return 'M01', 1, 'governance'
    # 4c) 活动动态清单 → M10
    if EFFECT.search(s):
        return 'M10', 1, 'effect-list'
    # 4d) 链接串 / 期刊条目标题 → OTHER
    if LINKRUN.search(s) and not has_verb(s):
        return 'OTHER', 1, 'link-run'
    if JOURNAL_ITEM.match(s):
        return 'OTHER', 1, 'journal-item'
    # 5) 学习成效 / 培养要求 → M05
    if NUMBERED_OUTCOME.match(s):
        return 'M05', 2, 'numbered-outcome'
    if OUTCOME.search(s):
        return 'M05', 2, 'learning-outcome'
    # 5b) 战略规划式祈使条目 → M03
    if STRATEGY.match(s):
        return 'M03', 1, 'strategy'
    # 6) 使命价值 → M03（须含使命/价值语汇，且非纯学位罗列）
    if PROUD.search(s):
        return 'M03', 1, 'proud'
    if re.match(r'^We (support|believe|value|strive|hold|see|understand|view)\b', s):
        return 'M03', 1, 'values'
    if MISSION.search(s) and not re.search(r'\b(program|degree|major|minor|course|curriculum|credits?)\b', s[:70], re.I):
        return 'M03', 1, 'mission'
    # 6b) 奖助学金/资助机会 → M06
    if FUNDING.search(s):
        return 'M06', 2, 'funding'
    # 6c) 合作网络（须有伙伴机构语境）→ M08
    if NETWORK.search(s) and re.search(r'\b(partner|universities|university|institution|college|school|consortium|institute|center|centre|museums?|organizations?|agencies|community|schools|government|firms?|companies)\b', s, re.I):
        return 'M08', 2, 'network'
    # 6d) 办学成效指标 → M07
    if OUTCOMES2.search(s) or CELEBRATE.search(s):
        return 'M07', 2, 'outcomes'
    # 7) 硬性规程/申请/活动公告 → M10
    if RULE.search(s) and not DEGREE.search(s):
        return 'M10', 1, 'rule'
    # 7b) 人物生平叙述（含时间/经历）→ M02（学脉/纪念）
    if BIOHIST.search(s) and re.search(r'\b(1[89]\d\d|20\d\d)\b|\b(at|in) [A-Z][a-z]+\b', s):
        return 'M02', 1, 'bio-history'
    # 8) 校史叙述 → M02
    if (FOUND.search(s) or HISTORY.search(s)) and not OUTCOME.search(s):
        if FOUND.search(s) or re.search(r'\b(in) (18|19|20)\d\d\b', s) or re.search(r'\b(predecessor|originally|formerly|renamed|merged|the late|in memoriam|memorial|tribute|commemorat|descend)\b', s, re.I):
            return 'M02', 2, 'history'
    # 9) 学位项目/课程 → M05
    if DEGREE.search(s):
        # 若同时是研究取向列表则归 M04
        if RESEARCH.search(s) and not re.search(r'\b(program|degree|major|minor|course|curriculum|requirement|credit)\b', s, re.I):
            return 'M04', 1, 'research-vs-degree'
        return 'M05', 1, 'degree'
    # 10) 学术研究取向 → M04
    if RESEARCH.search(s):
        return 'M04', 1, 'research'
    # 11) 合作交流 → M08
    if NETWORK.search(s):
        return 'M08', 1, 'network'
    # 12) 活动通告 / 动态 → M10
    if EFFECT.search(s) or EVENT.search(s):
        return 'M10', 1, 'event'
    # 13) 支撑条件 → M06
    if RESOURCE.search(s):
        return 'M06', 1, 'resource'
    # 14) 声誉实绩 → M07
    if PRESTIGE.search(s):
        return 'M07', 1, 'prestige'
    # 15) 机构身份 → M01
    if IDENTITY.search(s):
        return 'M01', 1, 'identity'
    # 兜底
    return 'M04', 0, 'fallback'
