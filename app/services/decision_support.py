from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "decision_support_catalog.json"

SECTORS = {
    "agriculture": {
        "label": "Agricultura e plantio",
        "description": "Solo, manejo e janela de campo",
    },
    "agribusiness": {
        "label": "Agronegócio e logística",
        "description": "Operação, armazenagem e acesso",
    },
    "risk-areas": {"label": "Áreas de risco", "description": "Preparação comunitária e alertas"},
    "hydropower": {"label": "Hidroenergia", "description": "Bacias, afluências e reservatórios"},
    "tourism": {
        "label": "Turismo, rios e cataratas",
        "description": "Acesso, experiência e segurança",
    },
    "water-management": {
        "label": "Água e cidades",
        "description": "Abastecimento e drenagem urbana",
    },
}

REGIME_LABELS = {
    "very_low": "muito pouca chuva",
    "low": "pouca chuva",
    "moderate": "chuva moderada",
    "high": "chuva elevada",
    "very_high": "chuva muito elevada",
}
CLASS_LABELS = {
    "below_historical": "abaixo da faixa histórica",
    "within_historical": "dentro da faixa histórica",
    "above_historical": "acima da faixa histórica",
}


@lru_cache
def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _guidance(sector: str, wet: bool, dry: bool) -> dict:
    common = "Cruze este cenário mensal com alertas e dados locais antes de decidir."
    if sector == "agriculture":
        actions = (
            [
                "Revise drenagem, acesso às áreas e janela de operações.",
                "Monitore pressão de doenças favorecidas por umidade.",
                "Proteja solo exposto contra erosão.",
            ]
            if wet
            else [
                "Confira umidade do solo e capacidade de irrigação.",
                "Ajuste a janela de plantio à cultura, ao solo e à previsão curta.",
                "Planeje conservação de água e cobertura do solo.",
            ]
            if dry
            else [
                "Mantenha monitoramento de solo e previsão de curto prazo.",
                "Planeje operações considerando a distribuição da chuva no mês.",
                "Valide o manejo com assistência agronômica local.",
            ]
        )
        limitation = (
            "Não é recomendação de cultura, plantio ou defensivo: faltam solo, "
            "cultivar, estágio fenológico e chuva diária."
        )
    elif sector == "agribusiness":
        actions = (
            [
                "Crie folga para acesso em estradas rurais e pátios.",
                "Revise proteção de carga e controle de umidade no armazenamento.",
                "Mapeie fornecedores e rotas alternativas.",
            ]
            if wet
            else [
                "Antecipe demanda por irrigação e insumos hídricos.",
                "Reforce prevenção de poeira e incêndio onde aplicável.",
                "Revise estoques e rotas expostos à baixa disponibilidade de água.",
            ]
            if dry
            else [
                "Combine o cenário com calendário de colheita e transporte.",
                "Monitore gargalos logísticos locais.",
                "Atualize o plano conforme previsões semanais.",
            ]
        )
        limitation = (
            "O cenário não prevê produtividade, preço, condição de estrada nem demanda logística."
        )
    elif sector == "risk-areas":
        actions = (
            [
                "Ative o recebimento de alertas oficiais da Defesa Civil.",
                "Observe drenagem, encostas, rachaduras e mudanças em cursos d'água.",
                "Revise contatos, rotas e ponto de encontro familiar.",
            ]
            if wet
            else [
                "Mantenha alertas oficiais ativos: pouca chuva mensal não elimina "
                "eventos intensos.",
                "Evite descarte que obstrua drenagem e canais.",
                "Conheça rotas seguras e contatos da Defesa Civil local.",
            ]
        )
        limitation = (
            "Não é alerta, mapa de risco nem ordem de evacuação. Em emergência, "
            "siga exclusivamente Defesa Civil e autoridades locais."
        )
    elif sector == "hydropower":
        actions = (
            [
                "Acompanhe afluências, níveis e regras de operação do reservatório.",
                "Cruze chuva prevista com saturação do solo e tempo de resposta da bacia.",
                "Revise cenários operativos com dados de ANA e ONS.",
            ]
            if wet
            else [
                "Monitore disponibilidade hídrica e afluências observadas.",
                "Teste cenários de armazenamento e atendimento à demanda.",
                "Cruze o sinal com previsões sazonais e operação coordenada.",
            ]
            if dry
            else [
                "Acompanhe afluências e armazenamento em cada bacia.",
                "Atualize cenários com chuva observada e prevista.",
                "Use dados operativos de ANA e ONS para qualquer decisão.",
            ]
        )
        limitation = (
            "Precipitação em um ponto não equivale a vazão, energia afluente ou "
            "nível de reservatório."
        )
    elif sector == "tourism":
        actions = (
            [
                "Confira condições de trilhas, acessos e travessias com operadores locais.",
                "Monitore alertas de cheias rápidas e interdições.",
                "Comunique alternativas e política de remarcação ao visitante.",
            ]
            if wet
            else [
                "Consulte nível e vazão observados antes de prometer condições de rios "
                "e cataratas.",
                "Planeje comunicação sobre calor, água e exposição solar.",
                "Mantenha alternativas de roteiro para baixa vazão.",
            ]
            if dry
            else [
                "Cheque nível dos rios, acessos e previsão diária perto da visita.",
                "Comunique incerteza e alternativas de roteiro.",
                "Acompanhe avisos de parques e autoridades locais.",
            ]
        )
        limitation = (
            "Chuva mensal não determina sozinha nível de rio, vazão de catarata, "
            "balneabilidade ou segurança de trilhas."
        )
    else:
        actions = (
            [
                "Revise limpeza e capacidade de drenagem.",
                "Monitore pontos de alagamento e canais.",
                "Integre o cenário ao plano de contingência municipal.",
            ]
            if wet
            else [
                "Reforce comunicação de uso eficiente da água.",
                "Acompanhe mananciais, reservatórios e demanda.",
                "Revise prioridades de abastecimento com dados locais.",
            ]
            if dry
            else [
                "Acompanhe drenagem, mananciais e demanda.",
                "Atualize planos com observações e previsão curta.",
                "Comunique incerteza e fontes oficiais.",
            ]
        )
        limitation = (
            "Não substitui balanço hídrico, modelagem de drenagem ou decisão da "
            "autoridade responsável."
        )
    return {
        "actions": actions,
        "watch": [
            "previsão diária e alertas oficiais",
            "chuva observada e sua distribuição",
            "indicadores locais do setor",
        ],
        "limitation": limitation,
        "safety_note": common,
    }


