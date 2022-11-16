## Millenium Dawn Automator Translation tool

### Beware

This tool is a helphing tool, you ***should always*** check the output translated, particulary the special annotation
from Paradox :

- §Cblablba§
- £icon_name
- [item_value]

etc.

__Some limitations__ :
in the yaml source file, you can not have more than 1 level when you want to check translation :

eg. this file will be checked correctly :
```
l_french:
 ARM_Kocharjan: "§YThe era of Kocharyan§!"
```

But this file __not__ :
```
l_french:
 ARM_Kocharjan: "§YThe era of Kocharyan§!"
 another_level: # NO
   ARM_test : "arm_test"
```

### Pre-requisities

You must have an API key from DeepL before using this tool

You also need Python 3

### Installation

```
pip install -r requirements.txt
```

### Configuration

You __must__ customize the tool by settings some mandatory options in the config file ```conf.json```

Explanation :

```
{
  "source_path": "source", # The source directory where original text are
  "dest_path": "dest", # The translated files will be put here
  "dict_filename": "dict.json", # The dictionnary file which will be construct & used for the translation
  "deepl": {
    "key": "xxxxx", # Your DeepL API KEY
    "lang": "FR" # The target language for translation
  }
}
```

All source file must be conform to yml definition.

The ``dict_filename`` is used to store translations already done. This saves requests to DeepL.

### Running

Simply launch the tool with Python :

```
python3 main.py
```

And it's done.

If you want to add a validation step after the translation, you can launch the script with the check option :

```
python3 main.py --check
```

In this case, after all translation a validation process will be show.
