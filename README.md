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