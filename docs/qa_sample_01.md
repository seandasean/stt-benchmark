# Audio QA Evaluation — Sample 01

## File
common_voice_en_687348_noisy.wav

## Overall Impression
Severe broadband noise overwhelms the signal, resulting in near-total intelligibility loss.

## Strengths
- Residual speech signal remains faintly detectable beneath noise  
- Temporal structure of speech is preserved despite masking

## Issues Detected
- Extreme broadband noise masking speech across full frequency spectrum (e.g., ~0:00, ~0:05)
- Poor signal-to-noise ratio (speech significantly recessed beneath noise floor)  
- Reduced phoneme intelligibility due to spectral masking  
- Low-energy speech components fully obscured

## Artifact Tags
- NOI (Noise floor issue)
- MUF (Muffled / masked speech)
- DYN (Imbalanced signal-to-noise ratio)

## Severity
High

## Impact on Transcription
- Severe phoneme masking → high substitution rate  
- Likely word deletions due to inaudible segments  
- Reduced model confidence across entire utterance

## Scores
- Naturalness: 1
- Clarity: 1
- Prosody: 2
- Artifact Severity: 5
- Commercial Readiness: 1

## Would this require human review?
Yes

## Notes (Cause Analysis)
Broadband noise dominates the signal, masking key speech frequencies and collapsing phoneme distinction. Likely caused by excessive noise addition or improper gain staging, resulting in critically low signal-to-noise ratio and cascading transcription errors.