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
## 🆕 ما الجديد في الإصدار 0.5.1 (What's New in Version 0.5.1)

### 🎯 تحليل أخطاء التلاوة (Recitation Error Analysis)
- إضافة دالة `explain_error` لمقارنة النص الصوتي المتوقع (المرجع) مع النص الصوتي المُتنبأ به (مثلاً من قارئ أو نموذج تعلم آلي).
- توفير تحليل تفصيلي للأخطاء يشمل:
  - نوع الخطأ: تجويدي (`tajweed`)، عادي (`normal`)، أو حركات (`tashkeel`).
  - نوع الخطأ الكلامي: إدراج (`insert`)، حذف (`delete`)، أو استبدال (`replace`).
  - قواعد التجويد المرتبطة بالخطأ (مثل المد، القلقلة، الغنة) مع تحديد الطول المتوقع والفعلي عند الاقتضاء.
- تمثيل النتائج باستخدام كائن `ReciterError` الذي يحتوي على معلومات دقيقة عن موقع الخطأ في النص العثماني والصوتي.
- هذه الأداة مفيدة لتقييم أداء قراء القرآن، وتحليل أخطاء نماذج التعرف على الكلام، وتقديم تغذية راجعة للمتعلمين.








## 🆕 ما الجديد في الإصدار 0.4.0 (What's New in Version 0.4.0)

