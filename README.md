# STT Benchmark — Multi-Condition Audio Evaluation

This project evaluates speech-to-text (STT) performance across multiple real-world audio conditions using Word Error Rate (WER) as the primary metric.

## Overview

- Dataset: 12 Common Voice clips  
- Evaluation approach: controlled condition comparison using identical source clips  
- Conditions:
  - Clean (baseline)
  - Broadband noise
  - MP3 compression (64 kbps)
- Engine: OpenAI (`gpt-4o-mini-transcribe`)  
- Primary metric: Word Error Rate (WER)

---

## Key Findings

### WER Summary

- Clean: **0.1124**  
- Noise: **0.3708** (**+0.2584 vs. clean**)  
- Codec (MP3 64 kbps): **0.1184** (**+0.0060 vs. clean**)  

- Noisy condition: **9 valid / 12 total samples (3 dropped due to transcription failure)**

### Insights

- **Noise is highly destructive**  
  Broadband noise significantly degrades transcription accuracy and caused complete failure in ~25% of samples, indicating strong sensitivity to signal masking.

- **Codec compression is highly resilient**  
  MP3 compression at 64 kbps produced negligible WER impact despite audible degradation, suggesting robustness to lossy encoding artifacts.

- **Perceptual quality ≠ transcription performance**  
  Audio that sounds degraded to humans can still transcribe accurately unless core speech intelligibility is compromised.

---

## What This Shows

This benchmark highlights key evaluation principles for speech systems:

- STT performance is driven by **intelligibility loss**, not just perceptual degradation  
- Signal masking (noise) is far more damaging than compression artifacts  
- Controlled condition testing helps isolate **failure modes vs. robustness zones**

---

## Results

- Clean: `benchmark_output/openai_clean_final_results.csv`  
- Noise: `benchmark_output/openai_noisy_results.csv`  
- Codec: `benchmark_output/openai_codec_results.csv`  

---

## Project Structure
stt_benchmark/
├── data/
├── benchmark_output/
├── analysis/
├── engines/
├── nr_processing/
├── docs/

---

## Next Steps

- Add combined degradation condition (noise + codec)  
- Expand evaluation matrix (reverb, compression artifacts, combined conditions)  
- Compare multiple STT engines  
- Standardize scoring and reporting workflow  
- Incorporate bootstrap confidence intervals into headline metrics  