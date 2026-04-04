# STT Benchmark — Data Capture Schema  (v4)
# Sean Tallman | AI Audio Specialist Portfolio
# ============================================================

## Reproducibility Statement

This benchmark is fully reproducible using open-source tools.
The automated pipeline (raw / oss_light / oss_heavy NR states) requires
only pip-installable packages listed in requirements.txt. iZotope RX
results (rx_light / rx_heavy) are included as an industry comparison
and are NOT required to replicate core findings. All RX settings are
documented exhaustively in rx_settings.md.

---

## Project Structure

```text
stt_benchmark/
├── data/
│   ├── audio/
│   │   ├── clean/                  # Reference recordings (control)
│   │   ├── processed/
│   │   │   ├── noise/              # SNR ladder: +10, 0, -10 dB
│   │   │   ├── reverb/             # RT60: 0.4s, 1.2s, 2.5s
│   │   │   ├── codec/              # mp3_128k, opus_32k
│   │   │   └── combined/           # noise + reverb
│   │   └── nr_processed/
│   │       ├── oss_light/          # DeepFilterNet output (automated)
│   │       ├── oss_heavy/          # noisereduce output (automated)
│   │       ├── rx_light/           # iZotope RX export (manual, see rx_settings.md)
│   │       └── rx_heavy/           # iZotope RX + Dialogue Isolation (manual)
│   ├── references/
│   │   └── ground_truth.json
│   └── conditions.json
│
├── benchmark_output/
│   ├── {run_id}.json               # Full BenchmarkRun (primary archive)
│   ├── {run_id}_results.csv        # Flat table — one row per transcription attempt
│   ├── {run_id}_summary.csv        # Per-bucket aggregates with bootstrap CI
│   └── {run_id}_nr_delta.csv       # NR preprocessing delta analysis
│
├── wer_calculator.py               # Core metrics + data structures
├── engines/
│   ├── whisper_runner.py
│   ├── google_stt_runner.py
│   └── assemblyai_runner.py
├── nr_processing/
│   ├── deepfilternet_runner.py     # Automated (fully reproducible)
│   └── noisereduce_runner.py       # Automated (fully reproducible)
│   # RX processing is manual — all settings in rx_settings.md
├── run_benchmark.py                # Orchestration loop
├── analysis/
│   ├── analyze_results.py
│   └── benchmark_report.ipynb      # PRIMARY PORTFOLIO ARTIFACT
├── rx_settings.md                  # RX settings log (reproducibility disclosure)
└── requirements.txt
```

---

## Normalization Assumptions (Document These)

WER normalization decisions affect results. Every choice must be documented.

```json
{
  "remove_fillers": true,
  "filler_pattern": "\\b(um+|uh+|hmm+|mm+|mhm+|erm+)\\b",
  "note": "WER computed both with and without filler removal. See wer_with_fillers and filler_sensitivity_delta fields. Applied symmetrically to both reference and hypothesis in all cases."
}
```

Why this matters: some STT engines suppress filler words internally before output.
By running WER both ways and reporting `filler_sensitivity_delta`, the benchmark
makes normalization sensitivity explicit instead of hiding it.

---

## TranscriptionResult — Full Field Reference

| Field                     | Type    | Description                                               |
|---------------------------|---------|-----------------------------------------------------------|
| run_id                    | str     | Unique run identifier                                     |
| audio_file                | str     | Audio filename                                            |
| condition_id              | str     | FK → AudioCondition                                       |
| nr_state                  | str     | FK → NRProcessingConfig.state                             |
| engine                    | str     | whisper / google_stt / assemblyai                         |
| engine_version            | str     | Model/API version                                         |
| engine_config             | JSON    | Language, model size, temperature, etc.                   |
| reference_text            | str     | Ground truth (raw)                                        |
| hypothesis_text           | str     | Engine output (raw)                                       |
| hypothesis_normalized     | str     | After normalization pipeline                              |
| **wer**                   | float   | **Primary metric** — with filler normalization            |
| **wer_with_fillers**      | float   | **WER without filler removal** — normalization check      |
| **cer**                   | float   | **Character Error Rate** — granular accuracy              |
| mer / wil / wip           | float   | jiwer companion metrics                                   |
| **substitutions**         | int     | **S** — wrong word (vocabulary/domain confusion)          |
| **deletions**             | int     | **D** — missing word (confidence pruning)                 |
| **insertions**            | int     | **I** — extra word (hallucination)                        |
| **substitution_rate**     | float   | S / N — normalized for cross-condition comparison         |
| **deletion_rate**         | float   | D / N                                                     |
| **insertion_rate**        | float   | I / N                                                     |
| reference_word_count      | int     | N                                                         |
| hypothesis_word_count     | int     | Words in hypothesis                                       |
| audio_duration_sec        | float   | Clip length                                               |
| transcription_latency_sec | float   | Wall-clock API/model response time                        |
| **rtf**                   | float   | **Real-Time Factor** = latency / duration                 |
| **pesq_wb**               | float?  | **PESQ wideband** (-0.5 to 4.5; correlation data)         |
| pesq_nb                   | float?  | PESQ narrowband (1.0 to 4.5)                              |
| **stoi**                  | float?  | **STOI** (0.0 to 1.0; >0.65 = intelligible)               |
| subjective                | JSON?   | SubjectiveRating (intelligibility / noise / quality)      |
| filler_removal_applied    | bool    | Documents normalization assumption used                   |
| confidence_score          | float?  | Engine confidence if available                            |
| timestamp_utc             | str     | ISO 8601                                                  |
| notes                     | str?    | Free-text annotation                                      |

