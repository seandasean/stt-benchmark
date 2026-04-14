# STT Benchmark — Multi-Condition Audio Evaluation

This project evaluates speech-to-text (STT) performance across multiple real-world audio conditions using Word Error Rate (WER) as the primary metric.

## Overview

- Dataset: 12 Common Voice clips  
- Evaluation approach: controlled condition comparison using identical source clips  
- Conditions:
  - Clean (baseline)
  - Broadband noise
  - MP3 compression (64 kbps)
  - Combined (noise + codec)
- Engine: OpenAI (`gpt-4o-mini-transcribe`)  
- Primary metric: Word Error Rate (WER)

---

## Results Summary

| Condition        | WER     | Δ vs Clean |
|------------------|---------|------------|
| Clean            | 0.1124  | —          |
| Noise            | 0.3708  | +0.2584    |
| Codec (MP3 64k)  | 0.1184  | +0.0060    |
| Combined         | 0.4552  | +0.3428    |

- Noisy condition: **9 valid / 12 total samples (3 failures)**

---

## Key Findings

### Noise is highly destructive  
Broadband noise significantly degrades transcription accuracy and caused complete failure in ~25% of samples.

### Codec compression is resilient (in isolation)  
MP3 compression at 64 kbps produced negligible WER impact when applied to clean speech.

### Stacked degradations amplify failure  
Combining noise with codec compression increased WER to **0.4552**, substantially worse than noise alone (**0.3708**).

### Perceptual quality ≠ transcription performance  
Audio that sounds degraded to humans can still transcribe accurately unless core speech intelligibility is compromised.

### Single-condition testing can be misleading  
Evaluating degradations in isolation may underestimate real-world failure, where multiple artifacts interact.

---

## What This Shows

This benchmark highlights key evaluation principles for speech systems:

- STT performance is driven by **intelligibility loss**, not just perceptual degradation  
- Signal masking (noise) is significantly more damaging than compression artifacts  
- Stacked degradations reveal **failure amplification** not visible in isolated tests  
- Controlled condition testing helps isolate **failure modes vs. robustness zones**

---

## Results Files

- Clean: `benchmark_output/openai_clean_final_results.csv`  
- Noise: `benchmark_output/openai_noisy_results.csv`  
- Codec: `benchmark_output/openai_codec_results.csv`  
- Combined: `benchmark_output/openai_combined_results.csv`  

---

## Sample Output

![Benchmark Preview](docs/benchmark_preview.png)

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

- Expand evaluation matrix (reverb, compression artifacts, additional combinations)  
- Compare multiple STT engines  
- Standardize scoring and reporting workflow  
- Incorporate bootstrap confidence intervals into headline metrics  

---

## Portfolio Summary

This project evaluates how speech-to-text performance changes across multiple audio degradation conditions using OpenAI’s `gpt-4o-mini-transcribe`.

On a 12-clip Common Voice sample:
- Clean WER: **0.1124**
- Noise WER: **0.3708**
- Codec WER: **0.1184**
- Combined WER: **0.4552**

Results show that while compression alone has minimal impact, **stacked degradations significantly amplify transcription failure**, highlighting the importance of evaluating realistic multi-condition scenarios rather than isolated effects.

---

## Audio QA Evaluation Samples

In addition to benchmarking, this project includes structured audio QA evaluations that simulate real-world model review workflows.

- [QA Portfolio Summary](docs/qa_portfolio_summary.md)
- Sample Evaluations:
  - [Sample 01](docs/qa_sample_01.md)
  - [Sample 02](docs/qa_sample_02.md)
  - [Sample 03](docs/qa_sample_03.md)

These samples demonstrate evaluation across failure, degraded, and acceptable audio conditions, including artifact detection, scoring, and cause analysis.