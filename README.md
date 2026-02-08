# Quran Transcript

<div align="center">
<strong>بفضل الله وحده عز وجل نقدم الرسم الصوتي للقرآن الكريم الملم بجل قواعد التجويد وصفات الحوف</strong>

[![PyPI][pypi-badge]][pypi-url]
[![Python Versions][python-badge]][python-url]
[![Google Colab][colab-badge]][colab-url]

</div>

[pypi-badge]: https://img.shields.io/pypi/v/quran-transcript.svg
[pypi-url]: https://pypi.org/project/quran-transcript/
[python-badge]: https://img.shields.io/pypi/pyversions/quran-transcript.svg
[python-url]: https://pypi.org/project/quran-transcript/
[colab-badge]: https://img.shields.io/badge/Google%20Colab-Open%20in%20Colab-F9AB00?logo=google-colab&logoColor=white
[colab-url]: https://colab.research.google.com/drive/1d9-mVu2eiPOPS9z5sS2V4TQ579xIUBi-?usp=sharing

# `quran-transcript` package

## 🆕 ما الجديد في الإصدار 0.2.0 (What's New in Version 0.2.0)

### 📍 خرائط المواقع الجديدة (New Position Mappings)
- إضافة خرائط المواقع من الرسم العثماني إلى الرسم الصوتي (Added position mappings from Uthmani script to phonetic script)
- تتبع دقيق لتحويل كل حرف إلى موضعه الجديد (Precise tracking of character transformations)
- دعم تمثيل الأحرف المحذوفة بقيمة `None` (Support for deleted characters representation with `None`)

# 📖 Quran Transcript


## 🔧 Installation

Install the package directly from GitHub using pip:

```bash
pip install quran-transcript
```

## 🧠 Usage Examples

### 🕋 Aya Object

إنشاء كائن Aya لتمثيل آية محددة واسترجاع معلوماتها

```python
from quran_transcript import Aya

aya = Aya(1, 1)  # سورة الفاتحة، الآية 1
print(aya)

aya_info = aya.get()
print(aya_info)
```

### 🔁 Loop Through All Surahs

التنقل عبر جميع الآيات في القرآن

```python
start_aya = Aya()
for aya in start_aya.get_ayat_after():
    aya_info = aya.get()
    # Do something with the aya info
```

### 🧮 Get Number of Verses per Surah

بناء خريطة بأرقام السور وعدد آياتها

```python
sura_to_aya_count = {}
start_aya = Aya(1, 1)

for i in range(1, 115):  # 114 سورة في القرآن
    aya.set(i, 1)
    sura_to_aya_count[i] = aya.get().num_ayat_in_sura

print(sura_to_aya_count)
```

### 🔄 Convert Imlaey Script to Uthmani

تحويل الرسم الإملائي للرسم العثماني

```python
from quran_transcript import search, Aya

imlaey_text = 'فأخرج به من الثمرات رزقا لكم'
results = search(
    imlaey_text,
    start_aya=Aya(2, 13),
    window=20,
    remove_tashkeel=True
)

uthmani_script = results[0].uthmani_script
print(uthmani_script)
```

### 🔤 Convert Uthmani Script to Phonetic Script

تحويل الرسم العثماني للرسم الصوتي للقرآن

