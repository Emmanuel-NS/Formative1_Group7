import pandas as pd

def generate_statistical_summary(file_path="data/salesdaily.csv"):
    """Profiles right-skewed distribution metrics for the target and auxiliary features."""
    try:
        df = pd.read_csv(file_path)
        atc_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']
        
        if all(col in df.columns for col in atc_cols):
            summary = df[atc_cols].describe().T[['mean', 'std', 'min', '50%', 'max']]
            print("--- Descriptive Summary Statistics ---")
            print(summary.to_string())
        else:
            print("Error: Matrix columns mismatch original ATC classifications.")
    except Exception as e:
        print(f"Profiling aborted: {e}")

if __name__ == "__main__":
    generate_statistical_summary()