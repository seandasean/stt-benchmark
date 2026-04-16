# STT Benchmark — Multi-Condition Audio Evaluation

This project evaluates speech-to-text (STT) performance across multiple real-world audio degradation conditions using Word Error Rate (WER) as the primary metric.

---

## Overview

- Dataset: 12 Common Voice speech clips  
- Evaluation approach: controlled condition comparison using identical source clips  
- STT Engine: OpenAI (`gpt-4o-mini-transcribe`)  
- Primary metric: Word Error Rate (WER)

### Conditions Evaluated
- Clean (baseline)
- Broadband noise (signal masking)
- MP3 compression (64 kbps)
- Reverb (temporal smearing)
- Combined (noise + codec)

---

## Results Summary

| Condition        | WER     | Δ vs Clean |
|------------------|---------|------------|
| Clean            | 0.1124  | —          |
| Reverb           | 0.1078  | -0.0046    |
| Codec (MP3 64k)  | 0.1184  | +0.0060    |
| Noise            | 0.3708  | +0.2584    |
| Combined         | 0.4552  | +0.3428    |

- Noisy condition: **9 valid / 12 total samples (3 failures)**

---

## Key Findings

### Noise is the dominant failure driver  
Broadband noise significantly degrades transcription accuracy (+0.2584 WER) and introduces complete transcription failures (~25% of samples).

### Codec compression is highly resilient (in isolation)  
MP3 compression at 64 kbps produces negligible impact on transcription accuracy when applied to clean speech.

### Reverb shows no measurable degradation at moderate levels  
Mild reverberation does not significantly impact WER, indicating robustness to temporal smearing when intelligibility is preserved.

### Stacked degradations amplify failure  
Combining noise with codec compression increases WER to **0.4552**, significantly worse than noise alone (**0.3708**), demonstrating failure amplification.

### Perceptual quality ≠ transcription performance  
Audio that sounds degraded to humans can still transcribe accurately unless core speech intelligibility is compromised.

### Single-condition testing is insufficient  
Evaluating degradations in isolation can underestimate real-world failure, where multiple artifacts interact.

---

## What This Demonstrates

This benchmark highlights key evaluation principles for STT systems:

- STT performance is driven primarily by **intelligibility loss**, not perceptual degradation  
- **Signal masking (noise)** is far more destructive than compression artifacts  
- **Temporal smearing (reverb)** is tolerated under moderate conditions  
- **Stacked degradations** reveal failure modes not visible in isolated tests  
- Controlled evaluation enables clear separation of **robustness vs. failure conditions**

---

## Results Files

- Clean: `benchmark_output/openai_clean_final_results.csv`  
- Noise: `benchmark_output/openai_noisy_results.csv`  
- Codec: `benchmark_output/openai_codec_results.csv`  
- Reverb: `benchmark_output/openai_reverb_results.csv`  
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

## Current Scope

This project represents **Phase 1** of a broader STT evaluation framework:

- Single-engine evaluation  
- Multi-condition robustness testing  
- WER as the primary comparison metric  
- Focus on failure modes and degradation behavior  

---

## Next Steps

- Expand condition matrix (reverb + noise, reverb + codec)  
- Introduce additional metrics (CER, substitution/deletion breakdown)  
- Compare multiple STT engines (Whisper, Google STT, AssemblyAI)  
- Incorporate bootstrap confidence intervals for statistical reporting  

---

## Portfolio Summary

This project evaluates how speech-to-text performance changes across realistic audio degradation conditions.

On a 12-clip Common Voice dataset:

- Clean WER: **0.1124**  
- Reverb WER: **0.1078**  
- Codec WER: **0.1184**  
- Noise WER: **0.3708**  
- Combined WER: **0.4552**  

Results show that:

- Compression and mild reverberation have minimal impact individually  
- Noise introduces significant degradation and system instability  
- **Stacked degradations significantly amplify transcription failure**

This highlights the importance of evaluating STT systems under **multi-condition, real-world scenarios**, rather than relying on isolated tests.

---

## Audio QA Evaluation Samples

In addition to benchmarking, this project includes structured audio QA evaluations simulating real-world model review workflows.

- [QA Portfolio Summary](docs/qa_portfolio_summary.md)
- Sample Evaluations:
  - [Sample 01](docs/qa_sample_01.md)
  - [Sample 02](docs/qa_sample_02.md)
  - [Sample 03](docs/qa_sample_03.md)

These demonstrate:
- artifact detection  
- structured evaluation scoring  
- transcription impact analysis  