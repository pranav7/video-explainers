from explainer.render import _join, caption_cues


def words(text, step=0.3):
    out, t = [], 0.0
    for token in text.split():
        out.append({"word": token, "start": t, "end": t + step})
        t += step
    return out


def test_join_attaches_punctuation():
    assert _join(words("The Executor reads , and why : say .")) == "The Executor reads, and why: say."


def test_cues_split_long_lines_and_stay_contiguous():
    w = words("Rows come from a spreadsheet , and the server matches them by order number , every time it runs .")
    cues = caption_cues(10.0, 20.0, w)
    assert len(cues) > 1
    assert all(len(text) <= 42 for _, _, text in cues)
    assert cues[0][0] == 10.0 and cues[-1][1] == 20.0
    assert all(a[1] == b[0] for a, b in zip(cues, cues[1:]))


def test_short_line_is_one_cue():
    assert caption_cues(0, 2, words("So what went wrong ?")) == [(0, 2, "So what went wrong?")]


def test_cue_never_starts_with_punctuation():
    w = words("The importer reads every row from the sheet , then it checks the totals .")
    cues = caption_cues(0, 10, w)
    assert all(not text[0] in ",.;:!?" for _, _, text in cues)


def test_join_handles_openers_and_quotes():
    assert _join(words('it said " hello " and costs $ 5 ( roughly )')) == 'it said "hello" and costs $5 (roughly)'
