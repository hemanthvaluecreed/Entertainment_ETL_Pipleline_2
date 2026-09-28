import pandas as pd

df = pd.read_csv("data/processed/shows.csv")

print("Rows:", len(df))
print("Unique show IDs:", df["show_id"].nunique())
print(
    "Unique non-null schedule IDs:",
    df["schedule_id"].dropna().nunique()
)

print(
    "Duplicate show IDs:",
    df["show_id"].duplicated().sum()
)

print(
    "Duplicate schedule IDs:",
    df["schedule_id"].dropna().duplicated().sum()
)