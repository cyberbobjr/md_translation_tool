import re

regex = r"\s{1,}(?P<country>.*)_[fascism|democratic|neutrality|communism|nationalist].*"
exclude = "autonomy"
countries = set()
prefix = 'FRLOC'
adjectives = ['INHAB', 'ADJ_MS', 'ADJ_FS', 'ADJ_MP', 'ADJ_FP']
template = """
    text = {
            trigger = { has_cosmetic_tag = %%COUNTRY%% }
            localization_key = %%ADJ%%
        }
"""
content = open("common/MD_countries_cosmetic_l_french.yml")
for line in content.readlines():
    matches = re.finditer(regex, line, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        country = match.group("country")
        if exclude.lower() not in country.lower() and country not in countries and "#" not in country:
            countries.add(country)

print(countries)
for adj in adjectives:
    output = open(f"{adj}.txt", "w+")
    for country in countries:
        build = f"{prefix}_{country}_{adj}"
        print(template.replace("%%COUNTRY%%", country).replace("%%ADJ%%", build), file=output)
