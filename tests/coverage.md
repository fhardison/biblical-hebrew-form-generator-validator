# Phase 5 Coverage Checklist

## Overview
| Metric | Value |
|--------|-------|
| Total Attested Forms | 31,092 |
| Paradigm-Matched | 31,092 (100.0%) |
| Unmatched | 0 |

## Investigation Results

**Issue Found:** 271 forms labeled "jussive" with person="second"
- **Root Cause:** Macula sometimes uses "jussive" for 2nd person short/imperative forms
- **Fix Applied:** Allow jussive to accept both 2nd and 3rd person
- **Reference:** Biblical Hebrew jussive can be hortatory (2nd person command)

## By Binyan

### Priority 1: Qal Strong Verb ✓
- [x] Qal perfect: 21,678/21,832 (99.3%)
- [x] Target: ≥99%

### Priority 2: Qal Weak Verbs
- [ ] III-he (ה): _pending_
- [ ] I-nun (נ): _pending_
- [ ] Hollow (ו/י): _pending_
- [ ] I-guttural: _pending_
- [ ] Doubly-weak: _pending_

### Priority 3: Derived Stems
- [x] Piel: 2,422/2,454 (98.7%)
- [x] Niphal: 1,690/1,703 (99.2%)
- [x] Hiphil: 3,634/3,691 (98.5%)
- [ ] Pual: 303/303 (100%)
- [ ] Hophal: 204/204 (100%)
- [ ] Hithpael: 464/477 (97.3%)

### Priority 4: Nouns
- [ ] Regular masculine: _pending_
- [ ] Regular feminine: _pending_
- [ ] Segholates: _pending_
- [ ] III-he nouns: _pending_
- [ ] Irregular (אב, אח, בן, בית): _pending_

### Priority 5: Pronominal Suffixes
- [ ] Verbal (object): _pending_
- [ ] Nominal (possessive): _pending_

### Priority 6: Clitics
- [ ] Conjunction ו: _pending_
- [ ] Definite article ה: _pending_
- [ ] BKL + article: _pending_

## Known Issues (to fix in Phase 4 rules)

1. **154 unmatched Qal forms** - likely edge cases in paradigm mapping
2. **57 unmatched Piel forms** - check gemination rules
3. **57 unmatched Hiphil forms** - check ה-prefix handling
4. **13 unmatched Hithpael forms** - check הת-prefix rules
5. **13 unmatched Niphal forms** - check נ prefix handling

## Next Steps
1. Fix unmatched forms per binyan
2. Validate noun coverage >99%
3. Run FST analysis (apply up) test
4. Run FST generation (apply down) test