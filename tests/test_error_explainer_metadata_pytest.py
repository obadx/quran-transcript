from quran_transcript.phonetics.error_explainer import ReciterError, normalize_error_details


def test_tajweed_length_short_sets_error_code_and_symbol_metadata():
    err = ReciterError(
        uthmani_pos=(36, 37),
        ph_pos=(27, 31),
        error_type='tajweed',
        speech_error_type='replace',
        expected_ph='ۦۦۦۦ',
        preditected_ph='ۦۦ',
        expected_len=4,
        predicted_len=2,
    )

    out = normalize_error_details([err])[0]

    assert out.error_code == 'TAJWEED_LENGTH_SHORT'
    assert out.symbol_metadata == {
        'ۦ': {
            'attr': 'yaa_madd',
            'label_en': 'Yaa madd',
            'symbol_class': 'madd',
        }
    }


def test_tashkeel_replace_sets_lengths_and_error_code():
    err = ReciterError(
        uthmani_pos=(4, 6),
        ph_pos=(3, 5),
        error_type='tashkeel',
        speech_error_type='replace',
        expected_ph='مِ',
        preditected_ph='مُ',
    )

    out = normalize_error_details([err])[0]

    assert out.expected_len == 2
    assert out.predicted_len == 2
    assert out.error_code == 'TASHKEEL_REPLACE'
    assert out.symbol_metadata['م']['symbol_class'] == 'letter'
    assert out.symbol_metadata['ِ']['attr'] == 'kasra'
    assert out.symbol_metadata['ُ']['attr'] == 'dama'