### 🔍 بحث صوتي ضبابي محسّن (Optimized Fuzzy Phonetic Search)
- إضافة فئة `PhoneticSearch` للبحث عن نصوص صوتية في القرآن باستخدام التشابه الضبابي (Levenshtein distance) باستخدام مكتبة [fuzzysearch](https://github.com/taleinat/fuzzysearch)
- بناء فهرس مسبق للرسم الصوتي (phoneme index) لتسريع البحث بشكل كبير.
- دعم تحديد نسبة الخطأ المسموح بها (`error_ratio`) للحصول على نتائج حتى مع الاختلافات الطفيفة.
- تمثيل النتائج باستخدام `PhonemesSearchSpan` و `PhonmesSearhResult` مع معلومات دقيقة عن الموقع (السورة، الآية، الكلمة، الحرف، المؤشر الصوتي).

### 🛠️ بناء الفهرس (Building the Index)
- يتم تضمين الفهرس الجاهز (`ph_index.npy` و `ref_norm_ph.txt`) داخل الحزمة، ولا يحتاج المستخدم العادي إلى بنائه.
- للمطورين الذين يرغبون في إعادة بناء الفهرس (بعد تعديل قواعد التحويل الصوتي مثلاً)، يمكن استخدام الأمر:
  ```bash
  python -m ph-ndx
  ```
  وسيتم حفظ الملفات في مجلد `quran-script` داخل الحزمة.

## 🆕 ما الجديد في الإصدار 0.3.0 (What's New in Version 0.3.0)

### 📍 خرائط المواقع الجديدة (New Position Mappings)
- أسرع مرتان  في عملية إنشاء الرسم الصوتي (Faster 2x in phonetizatoin)
- تمثيل الحروف المحذوفة ب `MappingPos(pos=(x, x), deleted=True` - حيث `x` رقم صحيح أكبر من الصفر -  بدلا من `None` (Represent deleted characther with `MappingPos(pos=(x, x), deleted=True)` -where `x` is an integer >=0- instead of `None`)


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
# print(f"صفات الحروف:\n{phonetic_script.sifat}")
print('\n' * 2)
print("صفات الحروف:")
for sifa in phonetic_script.sifat:
    print(json.dumps(sifa.model_dump(), ensure_ascii=False, indent=4))
    print()


# جديد: عرض خرائط المواقع
print('\n' * 2)
print("خرائط المواقع:")
for idx, (uth_char, mapping) in enumerate(zip(uthmani_script, phonetic_script.mappings)):
    if not mapping.deleted:
        # استخراج الصوت لهذا الحرف
        phoneme = phonetic_script.phonemes[mapping.pos[0]:mapping.pos[1]]
        print(f"حرف: '{uth_char}' -> صوت: '{phoneme}' (موقع: {mapping.pos})")
    else:
        print(f"حرف: '{uth_char}' -> محذوف")

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
    deleted: bool = False  # حالة الحذف - True إذا تم حذف الحرف مع حفظ الموقع وتتساوي البداية والنهاية في ال `pos`
```

### 📖 مثال على استخدام البحث الصوتي (Example of Phonetic Search)

```python
from quran_transcript import PhoneticSearch

# إنشاء كائن البحث (سيحمل الفهرس تلقائياً)
searcher = PhoneticSearch()

# نص صوتي للبحث (يمكن أن يكون غير دقيق)
query = "قَلِۦۦلَممممَاا"  # مثال من الاختبارات

# البحث بنسبة خطأ 10%
results = searcher.search(query, error_ratio=0.1)

# عرض النتائج
for r in results:
    print(f"سورة {r.start.sura_idx}, آية {r.start.aya_idx}")
    print(f"  من كلمة {r.start.uthmani_word_idx} حرف {r.start.uthmani_char_idx} إلى كلمة {r.end.uthmani_word_idx} حرف {r.end.uthmani_char_idx}")
    print(f"  المؤشرات الصوتية: {r.start.phonemes_idx} - {r.end.phonemes_idx}")

# استخراج النص العثماني المطابق
uthmani_text = searcher.get_uthmani_from_result(results[0])
print(f"النص العثماني: {uthmani_text}")
```

### 📦 كائنات النتائج (Result Dataclasses)

#### `PhonemesSearchSpan`
يمثل موقعاً واحداً في القرآن (بداية أو نهاية المطابقة):
- `sura_idx`: رقم السورة (1-based)
- `aya_idx`: رقم الآية (1-based)
- `uthmani_word_idx`: فهرس الكلمة داخل الآية (0-based)
- `uthmani_char_idx`: فهرس الحرف داخل الكلمة (0-based، شامل للبداية، غير شامل للنهاية)
- `phonemes_idx`: فهرس المجموعة الصوتية في التسلسل الصوتي المرجعي (0-based)

#### `PhonmesSearhResult`
يحتوي على زوج من `PhonemesSearchSpan` للبداية والنهاية:
- `start`: موقع بداية المطابقة
- `end`: موقع نهاية المطابقة (غير شامل)

### 📖 مثال على تحليل أخطاء التلاوة (Error Analysis Example)

```python
from quran_transcript import (
    quran_phonetizer,
    MoshafAttributes,
    ReciterError,
    explain_error,
)

# إعداد خصائص المصحف
moshaf = MoshafAttributes(
    rewaya="hafs",
    madd_monfasel_len=4,
    madd_mottasel_len=4,
    madd_mottasel_waqf=4,
    madd_aared_len=4,
)

# النص العثماني الأصلي
uthmani_text = "قَالُوٓا۟"

# نص صوتي متوقع (مرجعي)
ref_out = quran_phonetizer(uthmani_text, moshaf)
print("المرجع:", ref_out.phonemes)

# نص صوتي مُتنبأ به (به أخطاء)
predicted_text = "فكۥۥلۥۥ"
print("المتنبأ به:", predicted_text)

# تحليل الأخطاء
errors = explain_error(
    uthmani_text=uthmani_text,
    ref_ph_text=ref_out.phonemes,
    predicted_ph_text=predicted_text,
    mappings=ref_out.mappings,
)

# عرض النتائج
for err in errors:
    print("\n" + "="*50)
    print(f"الموقع في العثماني: `{uthmani_text[err.uthmani_pos[0]:err.uthmani_pos[1]]}`, {err.uthmani_pos}")
    print(f"الموقع في الصوتي: `{ref_out.phonemes[err.ph_pos[0]:err.ph_pos[1]]}`, {err.ph_pos}")
    print(f"نوع الخطأ: {err.error_type} - {err.speech_error_type}")
    print(f"المتوقع: '{err.expected_ph}' - المُتنبأ به: '{err.preditected_ph}'")
    if err.ref_tajweed_rules:
        for rule in err.ref_tajweed_rules:
            print(f"  قاعدة تجويد مرجعية: {rule.name.ar} ({rule.name.en})")
    if err.replaced_tajweed_rules:
        for rule in err.replaced_tajweed_rules:
            print(f"  قاعدة تجويد مستبدلة: {rule.name.ar} ({rule.name.en})")
    if err.missing_tajweed_rules:
        for rule in err.missing_tajweed_rules:
            print(f"  قاعدة تجويد مفقودة: {rule.name.ar} ({rule.name.en})")
```

**مخرجات متوقعة (Partial output):**
```
المرجع: قَاالُۥۥ
المتنبأ به: فكۥۥلۥۥ

==================================================
الموقع في العثماني: ``, (0, 0)
الموقع في الصوتي: ``, (0, 0)
نوع الخطأ: normal - insert
المتوقع: '' - المُتنبأ به: 'ف'

==================================================
الموقع في العثماني: `قَ`, (0, 2)
الموقع في الصوتي: `قَ`, (0, 2)
نوع الخطأ: normal - replace
المتوقع: 'قَ' - المُتنبأ به: 'ك'

==================================================
الموقع في العثماني: `ا`, (2, 3)
الموقع في الصوتي: `اا`, (2, 4)
نوع الخطأ: tajweed - replace
المتوقع: 'اا' - المُتنبأ به: 'ۥۥ'
  قاعدة تجويد مرجعية: المد الطبيعي (Normal Madd)
  قاعدة تجويد مستبدلة: المد الطبيعي (Normal Madd)

==================================================
الموقع في العثماني: `لُ`, (3, 5)
الموقع في الصوتي: `لُ`, (4, 6)
نوع الخطأ: tashkeel - delete
المتوقع: 'لُ' - المُتنبأ به: 'ل'
```

---

### 📦 كائنات تحليل الأخطاء (Error Analysis Dataclasses)

#### `ReciterError`
يمثل خطأ واحد في التلاوة:
- `uthmani_pos`: tuple[int, int] – موقع الخطأ في النص العثماني (بداية، نهاية).
- `ph_pos`: tuple[int, int] – موقع الخطأ في النص الصوتي المرجعي (بداية، نهاية).
- `error_type`: Literal["tajweed", "normal", "tashkeel"] – نوع الخطأ.
- `speech_error_type`: Literal["insert", "delete", "replace"] – نوع الخطأ الكلامي.
- `expected_ph`: str – المقطع الصوتي المتوقع.
- `preditected_ph`: str – المقطع الصوتي المُتنبأ به.
- `expected_len`: Optional[int] – الطول المتوقع (لأخطاء المد مثلاً).
- `predicted_len`: Optional[int] – الطول الفعلي.
- `ref_tajweed_rules`: Optional[list[TajweedRule]] – قواعد التجويد المرتبطة بالمقطع المتوقع.
- `inserted_tajweed_rules`, `replaced_tajweed_rules`, `missing_tajweed_rules`: Optional[list[TajweedRule]] – قواعد التجويد التي تم إدراجها أو استبدالها أو فقدانها.


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

## 👨‍💻 Developer Setup

### Prerequisites

Install **uv** (fast Python package manager) by following the official guide:  
[https://docs.astral.sh/uv/#installation](https://docs.astral.sh/uv/#installation)

Quick install (macOS/Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Quick install (Windows):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Cloning

```bash
git clone https://github.com/obadx/quran-transcript.git
cd quran-transcript
```

### Installing Dependencies

```bash
uv sync --all-extras
```

### Running Tests

Run all tests (as configured in `pyproject.toml`):

```bash
uv run pytest
```

Run individual test files:

```bash
uv run pytest tests/phonetics_pytest.py -v
uv run pytest tests/aya_pytest.py -vv
uv run pytest tests/test_sub_with_mapping_pytest.py -vv
uv run pytest tests/test_phonemes_search_pytest.py -vv
uv run pytest tests/test_explain_error_pytest.py -vv
```

### ⚠️ Windows Users: Symlink Workaround

The package data (`quran-script/`) is linked into `src/quran_transcript/` via a relative symlink:

```
src/quran_transcript/quran-script -> ../../quran-script/
```

This symlink may not work on Windows by default. To resolve this, either:

1. **Enable Developer Mode** (Windows 10/11):  
   Settings → Update & Security → For Developers → Enable Developer Mode.  
   This allows Windows to support symlinks without elevated privileges.

2. **Manually copy the directory** (no symlink needed):
   ```cmd
   rmdir src\quran_transcript\quran-script
   xcopy /E quran-script src\quran_transcript\quran-script\
   ```

3. **Use `mklink /D`** (run as Administrator):
   ```cmd
   cd src\quran_transcript
   rmdir quran-script
   mklink /D quran-script ..\..\quran-script
   ```

---

### 🧪 Running Tests

The test suite includes **stress tests** (marked with `@pytest.mark.stress`) that iterate over the whole Quran and are slow.

Run the **full** test suite (includes stress tests):

```bash
uv run pytest
```

Run a **quick** test pass (skips stress tests):

```bash
uv run pytest --skip-stress
```

Run **only** the stress tests:

```bash
uv run pytest -m stress
```

