import pandas as pd

INPUT_CSV = "/Users/seantallman/Downloads/commonvoice-v24_en-AU/commonvoice-v24_en-AU.csv"
OUTPUT_CSV = "data/test_transcripts.csv"
NUM_CLIPS = 12

def main():
    df = pd.read_csv(INPUT_CSV)

    df = df.dropna(subset=["path", "sentence"])
    df = df[df["sentence"].str.strip() != ""]

    if "duration_ms" in df.columns:
        df = df[df["duration_ms"] < 12000]

    df = df.head(NUM_CLIPS)

    clean_df = pd.DataFrame({
        "path": df["path"],
        "sentence": df["sentence"],
        "condition": "clean"
    })

    clean_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Created {OUTPUT_CSV} with {len(clean_df)} clips")

if __name__ == "__main__":
    main()
