# Find any number in twenty guesses

For anyone curious, no programming needed. About 1 minute.

## Palette

| Concept | Colour |
| --- | --- |
| The numbers still possible (the range) | SKY |
| A guess | AMBER |
| Numbers ruled out | FAINT (neutral) |
| The answer to a guess ("higher", "lower") | VIOLET |
| The result | MINT |

## 1. Hook: Twenty guesses for a million

- "Pick a number between one and a million. I can find it in twenty guesses."
  - A long, thick rounded bar across the frame: the range, in sky. "1" under its left end and "1,000,000" under its right end. Then an amber tag "20 guesses" appears above the bar.
- "After each guess, you only tell me higher or lower."
  - A person icon at the bottom left with a speech bubble that shows "higher". The bubble text changes to "lower".

## 2. Halving: Cut the range in half

- "My first guess is the middle: five hundred thousand."
  - An amber arrow drops onto the middle of the bar with the tag "500,000".
- "Lower. In one guess, half of the numbers are gone."
  - A violet tag "lower" appears. The right half of the bar turns faint grey. The left half stays sky.
- "Next, the middle of what is left: two hundred and fifty thousand."
  - The camera zooms in on the sky half. The amber arrow moves to its middle, tag "250,000".
- "Higher. Half of what was left is gone again."
  - A violet tag "higher". The left part of the sky half turns faint. A quarter of the bar is left, from 250,000 to 500,000. The camera zooms back out to show the whole bar.

## 3. WhyTwenty: Why twenty is enough

- "Each guess halves the range. A million, five hundred thousand, two hundred and fifty thousand, and so on."
  - The bar fades. A bar chart of the range after each guess appears row by row: "start" 1,000,000; "guess 1" 500,000; "guess 2" 250,000; "guess 3" 125,000; "guess 4" 62,500. The bars shrink by half each row.
- "After twenty halvings, one number is left."
  - The chart fades. A big mint number "20" with the caption "guesses to reach one number".
- "Double the range to two million, and it takes just one more guess."
  - The "20" turns into "21" in one step (no counting), and the caption changes to "guesses for two million numbers".
- "This is binary search. In a sorted list of a billion items, it needs only thirty steps."
  - A code window "binary_search.py" with the function below. Highlight the line `mid = (lo + hi) // 2`. Beside it, a big amber "30" with the caption "steps for a billion items".

```python
def binary_search(items, target):
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return None
```

## Facts behind each line (for checking)

- 2^20 = 1,048,576, which is at least 1,000,000, so 20 guesses always find the number.
- 2^21 = 2,097,152, which is at least 2,000,000, so two million needs 21 guesses.
- 2^30 = 1,073,741,824, which is at least 1,000,000,000, so a billion needs 30 steps.
- After "lower" at 500,000, the range is 1 to 499,999. Its middle is 250,000. After "higher", the range is 250,001 to 499,999.
