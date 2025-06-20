"""ml_predictor.py
Treino e uso de modelos de Machine Learning para previsão de emergência de
irrigação e forecasting de séries temporais.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

# Ignorar avisos de convergência do ARIMA que não são críticos
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning, module='statsmodels')


# ---------------------------------------------------------------------------
# Feature Engineering helpers
# ---------------------------------------------------------------------------

def add_time_based_features(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Adiciona hora do dia e dia da semana como variáveis categóricas.
    Garante que *timestamp_col* esteja em formato datetime.
    """
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df["hora_dia"] = df[timestamp_col].dt.hour
    df["dia_semana"] = df[timestamp_col].dt.dayofweek
    return df


def add_moving_average(df: pd.DataFrame, col: str, window: int = 3) -> pd.DataFrame:
    """Cria a média móvel de *col* nas últimas *window* leituras."""
    df = df.copy()
    df[f"{col}_ma{window}"] = df[col].rolling(window=window, min_periods=1).mean()
    return df


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Gera matrix X e vetor y para modelagem de risco.

    Assume que existe coluna `emergencia` e `timestamp` (ou um índice Datetime).
    """
    df_f = df.copy()
    
    if 'timestamp' not in df_f.columns and isinstance(df_f.index, pd.DatetimeIndex):
        df_f['timestamp'] = df_f.index
    
    df_f = add_time_based_features(df_f)
    df_f = add_moving_average(df_f, "umidade", window=3)
    df_f = add_moving_average(df_f, "temperatura", window=3)
    df_f = add_moving_average(df_f, "ph_estimado", window=3)

    feature_cols = [
        "umidade", "ph_estimado", "fosforo_presente", "potassio_presente",
        "temperatura", "hora_dia", "dia_semana", "umidade_ma3",
        "temperatura_ma3", "ph_estimado_ma3"
    ]

    for col in feature_cols:
        if col not in df_f.columns:
            df_f[col] = 0

    X = df_f[feature_cols].fillna(method="ffill").fillna(0)
    y = df_f["emergencia"].astype(int)
    return X, y


# ---------------------------------------------------------------------------
# Model Training - Risco de Emergência
# ---------------------------------------------------------------------------

def train_risk_model(
    df: pd.DataFrame,
    param_grid: dict | None = None,
    test_size: float = 0.3,
    random_state: int = 42,
):
    """Realiza treino/validação de um RandomForest para risco de emergência."""
    if df.empty or 'emergencia' not in df.columns:
        raise ValueError("DataFrame para treino de risco deve ser válido e conter a coluna 'emergencia'.")

    if param_grid is None:
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [5, 10, None],
            "min_samples_leaf": [2, 4],
        }

    X, y = build_feature_matrix(df)

    if len(y.unique()) < 2:
        return {"modelo": None, "acuracia": 0, "mensagem": "Não há dados suficientes de ambas as classes (emergência e não emergência) para treinar o modelo."}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    grid = GridSearchCV(
        RandomForestClassifier(random_state=random_state, class_weight='balanced'),
        param_grid=param_grid, cv=3, n_jobs=-1, scoring="accuracy"
    )
    grid.fit(X_train, y_train)

    best_model: RandomForestClassifier = grid.best_estimator_
    y_pred = best_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    return {
        "modelo": best_model, "acuracia": acc, "matriz_confusao": cm,
        "melhores_parametros": grid.best_params_, "features": X.columns.tolist()
    }


# ---------------------------------------------------------------------------
# Model Training - Forecast de Umidade (ARIMA)
# ---------------------------------------------------------------------------

def train_arima_model(series: pd.Series, order=(5,1,0)):
    """Treina um modelo ARIMA em uma série temporal e retorna o modelo treinado."""
    if not isinstance(series, pd.Series) or series.empty:
        raise ValueError("A entrada deve ser uma pandas Series não vazia.")

    if len(series) < 20:
        raise ValueError(f"Série temporal muito curta ({len(series)} pontos). São necessários pelo menos 20 pontos para o forecast.")

    # Garante que a série tenha frequência, se possível
    if series.index.inferred_freq is None:
        series = series.asfreq(pd.infer_freq(series.index), method='ffill')

    try:
        model = ARIMA(series.astype(float), order=order)
        model_fit = model.fit()
        return model_fit
    except Exception as e:
        raise RuntimeError(f"Falha ao treinar modelo ARIMA: {e}")


# ---------------------------------------------------------------------------
# Model Training - Previsão de Manutenção da Bomba
# ---------------------------------------------------------------------------

def train_maintenance_model(df: pd.DataFrame):
    """Treina um RandomForest para prever necessidade de manutenção da bomba."""
    if df.empty or 'bomba_ligada' not in df.columns:
        raise ValueError("DataFrame deve conter as colunas 'timestamp' e 'bomba_ligada'.")
        
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)

    df['ciclo_id'] = (df['bomba_ligada'].astype(int).diff() == 1).cumsum()
    
    time_delta_hours = df.index.to_series().diff().mean().total_seconds() / 3600
    if pd.isna(time_delta_hours) or time_delta_hours == 0:
        time_delta_hours = 1

    df['horas_intervalo'] = df['bomba_ligada'] * time_delta_hours
    df['horas_funcionamento'] = df.groupby('ciclo_id')['horas_intervalo'].cumsum()

    df = add_moving_average(df, "temperatura", window=5)
    df = add_moving_average(df, "umidade", window=5)
    
    X = df[['horas_funcionamento', 'temperatura_ma5', 'umidade_ma5']].fillna(0)
    y = (df['horas_funcionamento'] > 50).astype(int)

    if len(y.unique()) < 2:
        return {"modelo": None, "acuracia": 0, "mensagem": "Não há dados suficientes para treinar o modelo de manutenção."}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)

    acc = accuracy_score(y_test, clf.predict(X_test))
    
    return {"modelo": clf, "acuracia": acc, "features": X.columns.tolist()}
