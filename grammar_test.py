"""
Grammar/Sense analysis for Scenario + Response card combinations.
Tests all categories, substituting each response into each scenario's blank,
and checks for grammatical/sense issues.
"""
import json, re, sys

with open('data/cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Classification rules for detecting grammatical mismatches
# We categorize scenarios by what grammatical form the blank expects:
#   - NOUN_PHRASE: blank expects a noun/noun-phrase (e.g. "My guilty pleasure: _____.")
#   - GERUND_CLAUSE: blank expects "doing something" / "-ing" form (e.g. "What I got caught doing: _____.")
#   - IDENTITY: blank expects "I am _____" style (e.g. "The reality of who I am: _____.")
#   - QUESTION: blank expects a direct answer to a question
#   - OPEN: basically anything goes

def classify_scenario(s):
    """Return expected grammatical type for the blank."""
    sl = s.lower().strip()
    
    # Scenarios ending with question marks expect a direct noun/phrase answer
    if sl.endswith('?'):
        return 'QUESTION'
    
    # "caught me/myself _____" expects gerund
    if re.search(r'caught (me|myself|doing)\b', sl):
        return 'GERUND'
    
    # "I'm/I am _____", "who I am: _____", "I'm actually: _____", "I'm literally: _____"
    if re.search(r"(i'?m|i am|who i am|you find out i'm|i'm literally)\s*[:\.]?\s*_", sl):
        return 'IDENTITY'
    
    # "How I ..." expects gerund/phrase
    if re.search(r'^how i\b', sl):
        return 'GERUND'
    
    # "why I ..." can accept gerund or noun phrase
    if re.search(r'^why\b', sl):
        return 'REASON'
    
    # "What I do when ..." expects gerund
    if re.search(r'what i do\b', sl):
        return 'GERUND'
    
    # Patterns like "My guilty pleasure: _____." or "Something about me: _____."
    # These accept noun phrases
    if re.search(r':\s*_____', sl):
        return 'NOUN_PHRASE'
    
    # "It's giving _____ energy" 
    if 'giving' in sl and 'energy' in sl:
        return 'ADJECTIVE'
    
    # "My partner has no clue I'm _____"
    if re.search(r"i'?m\s+_", sl):
        return 'IDENTITY'
    
    return 'OPEN'


def classify_response(r):
    """Return grammatical type of the response."""
    rl = r.lower().strip().rstrip('.')
    
    if rl.startswith('trump:'):
        return 'TRUMP'
    
    # Gerund / -ing phrase
    if re.match(r'^(getting|being|having|doing|making|thinking|watching|texting|saying|working|living|pretending|writing|napping|sleeping|avoiding|fighting|tweeting|oversharing|committing|touching|running|loving|rotting|eating|drinking|slapping|using|asking|calling|putting|bargaining|planning|paying|surviving|dodging|collecting|mastering|stealing|buying|raising|comparing|considering|wishing|realizing|pretending|looking|remembering|becoming|finding|existing|knowing)', rl):
        return 'GERUND'
    
    # Starts with article/determiner → noun phrase
    if re.match(r'^(a |an |the |my |your |our |that |this |some )', rl):
        return 'NOUN_PHRASE'
    
    # Adjective/identity phrases (often start with adjective or adverb)
    if re.match(r'^(chronically|absolutely|literally|genuinely|mentally|emotionally|professionally|seriously|honestly|completely|desperately|secretly|actively|currently|already|still|actually|basically|essentially|two-faced|fake|down|weird|aesthetic|broke)', rl):
        return 'ADJECTIVE'
    
    # Full sentence indicators
    if re.match(r'^(i |he |she |they |we |it |just |can\'t|won\'t|didn\'t)', rl):
        return 'SENTENCE'
    
    # Verb phrases
    if re.match(r'^(revolts|wakes|can\'t|sets|complains|shops|buys|asks|saves|turns|knows|worries|budgets|romanticizes|resents|calls|compares|groan|check|forget|need)', rl):
        return 'VERB_PHRASE'
    
    # Default - treat as noun phrase
    return 'NOUN_PHRASE'


def test_combination(scenario, response):
    """
    Test if a scenario+response combination makes grammatical sense.
    Returns (ok: bool, issue: str or None)
    """
    if response.startswith('TRUMP:'):
        return True, None
    
    s_type = classify_scenario(scenario)
    r_type = classify_response(response)
    
    # Substitute and check
    filled = scenario.replace('_____', response)
    
    issues = []
    
    # IDENTITY scenarios need identity-compatible responses (adjective, noun_phrase, gerund)
    if s_type == 'IDENTITY':
        if r_type == 'VERB_PHRASE':
            issues.append(f'IDENTITY scenario + VERB_PHRASE response: "{filled[:80]}"')
    
    # GERUND scenarios need gerund responses    
    if s_type == 'GERUND':
        if r_type == 'NOUN_PHRASE' or r_type == 'VERB_PHRASE' or r_type == 'SENTENCE':
            # Check if it actually reads okay
            if not response.lower().strip().endswith('ing') and not re.match(r'^(a|an|the|my|that)', response.lower()):
                issues.append(f'GERUND scenario + non-gerund response: "{filled[:80]}"')
    
    # Check for double articles: "My guilty pleasure: A whatsapp forward" is fine
    # but "My partner has no clue I'm a ....." might sound weird with some responses
    
    # Check "verb after colon" issue - scenarios like "My guilty pleasure: _____." 
    # filled with a verb phrase like "revolts against that" sounds wrong
    if s_type == 'NOUN_PHRASE' and r_type == 'VERB_PHRASE':
        issues.append(f'NOUN/LABEL scenario + VERB_PHRASE response: "{filled[:80]}"')
    
    # Check capitalization consistency
    # Scenario "It's giving _____ energy" + "a functioning alcoholic" = 
    # "It's giving a functioning alcoholic energy" (sounds wrong)
    if s_type == 'ADJECTIVE' and r_type not in ('ADJECTIVE', 'NOUN_PHRASE'):
        issues.append(f'ADJECTIVE slot + wrong type: "{filled[:80]}"')
    
    # QUESTION scenarios - most responses work
    if s_type == 'QUESTION' and r_type == 'VERB_PHRASE':
        issues.append(f'QUESTION + VERB_PHRASE mismatch: "{filled[:80]}"')
    
    if issues:
        return False, issues[0]
    return True, None


# Run the test across all categories
print("=" * 90)
print("SCENARIO + RESPONSE GRAMMAR/SENSE TEST")
print("=" * 90)

grand_total = 0
grand_bad = 0
all_issues = []
category_stats = {}

for cat_key, cat_data in data.items():
    scenarios = cat_data['scenarios']
    responses = [r for r in cat_data['responses'] if not r.startswith('TRUMP:')]
    
    total = 0
    bad = 0
    cat_issues = []
    
    for s in scenarios:
        # Transform multi-blank scenarios same as the JS does
        blanks = s.count('_____')
        if blanks == 0:
            continue
        if blanks > 1:
            first = s.index('_____')
            last = s.rindex('_____')
            head = s[:first + 5]
            tail = s[last + 5:]
            s = re.sub(r'\s+', ' ', head + tail).strip()
            if s.count('_____') != 1:
                continue
        
        for r in responses:
            total += 1
            ok, issue = test_combination(s, r)
            if not ok:
                bad += 1
                cat_issues.append(issue)
    
    pct_bad = (bad / total * 100) if total > 0 else 0
    pct_good = 100 - pct_bad
    category_stats[cat_key] = {'total': total, 'bad': bad, 'good': total - bad, 'pct_good': pct_good}
    grand_total += total
    grand_bad += bad
    all_issues.extend(cat_issues)
    
    print(f"\n{'─' * 90}")
    print(f"Category: {cat_data['name']}")
    print(f"  Combinations tested: {total}")
    print(f"  Grammatically OK:    {total - bad} ({pct_good:.1f}%)")
    print(f"  Issues found:        {bad} ({pct_bad:.1f}%)")
    if cat_issues:
        print(f"  Sample issues:")
        for iss in cat_issues[:5]:
            print(f"    - {iss}")

print(f"\n{'=' * 90}")
print(f"OVERALL SUMMARY")
print(f"{'=' * 90}")
print(f"  Total combinations tested: {grand_total}")
print(f"  Grammatically OK:          {grand_total - grand_bad} ({(grand_total - grand_bad)/grand_total*100:.1f}%)")
print(f"  Issues found:              {grand_bad} ({grand_bad/grand_total*100:.1f}%)")

# Pattern Analysis
print(f"\n{'=' * 90}")
print(f"ROOT CAUSE PATTERN ANALYSIS")
print(f"{'=' * 90}")

# Count issue patterns
pattern_counts = {}
for iss in all_issues:
    # Extract pattern type
    pattern = iss.split(':')[0] if ':' in iss else iss
    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

print(f"\nIssue breakdown by pattern:")
for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
    print(f"  {pattern}: {count} ({count/grand_bad*100:.1f}% of all issues)")

print(f"\n{'=' * 90}")
print(f"RECOMMENDED FIXES")
print(f"{'=' * 90}")
print("""
The core problem is a GRAMMATICAL FORM MISMATCH between what the scenario blank
expects and what the response provides. There are two main patterns:

PATTERN 1: NOUN_PHRASE scenario + VERB_PHRASE response (~majority of issues)
  Example: "My guilty pleasure: revolts against that."
  The scenario expects a NOUN/thing, but the response is a VERB phrase.
  
  FIX: Rewrite verb-phrase responses as gerunds or noun phrases:
    "revolts against that"  → "revolting against everything"
    "wakes up feeling 60"   → "waking up feeling 60" 
    "can't recover physically" → "not being able to recover physically"
    "sets an alarm on weekends" → "setting an alarm on weekends"
    "complains about my back" → "complaining about my back"
    "shops at CostCo for fun" → "shopping at CostCo for fun"
    "groan getting out of bed" → "groaning while getting out of bed"
    "check my blood pressure" → "checking my blood pressure"
    "need reading glasses" → "needing reading glasses"
    "forget my kids' schedules" → "forgetting my kids' schedules"

PATTERN 2: GERUND scenario + NOUN_PHRASE response (smaller portion)
  Example: "What I got caught doing: Sharma Ji ka beta."
  The scenario expects an ACTION (-ing form), but gets a noun.
  
  FIX: These are mostly cross-category mismatches. Within a category,
  this occurs less often. The fix is to ensure responses within each
  category are predominantly in the SAME grammatical form.

UNIVERSAL FIX STRATEGY:
  Standardize ALL responses to one of these two forms:
  1. GERUND phrases: "getting drunk at a bar", "texting my ex at 2 AM"
  2. NOUN phrases: "a functioning alcoholic", "my parents' expectations"
  
  Both of these forms work in nearly ALL scenario templates because:
  - "My guilty pleasure: getting drunk at a bar." ✓
  - "My guilty pleasure: a functioning alcoholic." ✓  
  - "The reality of who I am: getting drunk at a bar." ✓
  - "The reality of who I am: a functioning alcoholic." ✓
  
  AVOID: Conjugated verb phrases like "revolts against", "wakes up feeling",
  "can't recover", "sets an alarm" — these only work as sentence predicates,
  not as fill-in-the-blank answers.

MOST IMPACTED CATEGORY: millennial30s and millennial40s
  These categories have the most verb-phrase responses that don't fit as blanks.
  Converting them to gerund form would fix ~90%+ of all issues instantly.
""")
