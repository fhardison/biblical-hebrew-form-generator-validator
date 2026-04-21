from scripts.hebrew_fst import HebrewFST

fst = HebrewFST()


TEST = 'לְחַיּוֹת'
ROOT = 'חָיָה'

analysis = fst.analyze(TEST)
for a in analysis:
    print(a)
print()

result = fst.validate(TEST, ROOT, "piel")
print('validating', TEST, result)
