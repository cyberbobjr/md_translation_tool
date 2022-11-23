import re

"""
This script is used for generating ADJ for French translation :
- it parse the ymf countries names in common/MD_countries_cosmetic_l_french.yml
- it create a file for each adj (feminin pluriel, feminin singulier,etc ...) with the template defined in the code
- all data must be in /common folder
"""

regex = r"\s{1,}(?P<country>.*)_[fascism|democratic|neutrality|communism|nationalist]_?.*?\:\s\"(?P<trad>.*)\""
exclude = "autonomy"
countries = {}
prefix = 'FRLOC'
adjectives = ['ADJ_MS', 'ADJ_FS', 'ADJ_MP', 'ADJ_FP','INHAB']
template = """
    text = {
            trigger = { has_cosmetic_tag = %%COUNTRY%% }
            localization_key = %%ADJ%%
        }
"""
keyfilename = "0_FR_loc_l_french_tomerge.yml"

content = open("common/MD_countries_cosmetic_l_french.yml")
for line in content.readlines():
    matches = re.finditer(regex, line, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        country = match.group("country")
        trad = match.group("trad")
        if exclude.lower() not in country.lower() and country not in countries and "#" not in country:
            countries[country] = trad

for adj in adjectives:
    output = open(f"common/{adj}.txt", "w+")
    for key in countries:
        build = f"{prefix}_{key}_{adj}"
        print(template.replace("%%COUNTRY%%", key).replace("%%ADJ%%", build), file=output)

keyoutput = open(f"{keyfilename}", "w+")
for key in countries:
    for adj in adjectives:
        build = f"{prefix}_{key}_{adj}"
        print(f" {build} : \"{countries[key]}\"", file=keyoutput)
    print(f"\r", file=keyoutput)
