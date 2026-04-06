import os
import pandas as pd
from openai import OpenAI

client = OpenAI()

INPUT_CSV = "data/test_transcripts.csv"
AUDIO_DIR = "data/audio/processed/noise"
OUTPUT_CSV = "benchmark_output/openai_noisy_results.csv"

def main():
    df = pd.read_csv(INPUT_CSV)

    results = []

    for _, row in df.iterrows():
        audio_file = row["path"].replace(".mp3", "_noisy.mp3")
        reference_text = row["sentence"]
        condition = row["condition"]

        audio_path = os.path.join(AUDIO_DIR, audio_file)

        if not os.path.exists(audio_path):
            print(f"[missing] {audio_path}")
            continue

        print(f"[transcribing] {audio_file}")

        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                file=f,
                model="gpt-4o-mini-transcribe"
            )

        hypothesis_text = transcript.text.strip()

        results.append({
            "audio_file": audio_file,
            "condition": condition,
            "engine": "openai_api",
            "engine_version": "gpt-4o-mini-transcribe",
            "reference_text": reference_text,
            "hypothesis_text": hypothesis_text,
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_CSV, index=False)

    print(f"[done] saved -> {OUTPUT_CSV}")

if __name__ == "__main__":
    main()