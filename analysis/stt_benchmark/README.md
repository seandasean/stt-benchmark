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
|----------|--------|
| Clean    | 0.1124 |
| Noisy    | 0.3708 |

- Δ WER: +0.2584  
- Failures: 3 / 12 noisy samples (no transcript returned)

### Key Insight

While performance on clean audio is strong, noise introduces a significant degradation in both accuracy and system reliability. In addition to higher WER, complete transcription failures were observed under noisy conditions.

This highlights the importance of evaluating:
- Robustness under real-world conditions
- Failure rates (not just average metrics)

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