---

## Summary Statistics Schema (per bucket: engine × condition × nr_state)

| Field                    | Description                                              |
|--------------------------|----------------------------------------------------------|
| mean_wer                 | Bootstrap mean WER                                       |
| median_wer               | Median WER (useful for skewed distributions)             |
| std_wer                  | Standard deviation for interpretability                  |
| wer_ci_lower             | 95% bootstrap CI lower bound                             |
| wer_ci_upper             | 95% bootstrap CI upper bound                             |
| wer_ci_width             | CI width — narrower means more stable estimate           |
| min_wer / max_wer        | Range                                                    |
| mean_wer_with_fillers    | WER without filler removal                               |
| filler_sensitivity_delta | mean_wer_with_fillers − mean_wer                         |
| mean_cer                 | Bootstrap mean CER                                       |
| median_cer               | Median CER                                               |
| std_cer                  | Standard deviation of CER                                |
| cer_ci_lower/upper       | 95% bootstrap CI                                         |
| **mean_substitution_rate**| **S/D/I HEADLINE — engine failure mode analysis**       |
| **mean_deletion_rate**   | See interpretation guide below                           |
| **mean_insertion_rate**  |                                                          |
| **failure_mode**         | substitution_dominant / deletion_dominant / insertion_dominant / mixed |
| total_substitutions/D/I  | Raw totals across all clips in bucket                    |
| mean_rtf                 | Bootstrap mean RTF                                       |
| median_rtf               | Median RTF                                               |
| std_rtf                  | Standard deviation of RTF                                |
| rtf_ci_lower/upper       | 95% bootstrap CI                                         |
| mean_pesq_wb             | Mean PESQ wideband (correlation context)                 |
| mean_stoi                | Mean STOI                                                |

---

## S/D/I Failure Mode Interpretation

Low WER tells you an engine is accurate. S/D/I tells you how it fails.

| Pattern                      | Engine behavior                            | Example finding                                      |
|------------------------------|--------------------------------------------|------------------------------------------------------|
| High deletion_rate           | Aggressive confidence pruning              | "Google STT prunes uncertain words under noise"      |
| High substitution_rate       | Vocabulary mismatch / domain confusion     | "Whisper substitutes audio terms in noisy conditions"|
| High insertion_rate          | Hallucination on noise/silence             | "Whisper inserts words on reverberant silence"       |
| Low WER + high deletion_rate | Conservative engine hiding errors as omissions | "WER understates Google's failure on reverb"    |

---

## PESQ / STOI Interpretation

Critical framing: **we analyze correlation, not causation.**
Higher PESQ does not guarantee lower WER.

| PESQ WB    | Quality         |
|------------|-----------------|
| 3.5–4.5    | Excellent       |
| 3.0–3.5    | Good            |
| 2.5–3.0    | Fair            |
| 2.0–2.5    | Poor            |
| < 2.0      | Very poor       |

| STOI       | Intelligibility |
|------------|-----------------|
| > 0.80     | High — STT should perform well |
| 0.65–0.80  | Moderate — elevated WER expected |
| < 0.65     | Low — engine failure likely regardless of NR |

---

## Key Analyses for Notebook

1. **WER heatmap** — engine × condition (3×5), with CI error bars
2. **S/D/I stacked bars** — per engine, per condition (failure mode fingerprint)
3. **NR delta waterfall** — % WER change from each NR state vs. raw, per engine
4. **PESQ vs. WER scatter** — does audio quality predict transcription failure?
5. **PESQ delta vs. WER delta** — does NR that improves audio quality also improve WER?
6. **Filler sensitivity** — bar chart of filler_sensitivity_delta per engine
7. **RTF comparison** — cloud vs. local inference cost/performance tradeoff

Analysis 2 (S/D/I) is the finding that demonstrates senior-level thinking.

---

## Confidence Interval Note (for notebook methodology section)

Bootstrap 95% CIs are used for interval estimation. Standard deviation is also
reported for interpretability, but not relied on due to the non-normal
distribution of WER.

WER values are bounded at [0, 1], often right-skewed in noisy conditions, and
may be multimodal across clip types. Bootstrap CI avoids assuming a normal
sampling distribution and provides a more robust interval estimate for this kind
of metric. Default configuration: 2000 resamples per bucket.

---

## Requirements

```text
jiwer>=3.0.3
pesq>=0.0.4
pystoi>=0.4.1
deepfilternet>=0.5.6
noisereduce>=3.0.0
numpy
scipy
pandas
matplotlib
seaborn
tqdm
jupyter
```
