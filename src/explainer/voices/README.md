# Narrator voices

The `qwen` engine clones the voice in `<Name>.wav`. `<Name>.txt` holds the exact
transcript of that clip. To add a voice, add both files; the file name is the voice name.

## Ellis

A synthetic voice, not a recording of a person. Qwen3-TTS-12Hz-1.7B-VoiceDesign
(Apache-2.0) made it from this description, with `mx.random.seed(1)`:

> A patient male teacher with a warm, mid-low American voice, explaining an idea one
> step at a time. Slow, relaxed pace with natural pauses. Plain, sincere,
> conversational delivery.

The clip was then raised by 3.5 dB, so cloned speech is about −21 LUFS.

It was chosen for intonation close to human read speech. Measured on cloned
passages, the pitch standard deviation is about 3.2 semitones, and the 5th to 95th
percentile range is about 11 semitones. LibriSpeech readers measure 3.0 and 9.6.
The previous preset voice, Aiden, measured 5.4 and 18.6.
