"""Gera um CSV parcial de pesquisa a partir de uma grade versionada no WORCAP."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--ref", default="origin/vermelho")
    parser.add_argument(
        "--artifact", default="models/pls_lagged_lstm_run1/sample_grids.npz"
    )
    parser.add_argument("--grid-index", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_repo = args.source_repo.resolve()
    blob = subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={source_repo.as_posix()}",
            "show",
            f"{args.ref}:{args.artifact}",
        ],
        cwd=source_repo,
    )
    archive = np.load(io.BytesIO(blob))
    target = str(archive["target_date"][args.grid_index])[:7].replace("-", "_")
    origin = str(archive["origin_date"][args.grid_index])[:7]
    prediction = archive["pred"][args.grid_index]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            [
                "id",
                "tp_mm_day",
                "status",
                "source_branch",
                "source_commit",
                "origin_month",
            ]
        )
        for lat_index, latitude in enumerate(archive["lat"]):
            for lon_index, longitude in enumerate(archive["lon"]):
                value = max(0.0, float(prediction[lat_index, lon_index]))
                writer.writerow(
                    [
                        f"{target}_{latitude:.2f}_{longitude:.2f}",
                        f"{value:.6f}",
                        "research_only_not_submittable",
                        "vermelho",
                        "62b3626",
                        origin,
                    ]
                )


if __name__ == "__main__":
    main()
