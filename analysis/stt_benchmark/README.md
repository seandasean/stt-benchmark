# STT Benchmark — Clean Speech Evaluation

This project evaluates speech-to-text (STT) performance using a clean speech dataset and Word Error Rate (WER) as the primary metric.

## Overview

- Dataset: 12 clean speech clips (Common Voice)
- Condition: Clean / raw audio
- Engine: OpenAI (`gpt-4o-mini-transcribe`)
- Evaluation metric: Word Error Rate (WER)

## Results

- Average WER: ~0.1065  
- Output file: `benchmark_output/openai_clean_final_results.csv`

## Clean vs Noisy Evaluation (Robustness Test)

To simulate real-world conditions, the same dataset was re-tested after adding white noise.

### Setup
- Noise type: White noise
- Method: ffmpeg (amplitude = 0.08)
- Same 12 clips used for direct comparison

### Results

| Condition | WER     |
|-----------|---------|
| Clean     | 0.1124  |
| Noisy     | 0.3708  |

- Δ WER: +0.2584  
- Failures: 3 / 12 noisy samples (no transcript returned)

### Key Insight

While performance on clean audio is strong, noise introduces a significant degradation in both accuracy and system reliability. In addition to higher WER, complete transcription failures were observed under noisy conditions.

This highlights the importance of evaluating:
- Robustness under real-world conditions  
- Failure rates (not just average metrics)

### Sample Output

![Benchmark Preview](docs/benchmark_preview.png)

## What This Shows

This benchmark demonstrates:
- Accurate transcription evaluation using WER  
- Error breakdown (substitutions, deletions, insertions)  
- Structured benchmarking workflow for STT systems  

## Project Structure
stt_benchmark/
├── data/
├── benchmark_output/
├── analysis/
├── engines/
├── nr_processing/
└── docs/

## Next Steps

- Add noisy/degraded audio conditions  
- Compare multiple STT engines  
- Evaluate noise reduction impact on WER  

## Portfolio Summary

This project evaluates how speech-to-text performance changes between clean and noisy audio using OpenAI’s `gpt-4o-mini-transcribe`. On a 12-clip Common Voice sample, clean Word Error Rate was approximately 0.1124, while performance degraded to 0.3708 after adding white noise. In addition to increased error rates, 3 of 12 noisy samples failed completely and returned no usable transcript. This highlights the importance of evaluating both accuracy and system reliability under real-world conditions.

## Audio QA Evaluation Samples

In addition to benchmarking, this project includes structured audio QA evaluations that simulate real-world model review workflows.

- [QA Portfolio Summary](docs/qa_portfolio_summary.md)
- Sample Evaluations:
  - [Sample 01](docs/qa_sample_01.md)
  - [Sample 02](docs/qa_sample_02.md)
  - [Sample 03](docs/qa_sample_03.md)

These samples demonstrate evaluation across failure, degraded, and acceptable audio conditions, including artifact detection, scoring, and cause analysis.