```python
from quran_transcript import Aya, search, quran_phonetizer, MoshafAttributes
import json

imlaey_text = "بسم الله الرحمن الرحيم"
results = search(
    imlaey_text,
    start_aya=Aya(1, 1),
    window=2,
    remove_tashkeel=True
)

# الحصول على الرسم العثماني
uthmani_script = results[0].uthmani_script
print(f"الرسم العثماني:\n{uthmani_script}")

# إعداد خصائص المصحف للتحويل الصوتي
moshaf = MoshafAttributes(
    rewaya="hafs",
    madd_monfasel_len=4,
    madd_mottasel_len=4,
    madd_mottasel_waqf=4,
    madd_aared_len=4,
)

# الحصول على الرسم الصوتي مع الخرائط
phonetic_script = quran_phonetizer(uthmani_script, moshaf)

print('\n' * 2)
print(f"الرسم الصوتي:\n{phonetic_script.phonemes}")

# جديد: عرض خرائط المواقع
print('\n' * 2)
print("خرائط المواقع:")
for idx, (uth_char, mapping) in enumerate(zip(uthmani_script, phonetic_script.mappings)):
    if mapping is not None:
        # استخراج الصوت لهذا الحرف
        phoneme = phonetic_script.phonemes[mapping.pos[0]:mapping.pos[1]]
        print(f"حرف: '{uth_char}' -> صوت: '{phoneme}' (موقع: {mapping.pos})")
    else:
        print(f"حرف: '{uth_char}' -> محذوف")

print('\n' * 2)
print("صفات الحروف:")
for sifa in phonetic_script.sifat:
    print(json.dumps(sifa.model_dump(), ensure_ascii=False, indent=4))
    print()
```
> 📘 For more information on `MoshafAttributes`, refer to the [Quran Dataset Documentation](https://github.com/obadx/prepare-quran-dataset?tab=readme-ov-file#moshaf-attributes-docs).


## الرسم الصوتي للقرآن الكريم

### 📊 خرائط المواقع (Position Mappings)

خرائط المواقع توفر تتبع دقيق لمواقع الأحرف من النص العثماني الأصلي إلى النص الصوتي المحول.
Position mappings provide precise tracking of character positions from original Uthmani text to converted phonetic text.

```python
# i الوصول إلى بيانات الخرائط
mappings = phonetic_script.mappings  # List[MappingPos | None]
phonemes = phonetic_script.phonemes  # str

# المرور على خرائط الأحرف
for idx, mapping in enumerate(mappings):
    if mapping is not None:
        # الحصول على امتداد الموقع
        start, end = mapping.pos  # Python-style slice notation
        # استخراج الصوت المقابل
        char_phoneme = phonemes[start:end]
        print(f"الحرف {idx} ينتقل إلى الصوت في الموقع ({start}, {end})")
    else:
        print(f"الحرف {idx} تم حذفه أثناء التحويل")
```

#### **فهم MappingPos (Understanding MappingPos)**
```python
@dataclass
class MappingPos:
    """خرائط المواقع لتحويلات الأحرف (Position mapping for character transformations)"""
    pos: tuple[int, int]  # (بداية، نهاية) - بالطريقة البايثونية
    tajweed_rules: list[TajweedRule] | None = None  # قواعد التجويد المرتبطة
```


### الحروف: (43)


| Phoneme Name          | Symbol | الحرف  بالعربية                          |
|-----------------------|--------|--------------------------------------|
| hamza                 | ء      | همزة                                 |
| baa                   | ب      | باء                                  |
| taa                   | ت      | تاء                                  |
| thaa                  | ث      | ثاء                                  |
| jeem                  | ج      | جيم                                  |
| haa_mohmala           | ح      | حاء                                  |
| khaa                  | خ      | خاء                                  |
| daal                  | د      | دال                                  |
| thaal                 | ذ      | ذال                                  |
| raa                   | ر      | راء                                  |
| zay                   | ز      | زاي                                  |
| seen                  | س      | سين                                  |
| sheen                 | ش      | شين                                  |
| saad                  | ص      | صاد                                  |
| daad                  | ض      | ضاد                                  |
| taa_mofakhama         | ط      | طاء                                  |
| zaa_mofakhama         | ظ      | ظاء                                  |
| ayn                   | ع      | عين                                  |
| ghyn                  | غ      | غين                                  |
| faa                   | ف      | فاء                                  |
| qaf                   | ق      | قاف                                  |
| kaf                   | ك      | كاف                                  |
| lam                   | ل      | لام                                  |
| meem                  | م      | ميم                                  |
| noon                  | ن      | نون                                  |
| haa                   | ه      | هاء                                  |
| waw                   | و      | واو                                  |
| yaa                   | ي      | ياء                                  |
| alif                  | ا      | نصف مد ألف                                  |
| yaa_madd              | ۦ       | نصف مد ياء |
| waw_madd              | ۥ       | نصف مد واوا |
| fatha                 | َ       | فتحة                                 |
| dama                  | ُ       | ضمة                                 |
| kasra                 | ِ       | كسرة                                 |
| fatha_momala          | ۪       | فتحة ممالة 
| alif_momala           | ـ       | ألف ممالة
| hamza_mosahala        | ٲ       | همزة مسهلة                           |
| qlqla                 | ڇ       | قلقة                                 |
| noon_mokhfah          | ں       | نون مخفاة                            |
| meem_mokhfah          | ۾       | ميم مخفاة                            |
| sakt                  | ۜ       | سكت                                  |
| dama_mokhtalasa       | ؙ       | ضمة مختلسة (عند الروم في تأمنا)

### صفات الحروف (10)

| Sifat (English)        | Sifat (Arabic)       | Available Attributes (English)          | Available Attributes (Arabic)       |
|------------------------|----------------------|----------------------------------------|-------------------------------------|
| hams_or_jahr         | الهمس أو الجهر     | hams, jahr                           | همس, جهر                          |
| shidda_or_rakhawa    | الشدة أو الرخاوة  | shadeed, between, rikhw              | شديد, بين بين, رخو                     |
| tafkheem_or_taqeeq   | التفخيم أو الترقيق | mofakham, moraqaq, low_mofakham                    | مفخم, مرقق, أدنى المفخم                         |
| itbaq                | الإطباق            | monfateh, motbaq                     | منفتح, مطبق                        |
| safeer               | الصفير             | safeer, no_safeer                    | صفير, لا صفير                      |
| qalqla               | القلقلة            | moqalqal, not_moqalqal               | مقلقل, غير مقلقل                   |
| tikraar              | التكرار            | mokarar, not_mokarar                 | مكرر, غير مكرر                     |
| tafashie             | التفشي             | motafashie, not_motafashie           | متفشي, غير متفشي                   |
| istitala             | الاستطالة          | mostateel, not_mostateel             | مستطيل, غير مستطيل                 |
| ghonna               | الغنة              | maghnoon, not_maghnoon               | مغنون, غير مغنون                   |



# Needs refactory


# Build for Source
create a `venv` or a conda environment to avoid coflicts, Then
```bash
cd quran-transcript
python -m pip install -r ./

````
# Annotation Application of annotation imlaey to uthmnai
To start server:
```bash
python -m uvicorn server:app --port 900
```

To start streamlit
```bash
python -m streamlit run streamlit_app
```

# Quran Script Description
[TODO]

# `merge_uthmani_imlaey.py`
Merging Uthmani Quran and Imlaye Quran scipts of [tanzil](https://tanzil.net/download/) into a single scipt (".xml" and ".json")
* Uthmanic: without (pause marks, sajda signs, hizb signs)
* Imlaey: without (pause marks, sajda signs, hizb signs and tatweel sign)
Usage:
```bash
usage: Merge Uthmani and Imlaey Script into a single scipt [-h] [--uthmani-file UTHMANI_FILE] [--imlaey-file IMLAEY_FILE] [--output-file OUTPUT_FILE]

options:
  -h, --help            show this help message and exit
  --uthmani-file UTHMANI_FILE
                        The path to the input file "file.xml"
  --imlaey-file IMLAEY_FILE
                        The path to the input file "file.xml"
  --output-file OUTPUT_FILE
                        The path to the output file either ".json" or ".xml"
```

Example within the repo (json):
```bash
python merge_uthman_imlaey.py --uthmani-file quran-script/quran-uthmani-without-pause-sajda-hizb-marks.xml --imlaey-file quran-script/quran-simple-imlaey-without-puase-sajda-hizb-marks-and-tatweel.xml --output-file quran-script/quran-uthmani-imlaey.json
```

Example within the repo (json):
```bash
python merge_uthman_imlaey.py --uthmani-file quran-script/quran-uthmani-without-pause-sajda-hizb-marks.xml --imlaey-file quran-script/quran-simple-imlaey-without-puase-sajda-hizb-marks-and-tatweel.xml --output-file quran-script/quran-uthmani-imlaey.xml
```

# TODO
- [ ] `quran_transcript` docs
- [ ] adding tests
- [ ] CI/CD with github