def options() -> dict:
    catalog = load_catalog()
    first = next(iter(catalog["locations"].values()))
    return {
        "sectors": [{"id": key, **value} for key, value in SECTORS.items()],
        "locations": [
            {"id": key, "name": value["name"], "country": value["country"]}
            for key, value in catalog["locations"].items()
        ],
        "target_months": list(first["predictions"]),
        "default_sector": "agriculture",
        "default_target_month": "2024-12",
    }


def scenario(location_id: str, target_month: str, sector: str) -> dict:
    catalog = load_catalog()
    if location_id not in catalog["locations"]:
        raise ValueError("Localidade não reconhecida.")
    if sector not in SECTORS:
        raise ValueError("Setor não reconhecido.")
    location = catalog["locations"][location_id]
    if target_month not in location["predictions"]:
        raise ValueError("Mês-alvo não disponível neste catálogo.")
    prediction = location["predictions"][target_month]
    wet = prediction["rainfall_regime"] in {"high", "very_high"}
    dry = prediction["rainfall_regime"] in {"very_low", "low"}
    guidance = _guidance(sector, wet, dry)
    return {
        "location_id": location_id,
        "location": {
            "name": location["name"],
            "country": location["country"],
            "grid_latitude": location["grid_latitude"],
            "grid_longitude": location["grid_longitude"],
        },
        "target_month": target_month,
        "sector": {"id": sector, **SECTORS[sector]},
        "scenario": {
            **prediction,
            "rainfall_regime_label": REGIME_LABELS[prediction["rainfall_regime"]],
            "historical_class_label": CLASS_LABELS[prediction["historical_class"]],
        },
        "headline": (
            f"Cenário de {REGIME_LABELS[prediction['rainfall_regime']]} em {location['name']}"
        ),
        "summary": (
            f"A previsão mensal indica {prediction['estimated_monthly_mm']:.1f} mm no mês, "
            f"{CLASS_LABELS[prediction['historical_class']]} para esta época do ano."
        ),
        "guidance": guidance,
        "provenance": {
            "model_id": catalog["model_id"],
            "training_period": catalog["training_period"],
            "prediction_period": catalog["prediction_period"],
            "temporal_contract": catalog["temporal_contract"],
            "generated_at": catalog["generated_at"],
            "notice": catalog["notice"],
        },
        "official_submission_unchanged": True,
        "is_current_forecast": False,
    }
