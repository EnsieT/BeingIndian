"""
Deep grammar analysis: For every category, substitute EVERY response into EVERY 
scenario and check if the result makes grammatical sense.

Key insight: Scenarios have different "slot types" based on what comes before _____:
  - "The tea is: _____" → expects a NOUN/ADJECTIVE (something that IS something)
  - "I'm literally: _____" → expects IDENTITY (adjective/noun/gerund)
  - "Caught myself simping over: _____" → expects OBJECT (noun/gerund)
  - "The cope is real when I: _____" → expects VERB PHRASE (I do something)
  - "It's giving _____ energy" → expects ADJECTIVE/NOUN modifier

We classify each scenario blank into what grammatical form it needs,
and each response into its grammatical form, then check compatibility.
"""
import json, re

with open('data/cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ── Scenario slot classification ──
def classify_scenario_slot(s):
    """What grammatical form does the blank expect?"""
    sl = s.lower().strip()
    
    # First, normalize multi-blank → single blank (same as JS)
    blanks = sl.count('_____')
    if blanks > 1:
        first = sl.index('_____')
        last = sl.rindex('_____')
        head = sl[:first + 5]
        tail = sl[last + 5:]
        sl = re.sub(r'\s+', ' ', head + tail).strip()
        if sl.count('_____') != 1:
            return 'SKIP', sl
    if '_____' not in sl:
        return 'SKIP', sl
    
    # What's before and after the blank?
    before = sl[:sl.index('_____')].strip()
    after = sl[sl.index('_____') + 5:].strip()
    
    # ── Pattern: "X is: _____" or "The tea is: _____" → IS_PREDICATE
    # Expects: noun phrase, adjective, gerund — something that can follow "is"
    if re.search(r'\bis[:\s]*$', before):
        return 'IS_PREDICATE', sl
    
    # ── Pattern: "I'm _____" / "I'm literally: _____" → IDENTITY  
    # Expects: adjective, noun phrase, gerund
    if re.search(r"(i'?m|i am)\s*(literally\s*)?[:\s]*$", before):
        return 'IDENTITY', sl
    
    # ── Pattern: "caught me/myself doing _____" → GERUND_OBJECT
    if re.search(r'caught\b', before):
        return 'GERUND_OBJECT', sl
    
    # ── Pattern: "It's giving _____ energy" → ADJECTIVE_MODIFIER
    if 'giving' in before and 'energy' in after:
        return 'ADJECTIVE_MODIFIER', sl
    
    # ── Pattern: "when I: _____" / "when I _____" → I_VERB
    # Expects: verb phrase (I do something)
    if re.search(r'when i[:\s]*$', before):
        return 'I_VERB', sl
    
    # ── Pattern: "saw me do: _____" → VERB_INF
    if re.search(r'(saw me|saw me do)[:\s]*$', before):
        return 'VERB_INF', sl
    
    # ── Pattern: "I respect people who: _____" → WHO_CLAUSE
    if re.search(r'who[:\s]*$', before):
        return 'WHO_CLAUSE', sl
    
    # ── Pattern: "would be if someone: _____" → SOMEONE_VERB
    if re.search(r'someone[:\s]*$', before):
        return 'SOMEONE_VERB', sl
    
    # ── Pattern: "stopping me from: _____" → FROM_GERUND  
    if re.search(r'from[:\s]*$', before):
        return 'FROM_GERUND', sl
    
    # ── Pattern: "is full of: _____" / "addicted to: _____" / "over: _____" → OBJECT
    if re.search(r'(of|to|over|about|for|at|from|into|with|doing)[:\s]*$', before):
        return 'OBJECT', sl
    
    # ── Pattern with question mark → ANSWER
    if sl.endswith('?'):
        return 'ANSWER', sl
    
    # ── Pattern: label/title before colon "My X: _____" → NOUN_LABEL
    # Most generic - expects noun phrase, gerund, or adjective
    if re.search(r'[:\s]*$', before) and ':' in before:
        return 'NOUN_LABEL', sl
    
    # ── Pattern: "I'm hiding _____" etc → OPEN
    return 'OPEN', sl

# ── Response classification ──
def classify_response(r):
    rl = r.lower().strip().rstrip('.')
    
    if rl.startswith('trump:'):
        return 'TRUMP'
    
    # Gerund phrases (starting with -ing verb)
    gerund_starts = r'^(getting|being|having|doing|making|thinking|watching|texting|saying|working|living|pretending|writing|napping|sleeping|avoiding|fighting|tweeting|oversharing|committing|touching|running|loving|rotting|eating|drinking|slapping|using|asking|calling|putting|bargaining|planning|paying|surviving|dodging|collecting|mastering|stealing|buying|raising|comparing|considering|wishing|realizing|looking|remembering|becoming|finding|existing|knowing|revolting|waking|recovering|setting|complaining|shopping|saving|turning|worrying|budgeting|romanticizing|resenting|hiding|forgetting|canceling|going|checking|groaning|falling|missing|dealing|hearing|wanting|making|needing|aching|seeing)'
    if re.match(gerund_starts, rl):
        return 'GERUND'
    
    # Noun phrases (start with article/determiner/possessive)
    if re.match(r'^(a |an |the |my |your |our |that |this |some |one |no |every)', rl):
        return 'NOUN_PHRASE'
    
    # Adjective/state phrases
    adj_starts = r'^(chronically|absolutely|literally|genuinely|mentally|emotionally|professionally|seriously|honestly|completely|desperately|secretly|actively|currently|already|still|actually|basically|essentially|fake|down|weird|aesthetic|main|parasocially|two-faced|rent-free|maidenless|broke)'
    if re.match(adj_starts, rl):
        return 'ADJECTIVE'
    
    # Standalone nouns/phrases (no article but clearly a thing)
    # These are nouns that work as "X is: [this]"
    noun_indicators = [
        'people', 'stuff', 'things', 'positions', 'situations', 'regrets', 
        'fantasies', 'substances', 'comfort', 'potential', 'betrayal',
        'beautiful', 'absolute', 'nothing', 'time', 'nobody'
    ]
    for ni in noun_indicators:
        if rl.startswith(ni):
            return 'NOUN_PHRASE'
    
    # Prepositional phrases ("at the gym", "in the closet", "on Reddit")
    if re.match(r'^(at |in |on |just |only |way )', rl):
        return 'PREP_PHRASE'
    
    # Short phrases that act as labels/nouns
    if len(rl.split()) <= 4 and not re.match(r"^(i |can't|won't|didn't)", rl):
        return 'SHORT_LABEL'
    
    # Sentence fragments starting with verbs
    if re.match(r"^(can't|won't|didn't|i )", rl):
        return 'SENTENCE_FRAG'
    
    return 'SHORT_LABEL'

# ── Compatibility matrix ──
# For each scenario slot type, which response types are grammatically OK?
COMPAT = {
    'IS_PREDICATE': {
        # "The tea is: [X]" — what CAN follow "is"?
        'GERUND': True,        # "The tea is: getting drunk" ✓
        'NOUN_PHRASE': True,   # "The tea is: a complete mess" ✓
        'ADJECTIVE': True,     # "The tea is: chronically online" ✓
        'SHORT_LABEL': True,   # "The tea is: sober" ✓ 
        'PREP_PHRASE': True,   # "The tea is: at the gym" ✓
        'SENTENCE_FRAG': False,# "The tea is: can't even adult" ✗
        'TRUMP': True,
    },
    'IDENTITY': {
        # "I'm literally: [X]" — same as IS_PREDICATE
        'GERUND': True, 'NOUN_PHRASE': True, 'ADJECTIVE': True,
        'SHORT_LABEL': True, 'PREP_PHRASE': True,
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'GERUND_OBJECT': {
        # "Caught myself simping over: [X]"
        'GERUND': False,       # "Caught simping over: getting drunk" — questionable
        'NOUN_PHRASE': True,   # "Caught simping over: a dead meme" ✓
        'ADJECTIVE': False,    # "Caught simping over: chronically online" ✗
        'SHORT_LABEL': True,   # "Caught simping over: sober" — OK ish
        'PREP_PHRASE': False,  # "Caught simping over: at the gym" ✗
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'ADJECTIVE_MODIFIER': {
        # "It's giving _____ energy" — needs adjective/noun modifier
        'GERUND': False,       # "It's giving getting drunk energy" ✗
        'NOUN_PHRASE': False,  # "It's giving a complete mess energy" ✗  
        'ADJECTIVE': True,     # "It's giving chronically online energy" ✓
        'SHORT_LABEL': True,   # "It's giving sober energy" ✓
        'PREP_PHRASE': False,  # "It's giving at the gym energy" ✗
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'I_VERB': {
        # "The cope is real when I: [X]"
        'GERUND': False,       # "when I: getting drunk" ✗
        'NOUN_PHRASE': False,  # "when I: a complete mess" ✗
        'ADJECTIVE': False,    # "when I: chronically online" ✗
        'SHORT_LABEL': False,  # most don't work
        'PREP_PHRASE': False,
        'SENTENCE_FRAG': True, # "when I: can't even adult" ✓ (needs verb)
        'TRUMP': True,
    },
    'VERB_INF': {
        # "Twitter saw me do: [X]" → needs noun/gerund
        'GERUND': False, 'NOUN_PHRASE': True, 'ADJECTIVE': False,
        'SHORT_LABEL': True, 'PREP_PHRASE': False,
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'WHO_CLAUSE': {
        # "I respect people who: [X]" → needs "who [verb]" compatible
        'GERUND': False, 'NOUN_PHRASE': False, 'ADJECTIVE': False,
        'SHORT_LABEL': False, 'PREP_PHRASE': False,
        'SENTENCE_FRAG': True, 'TRUMP': True,
    },
    'SOMEONE_VERB': {
        # "if someone: [X]" → needs verb phrase
        'GERUND': False, 'NOUN_PHRASE': False, 'ADJECTIVE': False,
        'SHORT_LABEL': False, 'PREP_PHRASE': False,
        'SENTENCE_FRAG': True, 'TRUMP': True,
    },
    'FROM_GERUND': {
        # "stopping me from: [X]" → needs gerund
        'GERUND': True, 'NOUN_PHRASE': True, 'ADJECTIVE': False,
        'SHORT_LABEL': True, 'PREP_PHRASE': False,
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'OBJECT': {
        # "addicted to: [X]", "full of: [X]", "judge me for: [X]"
        'GERUND': True, 'NOUN_PHRASE': True, 'ADJECTIVE': False,
        'SHORT_LABEL': True, 'PREP_PHRASE': False,
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'NOUN_LABEL': {
        # "My guilty pleasure: [X]" — very flexible
        'GERUND': True, 'NOUN_PHRASE': True, 'ADJECTIVE': True,
        'SHORT_LABEL': True, 'PREP_PHRASE': True,
        'SENTENCE_FRAG': False, 'TRUMP': True,
    },
    'ANSWER': {
        # Question format — almost anything works
        'GERUND': True, 'NOUN_PHRASE': True, 'ADJECTIVE': True,
        'SHORT_LABEL': True, 'PREP_PHRASE': True,
        'SENTENCE_FRAG': True, 'TRUMP': True,
    },
    'OPEN': {
        'GERUND': True, 'NOUN_PHRASE': True, 'ADJECTIVE': True,
        'SHORT_LABEL': True, 'PREP_PHRASE': True,
        'SENTENCE_FRAG': True, 'TRUMP': True,
    },
}

print("=" * 100)
print("DEEP GRAMMAR ANALYSIS — Every Scenario × Every Response")
print("=" * 100)

grand_total = 0
grand_bad = 0
all_bad_examples = []

for cat_key, cat_data in data.items():
    scenarios = cat_data['scenarios']
    responses = cat_data['responses']
    
    total = 0
    bad = 0
    cat_bad = []
    
    # Classify all responses once
    resp_types = [(r, classify_response(r)) for r in responses]
    
    for s_raw in scenarios:
        s = s_raw
        blanks = s.count('_____')
        if blanks > 1:
            first = s.index('_____')
            last = s.rindex('_____')
            head = s[:first + 5]
            tail = s[last + 5:]
            s = re.sub(r'\s+', ' ', head + tail).strip()
            if s.count('_____') != 1:
                continue
        if '_____' not in s:
            continue
        
        slot_type, _ = classify_scenario_slot(s)
        if slot_type == 'SKIP':
            continue
        
        compat = COMPAT.get(slot_type, COMPAT['OPEN'])
        
        for r, r_type in resp_types:
            if r_type == 'TRUMP':
                total += 1
                continue
            
            total += 1
            is_ok = compat.get(r_type, True)
            
            if not is_ok:
                bad += 1
                filled = s.replace('_____', r)
                cat_bad.append({
                    'scenario': s_raw,
                    'response': r,
                    'filled': filled,
                    'slot_type': slot_type,
                    'resp_type': r_type,
                })
    
    pct_bad = (bad / total * 100) if total > 0 else 0
    pct_ok = 100 - pct_bad
    grand_total += total
    grand_bad += bad
    all_bad_examples.extend(cat_bad)
    
    print(f"\n{'─' * 100}")
    print(f"  Category: {cat_data['name']}")
    print(f"  Total combos: {total} | OK: {total-bad} ({pct_ok:.1f}%) | BAD: {bad} ({pct_bad:.1f}%)")
    
    # Show slot type breakdown
    slot_issues = {}
    for b in cat_bad:
        key = f"{b['slot_type']} + {b['resp_type']}"
        slot_issues.setdefault(key, []).append(b)
    
    if slot_issues:
        print(f"  Issue breakdown:")
        for key, items in sorted(slot_issues.items(), key=lambda x: -len(x[1])):
            print(f"    {key}: {len(items)} bad combos")
            print(f"      e.g. \"{items[0]['filled'][:90]}\"")

    # Count how many scenarios have the problematic slot types
    problem_scenarios = set()
    for b in cat_bad:
        problem_scenarios.add(b['scenario'])
    if problem_scenarios:
        print(f"  Scenarios causing most issues ({len(problem_scenarios)}):")
        for ps in list(problem_scenarios)[:5]:
            count = sum(1 for b in cat_bad if b['scenario'] == ps)
            print(f"    \"{ps[:70]}\" → {count} bad responses")

print(f"\n{'=' * 100}")
print(f"OVERALL: {grand_total} combos tested | {grand_total-grand_bad} OK ({(grand_total-grand_bad)/grand_total*100:.1f}%) | {grand_bad} BAD ({grand_bad/grand_total*100:.1f}%)")
print(f"{'=' * 100}")

# Analyze what response type distribution looks like per category
print(f"\n{'=' * 100}")
print("RESPONSE TYPE DISTRIBUTION PER CATEGORY")
print(f"{'=' * 100}")
for cat_key, cat_data in data.items():
    resp_types = {}
    for r in cat_data['responses']:
        rt = classify_response(r)
        resp_types[rt] = resp_types.get(rt, 0) + 1
    total_r = len(cat_data['responses'])
    print(f"\n  {cat_data['name']}:")
    for rt, ct in sorted(resp_types.items(), key=lambda x: -x[1]):
        print(f"    {rt}: {ct} ({ct/total_r*100:.0f}%)")

# Analyze what scenario slot types exist per category
print(f"\n{'=' * 100}")
print("SCENARIO SLOT TYPE DISTRIBUTION PER CATEGORY")
print(f"{'=' * 100}")
for cat_key, cat_data in data.items():
    slot_types = {}
    for s in cat_data['scenarios']:
        st, _ = classify_scenario_slot(s)
        slot_types[st] = slot_types.get(st, 0) + 1
    total_s = len(cat_data['scenarios'])
    print(f"\n  {cat_data['name']}:")
    for st, ct in sorted(slot_types.items(), key=lambda x: -x[1]):
        pct = ct/total_s*100
        compat = COMPAT.get(st, {})
        ok_types = [k for k,v in compat.items() if v and k != 'TRUMP']
        print(f"    {st}: {ct} ({pct:.0f}%) — accepts: {', '.join(ok_types)}")

print(f"\n{'=' * 100}")
print("RECOMMENDED FIX: SPLIT RESPONSES INTO TWO POOLS")
print(f"{'=' * 100}")
print("""
The root problem: scenarios have DIFFERENT grammatical slot types but all share 
ONE pool of responses. Some responses (gerunds, nouns) work in most slots, but
others (sentence fragments, adjectives) only work in specific slots.

SOLUTION: Split responses into two pools per category:
  Pool A ("noun_responses"): GERUND + NOUN_PHRASE + SHORT_LABEL + PREP_PHRASE
    → Works with: IS_PREDICATE, IDENTITY, OBJECT, NOUN_LABEL, FROM_GERUND, ANSWER
    → These are ~80% of scenarios
    
  Pool B ("verb_responses"): SENTENCE_FRAG + specific verb forms  
    → Works with: I_VERB, WHO_CLAUSE, SOMEONE_VERB
    → These are ~5-10% of scenarios

  Pool C ("modifier_responses"): ADJECTIVE + SHORT_LABEL
    → Works with: ADJECTIVE_MODIFIER
    → Very few scenarios use this

For most categories, converting ALL responses to Pool A form (gerunds/nouns)
would eliminate nearly all issues since very few scenarios need verb forms.

For categories WITH verb-slot scenarios (like GenZ "when I: _____"), we should
either rewrite those scenarios to use noun-slots, or maintain a small verb pool.
""")

# Print specific GenZ analysis
print(f"\n{'=' * 100}")
print("DETAILED GENZ ANALYSIS")
print(f"{'=' * 100}")
genz = data['genz']
for s in genz['scenarios']:
    st, normalized = classify_scenario_slot(s)
    compat = COMPAT.get(st, COMPAT['OPEN'])
    ok_count = 0
    bad_count = 0
    bad_responses = []
    for r in genz['responses']:
        rt = classify_response(r)
        if rt == 'TRUMP':
            ok_count += 1
            continue
        if compat.get(rt, True):
            ok_count += 1
        else:
            bad_count += 1
            bad_responses.append(f"  \"{r}\" [{rt}]")
    total = ok_count + bad_count
    pct_ok = ok_count/total*100 if total else 0
    print(f"\n  \"{s}\" [{st}]")
    print(f"    OK: {ok_count}/{total} ({pct_ok:.0f}%) | BAD: {bad_count}")
    if bad_responses:
        for br in bad_responses[:3]:
            print(f"      ✗ {br}")
