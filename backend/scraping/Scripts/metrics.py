import logging
import pathlib

import jiwer as ji
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def calculate_metrics(real_path, asr_path):
    with open(real_path, "r") as f:
        human = f.read()

    with open(asr_path, "r") as f:
        asr = f.read()

    wer = ji.wer(human, asr)
    wil = ji.wil(human, asr)

    return {"wer": wer, "wil": wil}


def compare_models(subject_paths, transcriptions_path="../DB/Transcripciones"):
    """
    subject_names = ["actint/comp1-2023_01_medium.txt", ...]
    subject_paths are relative to transcriptions_path
    """
    transcriptions_path = pathlib.Path(transcriptions_path)
    data = {}

    for model in ["medium", "small", "base"]:
        for language in ["ad", "es"]:  # auto-detected, spanish
            for subject in subject_paths:
                real_path = transcriptions_path / language / f"{subject}_human.txt"
                asr_path = transcriptions_path / language / f"{subject}_{model}.txt"

                if not real_path.exists():
                    logging.info(f"File {real_path} not found. Skipping...")
                    continue
                if not asr_path.exists():
                    logging.info(f"File {asr_path} not found. Skipping...")
                    continue

                metrics = calculate_metrics(real_path, asr_path)
                data[model][subject][language] = metrics

    return data


def plot(data):
    """
    data = {
        "medium": {
            "subject1": {"wer": 0.2, "wil": 0.15},
            "subject2": {"wer": 0.3, "wil": 0.25}
        },
        "small": {
            "subject1": {"wer": 0.25, "wil": 0.2},
            "subject2": {"wer": 0.35, "wil": 0.3}
        },
        ...
    }
    """
    wer_data, wil_data = [], []

    for model, subjects in data.items():
        for subject, languages in subjects.items():
            for language, metrics in languages.items():
                wer_data.append(
                    {
                        "model": model,
                        "subject": f"{subject}_{language}",
                        "metric": "WER",
                        "value": metrics["wer"],
                    }
                )
                wil_data.append(
                    {
                        "model": model,
                        "subject": f"{subject}_{language}",
                        "metric": "WIL",
                        "value": metrics["wil"],
                    }
                )

    df = pd.DataFrame(wer_data + wil_data)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="subject", y="value", hue="metric", data=df, palette="muted", ci=None)
    plt.title(
        "Comparison of WER and WIL Across Models and Subjects (Auto-Detected vs Spanish)"
    )
    plt.ylabel("Error Rate")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()
