from pathlib import Path

EXPECTED_FILES = {
    "sample_submission.csv", "teste_features.nc", "treino_cloud_cover.nc",
    "treino_geopotential_850.nc", "treino_rel_hum_850.nc", "treino_shum_850.nc",
    "treino_surface_pressure.nc", "treino_t2.nc", "treino_temperature_850.nc",
    "treino_tp.nc", "treino_tp_alvo.nc", "treino_u_850.nc", "treino_v_850.nc",
}


def main() -> None:
    try:
        import kagglehub
    except ImportError as exc:
        raise SystemExit("Instale primeiro: pip install kagglehub") from exc
    downloaded = Path(
        kagglehub.competition_download(
            "previsao-climatica-de-precipitacao-sobre-a-america-do-sul"
        )
    )
    found = {item.name for item in downloaded.rglob("*") if item.is_file()}
    missing = sorted(EXPECTED_FILES - found)
    if missing:
        raise SystemExit(f"Download incompleto. Arquivos ausentes: {', '.join(missing)}")
    print(f"Dataset validado em: {downloaded}")
    print("13 arquivos oficiais encontrados.")


if __name__ == "__main__":
    main()
