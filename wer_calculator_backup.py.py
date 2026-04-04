"""
wer_calculator.py  (v4)
STT Benchmark — Core Metrics & Data Capture Module
Sean Tallman | AI Audio Specialist Portfolio

Changes in v4:
  - Bootstrap confidence intervals on WER/CER/RTF with NumPy RNG
  - Standard deviation reported for interpretability, but not relied on for interval estimation
  - REMOVE_FILLERS flag: runs WER both ways and reports normalization sensitivity
  - S/D/I breakdown surfaced as headline fields in compute_summary
  - Failure mode classification added from dominant S/D/I pattern
  - Reproducibility note embedded in module docstring

Reproducibility statement:
    This benchmark is fully reproducible using open-source tools.
    The automated pipeline (raw / oss_light / oss_heavy NR states) requires
    only pip-installable packages. iZotope RX results (rx_light / rx_heavy)
    are included as an industry comparison — they are not required to replicate
    core findings. All RX settings are documented in rx_settings.md.

Metrics per transcription attempt:
  - WER         : Word Error Rate               (primary STT metric)
  - WER_raw     : WER without filler removal    (normalization sensitivity check)
  - CER         : Character Error Rate          (secondary STT metric)
  - MER / WIL / WIP : jiwer companion metrics
  - S / D / I   : Substitution / Deletion / Insertion counts  (error type analysis)
  - RTF         : Real-Time Factor              (latency / audio_duration)
  - PESQ        : Perceptual Evaluation of Speech Quality  (ITU-T P.862)
  - STOI        : Short-Time Objective Intelligibility

Install:
    pip install jiwer pesq pystoi deepfilternet noisereduce numpy scipy
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Callable, Optional

import numpy as np

try:
    import jiwer
except ImportError as exc:
    raise ImportError("pip install jiwer") from exc

try:
    from pesq import pesq as pesq_score
    PESQ_AVAILABLE = True
except ImportError:
    PESQ_AVAILABLE = False
    print("[warn] pesq not installed — PESQ scores will be None. pip install pesq")

try:
    from pystoi import stoi as stoi_score
    STOI_AVAILABLE = True
except ImportError:
    STOI_AVAILABLE = False
    print("[warn] pystoi not installed — STOI scores will be None. pip install pystoi")

try:
    from scipy.io import wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("[warn] scipy not installed — audio loading unavailable. pip install scipy")


# ===========================================================================
# Normalization Configuration
# ===========================================================================

REMOVE_FILLERS: bool = True
FILLER_PATTERN = re.compile(r"\b(um+|uh+|hmm+|mm+|mhm+|erm+)\b", re.IGNORECASE)


# ===========================================================================
# Data Structures
# ===========================================================================

NR_STATES = {
    "raw": "No preprocessing — control condition",
    "oss_light": "DeepFilterNet default — open source, light processing",
    "oss_heavy": "noisereduce aggressive — open source, heavy spectral subtraction",
    "rx_light": "iZotope RX — NR + gentle de-reverb (manual, settings documented in rx_settings.md)",
    "rx_heavy": "iZotope RX — NR + Dialogue Isolation (manual, settings documented in rx_settings.md)",
}


@dataclass
class AudioCondition:
    condition_id: str
    noise_type: Optional[str]
    snr_db: Optional[float]
    reverb_rt60: Optional[float]
    sample_rate_hz: int
    bit_depth: int
    channel: str
    codec: str
    notes: Optional[str] = None


@dataclass
class NRProcessingConfig:
    state: str
    tool: str
    tool_version: str
    params: dict
    automated: bool
    processing_latency_sec: Optional[float] = None


@dataclass
class SubjectiveRating:
    intelligibility: int
    noise_intrusiveness: int
    overall_quality: int
    rater_notes: Optional[str] = None

    def composite(self) -> float:
        return round(
            (self.intelligibility * 0.5)
            + (self.noise_intrusiveness * 0.25)
            + (self.overall_quality * 0.25),
            2,
        )


@dataclass
class TranscriptionResult:
    run_id: str
    audio_file: str
    condition_id: str
    nr_state: str
    engine: str
    engine_version: str
    engine_config: dict
    reference_text: str
    hypothesis_text: str
    hypothesis_normalized: str
    wer: float
    wer_with_fillers: float
    cer: float
    mer: float
    wil: float
    wip: float
    substitutions: int
    deletions: int
    insertions: int
    substitution_rate: float
    deletion_rate: float
    insertion_rate: float
    reference_word_count: int
    hypothesis_word_count: int
    audio_duration_sec: float
    transcription_latency_sec: float
    rtf: float
    pesq_wb: Optional[float]
    pesq_nb: Optional[float]
    stoi: Optional[float]
    subjective: Optional[dict]
    timestamp_utc: str
    filler_removal_applied: bool
    confidence_score: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class BenchmarkRun:
    run_id: str
    description: str
    created_utc: str
    engines_tested: list
    conditions_tested: list
    nr_states_tested: list
    normalization_config: dict
    total_clips: int
    total_records: int
    results: list = field(default_factory=list)
    summary_stats: dict = field(default_factory=dict)


# ===========================================================================
# Text Normalization
# ===========================================================================

def normalize_text(text: str, remove_fillers: bool = REMOVE_FILLERS) -> str:
    """
    Normalize a transcript for WER/CER comparison.

    The remove_fillers parameter is applied symmetrically to both reference
    and hypothesis. Running WER both ways exposes normalization sensitivity.
    """
    text = re.sub(r"\[?speaker[\s_]?\w+\]?:?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\w+[\s_]?\d+\s*:", "", text)
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", "").replace("\u201d", "")

    if remove_fillers:
        text = FILLER_PATTERN.sub("", text)

    transforms = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.ExpandCommonEnglishContractions(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
    ])
    return transforms(text)


# ===========================================================================
# Core STT Metrics
# ===========================================================================

def calculate_wer(
    reference: str,
    hypothesis: str,
    remove_fillers: bool = REMOVE_FILLERS,
) -> dict:
    """
    Compute WER and companion metrics.

    Returns primary metrics using the requested normalization mode and also
    reports WER without filler removal as a sensitivity check.
    """
    ref_normalized = normalize_text(reference, remove_fillers=remove_fillers)
    hyp_normalized = normalize_text(hypothesis, remove_fillers=remove_fillers)
    ref_with_fillers = normalize_text(reference, remove_fillers=False)
    hyp_with_fillers = normalize_text(hypothesis, remove_fillers=False)

    if not ref_normalized.strip():
        raise ValueError("Reference transcript is empty after normalization.")

    def _compute(ref: str, hyp: str) -> dict:
        if not hyp.strip():
            n = len(ref.split())
            return {
                "wer": 1.0,
                "mer": 1.0,
                "wil": 1.0,
                "wip": 0.0,
                "substitutions": 0,
                "deletions": n,
                "insertions": 0,
                "ref_wc": n,
                "hyp_wc": 0,
            }
        m = jiwer.compute_measures(ref, hyp)
        return {
            "wer": round(m["wer"], 6),
            "mer": round(m["mer"], 6),
            "wil": round(m["wil"], 6),
            "wip": round(m["wip"], 6),
            "substitutions": m["substitutions"],
            "deletions": m["deletions"],
            "insertions": m["insertions"],
            "ref_wc": len(ref.split()),
            "hyp_wc": len(hyp.split()),
        }

    primary = _compute(ref_normalized, hyp_normalized)
    filler = _compute(ref_with_fillers, hyp_with_fillers)
    n = primary["ref_wc"] if primary["ref_wc"] > 0 else 1

    return {
        "wer": primary["wer"],
        "mer": primary["mer"],
        "wil": primary["wil"],
        "wip": primary["wip"],
        "substitutions": primary["substitutions"],
        "deletions": primary["deletions"],
        "insertions": primary["insertions"],
        "substitution_rate": round(primary["substitutions"] / n, 6),
        "deletion_rate": round(primary["deletions"] / n, 6),
        "insertion_rate": round(primary["insertions"] / n, 6),
        "reference_word_count": primary["ref_wc"],
        "hypothesis_word_count": primary["hyp_wc"],
        "reference_normalized": ref_normalized,
        "hypothesis_normalized": hyp_normalized,
        "wer_with_fillers": filler["wer"],
    }


def calculate_cer(
    reference: str,
    hypothesis: str,
    remove_fillers: bool = REMOVE_FILLERS,
) -> float:
    ref = normalize_text(reference, remove_fillers=remove_fillers)
    hyp = normalize_text(hypothesis, remove_fillers=remove_fillers)
    if not ref.strip():
        raise ValueError("Reference is empty after normalization.")
    if not hyp.strip():
        return 1.0
    return round(jiwer.cer(ref, hyp), 6)


def calculate_rtf(latency_sec: float, duration_sec: float) -> float:
    if duration_sec <= 0:
        raise ValueError("duration_sec must be > 0")
    return round(latency_sec / duration_sec, 4)


# ===========================================================================
# Bootstrap Confidence Intervals
# ===========================================================================

def bootstrap_ci(
    values: list,
    stat_fn: Optional[Callable[[np.ndarray], float]] = None,
    n_bootstrap: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> dict:
    """
    Bootstrap confidence interval for any statistic on a sample.

    WER is non-normally distributed (bounded, skewed), so standard deviation
    alone is insufficient for reliable interval estimation. Bootstrap confidence
    intervals are used because they make no strong distributional assumptions.
    Standard deviation is still reported separately for interpretability.
    """
    if not values:
        return {
            "mean": None,
            "ci_lower": None,
            "ci_upper": None,
            "ci_width": None,
            "n": 0,
            "ci_level": ci,
        }

    arr = np.asarray(values, dtype=float)
    if stat_fn is None:
        stat_fn = np.mean

    rng = np.random.default_rng(seed)
    n = len(arr)
    boot_stats = np.empty(n_bootstrap, dtype=float)

    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = float(stat_fn(sample))

    alpha = 1 - ci
    ci_lower = round(float(np.percentile(boot_stats, 100 * (alpha / 2))), 4)
    ci_upper = round(float(np.percentile(boot_stats, 100 * (1 - alpha / 2))), 4)
    observed = round(float(stat_fn(arr)), 4)

    return {
        "mean": observed,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": round(ci_upper - ci_lower, 4),
        "n": n,
        "ci_level": ci,
    }


# ===========================================================================
# Perceptual Audio Quality Metrics
# ===========================================================================

def load_wav_mono(path: str, target_sr: int = 16000) -> tuple:
    if not SCIPY_AVAILABLE:
        raise RuntimeError("pip install scipy")
    sr, data = wavfile.read(path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    else:
        data = data.astype(np.float32)
    if data.ndim == 2:
        data = data.mean(axis=1)
    if sr != target_sr:
        print(f"[warn] Expected {target_sr}Hz, got {sr}Hz for {path}. Resample before computing PESQ/STOI.")
    return data, sr


def calculate_pesq(reference_wav: str, degraded_wav: str, sample_rate: int = 16000) -> dict:
    """
    Compute PESQ (Perceptual Evaluation of Speech Quality) — ITU-T P.862.

    We analyze correlation, not causation. Higher PESQ does not guarantee
    lower WER.
    """
    if not PESQ_AVAILABLE:
        return {"pesq_wb": None, "pesq_nb": None}
    try:
        ref, _ = load_wav_mono(reference_wav, sample_rate)
        deg, _ = load_wav_mono(degraded_wav, sample_rate)
        min_len = min(len(ref), len(deg))
        ref, deg = ref[:min_len], deg[:min_len]
        wb = round(float(pesq_score(sample_rate, ref, deg, "wb")), 4) if sample_rate == 16000 else None
        nb = round(float(pesq_score(sample_rate, ref, deg, "nb")), 4)
        return {"pesq_wb": wb, "pesq_nb": nb}
    except Exception as exc:
        print(f"[error] PESQ: {exc}")
        return {"pesq_wb": None, "pesq_nb": None}


def calculate_stoi(
    reference_wav: str,
    degraded_wav: str,
    sample_rate: int = 16000,
    extended: bool = False,
) -> Optional[float]:
    if not STOI_AVAILABLE:
        return None
    try:
        ref, _ = load_wav_mono(reference_wav, sample_rate)
        deg, _ = load_wav_mono(degraded_wav, sample_rate)
        min_len = min(len(ref), len(deg))
        ref, deg = ref[:min_len], deg[:min_len]
        return round(float(stoi_score(ref, deg, sample_rate, extended=extended)), 4)
    except Exception as exc:
        print(f"[error] STOI: {exc}")
        return None


# ===========================================================================
# Result Builder
# ===========================================================================

def build_result(
    run_id: str,
    audio_file: str,
    condition: AudioCondition,
    nr_config: NRProcessingConfig,
    engine: str,
    engine_version: str,
    engine_config: dict,
    reference_text: str,
    hypothesis_text: str,
    audio_duration_sec: float,
    transcription_latency_sec: float,
    reference_wav: Optional[str] = None,
    degraded_wav: Optional[str] = None,
    subjective: Optional[SubjectiveRating] = None,
    confidence_score: Optional[float] = None,
    notes: Optional[str] = None,
) -> TranscriptionResult:
    wer_metrics = calculate_wer(reference_text, hypothesis_text)
    cer = calculate_cer(reference_text, hypothesis_text)
    rtf = calculate_rtf(transcription_latency_sec, audio_duration_sec)

    pesq_scores = {"pesq_wb": None, "pesq_nb": None}
    stoi_val = None
    if reference_wav and degraded_wav:
        pesq_scores = calculate_pesq(reference_wav, degraded_wav)
        stoi_val = calculate_stoi(reference_wav, degraded_wav)

    return TranscriptionResult(
        run_id=run_id,
        audio_file=audio_file,
        condition_id=condition.condition_id,
        nr_state=nr_config.state,
        engine=engine,
        engine_version=engine_version,
        engine_config=engine_config,
        reference_text=reference_text,
        hypothesis_text=hypothesis_text,
        hypothesis_normalized=wer_metrics["hypothesis_normalized"],
        wer=wer_metrics["wer"],
        wer_with_fillers=wer_metrics["wer_with_fillers"],
        cer=cer,
        mer=wer_metrics["mer"],
        wil=wer_metrics["wil"],
        wip=wer_metrics["wip"],
        substitutions=wer_metrics["substitutions"],
        deletions=wer_metrics["deletions"],
        insertions=wer_metrics["insertions"],
        substitution_rate=wer_metrics["substitution_rate"],
        deletion_rate=wer_metrics["deletion_rate"],
        insertion_rate=wer_metrics["insertion_rate"],
        reference_word_count=wer_metrics["reference_word_count"],
        hypothesis_word_count=wer_metrics["hypothesis_word_count"],
        audio_duration_sec=audio_duration_sec,
        transcription_latency_sec=transcription_latency_sec,
        rtf=rtf,
        pesq_wb=pesq_scores["pesq_wb"],
        pesq_nb=pesq_scores["pesq_nb"],
        stoi=stoi_val,
        subjective=asdict(subjective) if subjective else None,
        timestamp_utc=datetime.utcnow().isoformat() + "Z",
        filler_removal_applied=REMOVE_FILLERS,
        confidence_score=confidence_score,
        notes=notes,
    )


# ===========================================================================
# Summary Statistics
# ===========================================================================

def classify_failure_mode(sub: Optional[float], dele: Optional[float], ins: Optional[float]) -> Optional[str]:
    if sub is None or dele is None or ins is None:
        return None
    if dele > sub and dele > ins:
        return "deletion_dominant"
    if sub > dele and sub > ins:
        return "substitution_dominant"
    if ins > sub and ins > dele:
        return "insertion_dominant"
    return "mixed"


def compute_summary(
    results: list,
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
) -> dict:
    """
    Summary statistics bucketed by engine x condition x nr_state.

    Bootstrap confidence intervals are used for interval estimation. Standard
    deviation is also reported for interpretability, but not relied on due to
    the non-normal distribution of WER.
    """
    from collections import defaultdict

    buckets = defaultdict(list)
    for r in results:
        buckets[(r.engine, r.condition_id, r.nr_state)].append(r)

    def safe_mean(vals: list[float]) -> Optional[float]:
        return round(float(np.mean(vals)), 4) if vals else None

    def safe_median(vals: list[float]) -> Optional[float]:
        return round(float(np.median(vals)), 4) if vals else None

    def safe_std(vals: list[float]) -> Optional[float]:
        return round(float(np.std(vals)), 4) if vals else None

    summary = {}
    for (engine, condition_id, nr_state), records in sorted(buckets.items()):
        key = f"{engine}__{condition_id}__{nr_state}"
        n = len(records)

        wers = [r.wer for r in records]
        wers_f = [r.wer_with_fillers for r in records]
        cers = [r.cer for r in records]
        rtfs = [r.rtf for r in records]
        pesqs = [r.pesq_wb for r in records if r.pesq_wb is not None]
        stois = [r.stoi for r in records if r.stoi is not None]
        sub_rates = [r.substitution_rate for r in records]
        del_rates = [r.deletion_rate for r in records]
        ins_rates = [r.insertion_rate for r in records]

        wer_ci = bootstrap_ci(wers, n_bootstrap=n_bootstrap, ci=ci_level)
        cer_ci = bootstrap_ci(cers, n_bootstrap=n_bootstrap, ci=ci_level)
        rtf_ci = bootstrap_ci(rtfs, n_bootstrap=n_bootstrap, ci=ci_level)

        mean_sub = safe_mean(sub_rates)
        mean_del = safe_mean(del_rates)
        mean_ins = safe_mean(ins_rates)

        summary[key] = {
            "engine": engine,
            "condition_id": condition_id,
            "nr_state": nr_state,
            "n_samples": n,
            "mean_wer": wer_ci["mean"],
            "median_wer": safe_median(wers),
            "std_wer": safe_std(wers),
            "wer_ci_lower": wer_ci["ci_lower"],
            "wer_ci_upper": wer_ci["ci_upper"],
            "wer_ci_width": wer_ci["ci_width"],
            "min_wer": round(min(wers), 4),
            "max_wer": round(max(wers), 4),
            "mean_wer_with_fillers": safe_mean(wers_f),
            "filler_sensitivity_delta": round((safe_mean(wers_f) or 0) - (wer_ci["mean"] or 0), 4),
            "mean_cer": cer_ci["mean"],
            "median_cer": safe_median(cers),
            "std_cer": safe_std(cers),
            "cer_ci_lower": cer_ci["ci_lower"],
            "cer_ci_upper": cer_ci["ci_upper"],
            "mean_substitution_rate": mean_sub,
            "mean_deletion_rate": mean_del,
            "mean_insertion_rate": mean_ins,
            "failure_mode": classify_failure_mode(mean_sub, mean_del, mean_ins),
            "total_substitutions": sum(r.substitutions for r in records),
            "total_deletions": sum(r.deletions for r in records),
            "total_insertions": sum(r.insertions for r in records),
            "mean_rtf": rtf_ci["mean"],
            "median_rtf": safe_median(rtfs),
            "std_rtf": safe_std(rtfs),
            "rtf_ci_lower": rtf_ci["ci_lower"],
            "rtf_ci_upper": rtf_ci["ci_upper"],
            "mean_pesq_wb": safe_mean(pesqs) if pesqs else None,
            "mean_stoi": safe_mean(stois) if stois else None,
            "ci_level": ci_level,
            "n_bootstrap": n_bootstrap,
        }

    return summary


def compute_nr_delta(summary: dict) -> dict:
    baselines = {}
    for _, stats in summary.items():
        if stats["nr_state"] == "raw":
            baselines[(stats["engine"], stats["condition_id"])] = stats["mean_wer"]

    deltas = {}
    for key, stats in summary.items():
        if stats["nr_state"] == "raw":
            continue
        baseline = baselines.get((stats["engine"], stats["condition_id"]))
        if baseline is None or stats["mean_wer"] is None or baseline == 0:
            continue
        delta_pct = round((baseline - stats["mean_wer"]) / baseline * 100, 2)
        deltas[key] = {
            **stats,
            "baseline_wer": baseline,
            "wer_delta_pct": delta_pct,
            "improved": delta_pct > 0,
        }
    return deltas


def print_sdi_report(summary: dict) -> None:
    print("\n" + "=" * 88)
    print("ERROR TYPE BREAKDOWN (S / D / I rates per 100 reference words)")
    print("=" * 88)
    print(f"{'Engine':<14} {'Condition':<22} {'NR':<12} {'Sub%':>6} {'Del%':>6} {'Ins%':>6} {'Mode':>22}")
    print("-" * 88)
    for _, s in sorted(summary.items()):
        sub_pct = round((s["mean_substitution_rate"] or 0) * 100, 1)
        del_pct = round((s["mean_deletion_rate"] or 0) * 100, 1)
        ins_pct = round((s["mean_insertion_rate"] or 0) * 100, 1)
        print(
            f"{s['engine']:<14} {s['condition_id']:<22} {s['nr_state']:<12} "
            f"{sub_pct:>6.1f} {del_pct:>6.1f} {ins_pct:>6.1f} {s['failure_mode']:>22}"
        )


# ===========================================================================
# I/O
# ===========================================================================

def save_results_json(run: BenchmarkRun, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(run), f, indent=2, ensure_ascii=False)
    print(f"[ok] JSON saved      -> {output_path}")


def save_results_csv(results: list, output_path: str) -> None:
    if not results:
        return
    rows = []
    for r in results:
        row = asdict(r)
        row["engine_config"] = json.dumps(row["engine_config"])
        row["subjective"] = json.dumps(row["subjective"]) if row["subjective"] else ""
        rows.append(row)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] CSV saved       -> {output_path}")


def save_nr_delta_csv(deltas: dict, output_path: str) -> None:
    if not deltas:
        return
    rows = list(deltas.values())
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] NR delta saved  -> {output_path}")


def save_summary_csv(summary: dict, output_path: str) -> None:
    if not summary:
        return
    rows = list(summary.values())
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] Summary saved   -> {output_path}")


# ===========================================================================
# Smoke Test
# ===========================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("STT Benchmark v4 — Smoke Test  |  Sean Tallman")
    print(f"    Filler removal: {REMOVE_FILLERS}")
    print(f"    Bootstrap CI:   95%, 2000 resamples")
    print("=" * 65)

    condition = AudioCondition(
        condition_id="reverb_1.2s",
        noise_type=None,
        snr_db=None,
        reverb_rt60=1.2,
        sample_rate_hz=16000,
        bit_depth=16,
        channel="mono",
        codec="wav",
        notes="Medium reverb — RT60 = 1.2s",
    )

    nr_configs = {
        "raw": NRProcessingConfig(state="raw", tool="none", tool_version="n/a", params={}, automated=True),
        "oss_light": NRProcessingConfig(
            state="oss_light",
            tool="deepfilternet",
            tool_version="0.5.6",
            params={"atten_lim_db": 100, "post_filter": True},
            automated=True,
            processing_latency_sec=0.31,
        ),
        "rx_light": NRProcessingConfig(
            state="rx_light",
            tool="izotope_rx",
            tool_version="RX11",
            params={"nr_amount": 6, "de_reverb": 4, "dialogue_isolation": False},
            automated=False,
        ),
    }

    reference = "The session was recorded in a reverberant tracking room with live drums"
    hypotheses = {
        "raw": {
            "whisper": [
                ("the session was recorded in a reverberant tracking room with live rooms", 2.10),
                ("the session recorded in a reverberant tracking room live drums", 2.15),
                ("the session was recorded in reverberant tracking room with live drums", 2.08),
            ],
            "google_stt": [
                ("session was recorded reverberant tracking room live drums", 0.74),
                ("session recorded reverberant tracking room live drums", 0.77),
                ("the session was reverberant tracking room live drums", 0.72),
            ],
            "assemblyai": [
                ("the session was recorded in a reverberant tracking room with live drums", 1.05),
                ("the session was recorded in a reverberant tracking room with live drums", 1.07),
                ("the session was recorded in reverberant tracking room with live drums", 1.03),
            ],
        },
        "oss_light": {
            "whisper": [
                ("the session was recorded in a reverberant tracking room with live drums", 1.95),
                ("the session was recorded in a reverberant tracking room with live drums", 1.98),
                ("the session was recorded in a reverberant tracking room with live drums", 1.93),
            ],
            "google_stt": [
                ("the session was recorded in a reverberant tracking room with live drums", 0.71),
                ("the session was recorded in a reverberant tracking room with live drums", 0.73),
                ("the session was recorded in a reverberant tracking room with live drums", 0.70),
            ],
            "assemblyai": [
                ("the session was recorded in a reverberant tracking room with live drums", 0.98),
                ("the session was recorded in a reverberant tracking room with live drums", 1.01),
                ("the session was recorded in a reverberant tracking room with live drums", 0.97),
            ],
        },
        "rx_light": {
            "whisper": [
                ("the session was recorded in a reverberant tracking room with live drums", 1.88),
                ("the session was recorded in a reverberant tracking room with live drums", 1.91),
                ("the session was recorded in a reverberant tracking room with live drums", 1.87),
            ],
            "google_stt": [
                ("the session was recorded in a reverberant tracking room with live drums", 0.69),
                ("the session was recorded in a reverberant tracking room with live drums", 0.71),
                ("the session was recorded in a reverberant tracking room with live drums", 0.68),
            ],
            "assemblyai": [
                ("the session was recorded in a reverberant tracking room with live drums", 0.95),
                ("the session was recorded in a reverberant tracking room with live drums", 0.97),
                ("the session was recorded in a reverberant tracking room with live drums", 0.94),
            ],
        },
    }

    run_id = f"run_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"
    results = []
    versions = {"whisper": "large-v3", "google_stt": "chirp_2", "assemblyai": "best"}

    for nr_state, engines in hypotheses.items():
        for engine, clips in engines.items():
            for i, (hyp_text, latency) in enumerate(clips):
                results.append(
                    build_result(
                        run_id=run_id,
                        audio_file=f"clip_{i+1:03d}_reverb_1.2s.wav",
                        condition=condition,
                        nr_config=nr_configs[nr_state],
                        engine=engine,
                        engine_version=versions[engine],
                        engine_config={"language": "en-US"},
                        reference_text=reference,
                        hypothesis_text=hyp_text,
                        audio_duration_sec=5.1,
                        transcription_latency_sec=latency,
                    )
                )

    summary = compute_summary(results)
    deltas = compute_nr_delta(summary)

    print("\n--- WER SUMMARY (95% Bootstrap CI) ---")
    for _, s in sorted(summary.items()):
        print(
            f"  {s['engine']:12s} | {s['nr_state']:12s} | "
            f"WER {s['mean_wer']:.4f} [{s['wer_ci_lower']:.4f}–{s['wer_ci_upper']:.4f}]  "
            f"median: {s['median_wer']:.4f} std: {s['std_wer']:.4f}  "
            f"filler_delta: {s['filler_sensitivity_delta']:+.4f}"
        )

    print_sdi_report(summary)

    print("\n--- NR PREPROCESSING DELTA ---")
    for _, d in sorted(deltas.items()):
        arrow = "+" if d["improved"] else "-"
        print(f"  [{arrow}] {d['engine']:12s} | {d['nr_state']:12s} | delta: {d['wer_delta_pct']:+.1f}%")

    run = BenchmarkRun(
        run_id=run_id,
        description="Smoke test v4 — reverb 1.2s, 3 NR states x 3 engines x 3 clips",
        created_utc=datetime.utcnow().isoformat() + "Z",
        engines_tested=["whisper", "google_stt", "assemblyai"],
        conditions_tested=["reverb_1.2s"],
        nr_states_tested=list(nr_configs.keys()),
        normalization_config={
            "remove_fillers": REMOVE_FILLERS,
            "filler_pattern": FILLER_PATTERN.pattern,
            "note": "WER computed both with and without filler removal. See wer_with_fillers and filler_sensitivity_delta fields.",
        },
        total_clips=3,
        total_records=len(results),
        results=[asdict(r) for r in results],
        summary_stats=summary,
    )

    os.makedirs("benchmark_output", exist_ok=True)
    save_results_json(run, f"benchmark_output/{run_id}.json")
    save_results_csv(results, f"benchmark_output/{run_id}_results.csv")
    save_nr_delta_csv(deltas, f"benchmark_output/{run_id}_nr_delta.csv")
    save_summary_csv(summary, f"benchmark_output/{run_id}_summary.csv")
