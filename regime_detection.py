"""
Regime Detection via Markov Switching (statsmodels) ou Change-Point Detection (scipy/sklearn).

Uso:
    from regime_detection import detect_regimes
    result = detect_regimes(df_ohlcv, method="hmm", n_states=0, features=["log_return", "volatility"])
"""

import warnings
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

warnings.filterwarnings("ignore")


# ─── Feature engineering ─────────────────────────────────────────────────────

def _compute_features(df: pd.DataFrame, feature_list: list, vol_window: int = 20) -> pd.DataFrame:
    """Calcula features para o modelo a partir de OHLCV."""
    feats = pd.DataFrame(index=df.index)

    close = df["Close"] if "Close" in df.columns else df["close"]
    log_ret = np.log(close / close.shift(1))

    if "log_return" in feature_list:
        feats["log_return"] = log_ret

    if "volatility" in feature_list:
        feats["volatility"] = log_ret.rolling(vol_window).std()

    if "volume" in feature_list:
        vol_col = "Volume" if "Volume" in df.columns else "volume" if "volume" in df.columns else None
        if vol_col:
            feats["volume"] = np.log1p(df[vol_col].astype(float))

    feats.dropna(inplace=True)
    return feats


# ─── Gaussian HMM via scikit-learn (GaussianMixture + Viterbi manual) ────────

def _fit_gmm_hmm(X: np.ndarray, n_states: int):
    """
    Fit a Gaussian HMM usando sklearn GaussianMixture para emissao
    e estimativa de transicao via contagem sequencial (EM simplificado).
    Retorna: means, covars, transmat, startprob, labels, posteriors
    """
    from sklearn.mixture import GaussianMixture

    # Step 1: Fit GMM para obter clusters iniciais
    gmm = GaussianMixture(
        n_components=n_states,
        covariance_type="full",
        n_init=5,
        max_iter=300,
        random_state=42,
    )
    gmm.fit(X)
    labels = gmm.predict(X)
    posteriors = gmm.predict_proba(X)

    # Step 2: Estima matriz de transicao a partir da sequencia de labels
    transmat = np.zeros((n_states, n_states))
    for i in range(1, len(labels)):
        transmat[labels[i - 1], labels[i]] += 1
    row_sums = transmat.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    transmat = transmat / row_sums

    # Step 3: Startprob
    startprob = np.zeros(n_states)
    startprob[labels[0]] = 1.0

    # Step 4: Viterbi refinement usando transicao + emissao
    # Log-likelihood de emissao por estado
    log_lik = np.zeros((len(X), n_states))
    for s in range(n_states):
        try:
            rv = scipy_stats.multivariate_normal(
                mean=gmm.means_[s],
                cov=gmm.covariances_[s],
                allow_singular=True,
            )
            log_lik[:, s] = rv.logpdf(X)
        except Exception:
            log_lik[:, s] = -1e10

    # Viterbi
    T = len(X)
    delta = np.zeros((T, n_states))
    psi = np.zeros((T, n_states), dtype=int)

    log_trans = np.log(transmat + 1e-10)
    log_start = np.log(startprob + 1e-10)

    delta[0] = log_start + log_lik[0]
    for t in range(1, T):
        for j in range(n_states):
            scores = delta[t - 1] + log_trans[:, j]
            psi[t, j] = np.argmax(scores)
            delta[t, j] = scores[psi[t, j]] + log_lik[t, j]

    # Backtrack
    states = np.zeros(T, dtype=int)
    states[-1] = np.argmax(delta[-1])
    for t in range(T - 2, -1, -1):
        states[t] = psi[t + 1, states[t + 1]]

    # Recalcula posteriors usando forward-backward simplificado
    # (usa os posteriors do GMM como aproximacao, ajustados pelo Viterbi)
    # Para rolling probs mais suaves, usamos smoothed posteriors
    alpha = np.zeros((T, n_states))
    alpha[0] = startprob * np.exp(log_lik[0] - log_lik[0].max())
    alpha[0] /= alpha[0].sum() + 1e-10

    for t in range(1, T):
        for j in range(n_states):
            alpha[t, j] = np.sum(alpha[t - 1] * transmat[:, j]) * np.exp(log_lik[t, j] - log_lik[t].max())
        s = alpha[t].sum()
        if s > 0:
            alpha[t] /= s

    beta = np.zeros((T, n_states))
    beta[-1] = 1.0
    for t in range(T - 2, -1, -1):
        for j in range(n_states):
            beta[t, j] = np.sum(transmat[j, :] * np.exp(log_lik[t + 1] - log_lik[t + 1].max()) * beta[t + 1])
        s = beta[t].sum()
        if s > 0:
            beta[t] /= s

    gamma = alpha * beta
    row_sums = gamma.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    gamma = gamma / row_sums

    return {
        "states": states,
        "posteriors": gamma,
        "transmat": transmat,
        "means": gmm.means_,
        "bic": gmm.bic(X),
        "n_states": n_states,
    }


def _select_n_states(X: np.ndarray, max_states: int = 5) -> int:
    """Seleciona numero otimo de estados via BIC."""
    best_bic = np.inf
    best_n = 2
    for n in range(2, max_states + 1):
        try:
            result = _fit_gmm_hmm(X, n)
            if result["bic"] < best_bic:
                best_bic = result["bic"]
                best_n = n
        except Exception:
            continue
    return best_n


def _label_regimes(states, n_states, close_aligned):
    """Classifica e rotula estados como bull/bear/sideways baseado no retorno medio."""
    returns = close_aligned.pct_change()
    state_means = {}
    for s in range(n_states):
        mask = states == s
        if mask.sum() > 0:
            state_means[s] = float(returns[mask].mean())
        else:
            state_means[s] = 0.0

    sorted_states = sorted(state_means.keys(), key=lambda s: state_means[s])

    if n_states == 2:
        label_map = {sorted_states[0]: "bear", sorted_states[1]: "bull"}
    elif n_states == 3:
        label_map = {sorted_states[0]: "bear", sorted_states[1]: "sideways", sorted_states[2]: "bull"}
    else:
        label_map = {}
        for i, s in enumerate(sorted_states):
            if i < len(sorted_states) // 3:
                label_map[s] = "bear"
            elif i < 2 * len(sorted_states) // 3:
                label_map[s] = "sideways"
            else:
                label_map[s] = "bull"

    labels = [label_map[s] for s in states]
    return labels, label_map


# ─── Markov Switching via statsmodels ────────────────────────────────────────

def _fit_markov_switching(X_series: pd.Series, n_states: int):
    """Fit Markov Switching Regression via statsmodels."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    model = MarkovRegression(
        X_series,
        k_regimes=n_states,
        trend="c",
        switching_variance=True,
    )
    result = model.fit(maxiter=200, disp=False)
    return result


# ─── Change-Point Detection via scipy/numpy (CUSUM-based) ───────────────────

def _detect_changepoints(X: np.ndarray, close_aligned, min_segment: int = 20):
    """Change-point detection usando Binary Segmentation com custo L2."""
    T = len(X)
    if T < min_segment * 2:
        return np.zeros(T, dtype=int), ["sideways"] * T

    # Binary segmentation recursiva
    breakpoints = []
    _binary_segmentation(X, 0, T, min_segment, breakpoints, max_bkps=8)
    breakpoints = sorted(set(breakpoints))

    # Cria segmentos
    boundaries = [0] + breakpoints + [T]
    segments = []
    for i in range(len(boundaries) - 1):
        start, end = boundaries[i], boundaries[i + 1]
        seg_close = close_aligned.iloc[start:end]
        seg_ret = seg_close.pct_change().mean() if len(seg_close) > 1 else 0
        segments.append({"start": start, "end": end, "mean_return": float(seg_ret)})

    # Rotula por retorno medio
    rets = [s["mean_return"] for s in segments]
    if not rets:
        return np.zeros(T, dtype=int), ["sideways"] * T

    q33 = np.percentile(rets, 33)
    q66 = np.percentile(rets, 66)

    labels = ["sideways"] * T
    for seg in segments:
        r = seg["mean_return"]
        if r <= q33:
            l = "bear"
        elif r >= q66:
            l = "bull"
        else:
            l = "sideways"
        for i in range(seg["start"], min(seg["end"], T)):
            labels[i] = l

    # Remapeia para state IDs contíguos (0, 1, ..., n-1)
    unique_labels = sorted(set(labels))
    label_to_id = {lb: idx for idx, lb in enumerate(unique_labels)}
    states = np.array([label_to_id[lb] for lb in labels], dtype=int)

    return states, labels


def _binary_segmentation(X, start, end, min_size, breakpoints, max_bkps=8):
    """Binary segmentation recursiva com custo L2."""
    if end - start < 2 * min_size or len(breakpoints) >= max_bkps:
        return

    # Custo total do segmento
    seg = X[start:end]
    total_cost = np.sum((seg - seg.mean(axis=0)) ** 2)

    # Testa cada ponto de corte
    best_gain = 0
    best_bp = None
    for bp in range(start + min_size, end - min_size):
        left = X[start:bp]
        right = X[bp:end]
        cost_left = np.sum((left - left.mean(axis=0)) ** 2)
        cost_right = np.sum((right - right.mean(axis=0)) ** 2)
        gain = total_cost - cost_left - cost_right
        if gain > best_gain:
            best_gain = gain
            best_bp = bp

    # Threshold: ganho minimo proporcional ao tamanho
    threshold = total_cost * 0.01
    if best_bp is not None and best_gain > threshold:
        breakpoints.append(best_bp)
        _binary_segmentation(X, start, best_bp, min_size, breakpoints, max_bkps)
        _binary_segmentation(X, best_bp, end, min_size, breakpoints, max_bkps)


# ─── Metrics by regime ───────────────────────────────────────────────────────

def _metrics_by_regime(close_aligned, labels):
    """Calcula metricas condicionais por regime."""
    df = pd.DataFrame({"close": close_aligned.values, "label": labels}, index=close_aligned.index)
    df["return"] = df["close"].pct_change()

    results = {}
    for regime in sorted(set(labels)):
        mask = df["label"] == regime
        rets = df.loc[mask, "return"].dropna()
        if len(rets) < 2:
            results[regime] = {
                "count_bars": int(mask.sum()),
                "pct_time": round(mask.sum() / len(df) * 100, 1),
                "total_return": 0,
                "annualized_return": 0,
                "sharpe": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "volatility": 0,
            }
            continue

        total_ret = float((1 + rets).prod() - 1)
        n_periods = len(rets)
        annual_factor = 252
        ann_ret = (1 + total_ret) ** (annual_factor / max(n_periods, 1)) - 1
        vol = float(rets.std() * np.sqrt(annual_factor))
        sharpe = ann_ret / vol if vol > 0 else 0

        cummax = (1 + rets).cumprod().cummax()
        dd = (1 + rets).cumprod() / cummax - 1
        max_dd = float(dd.min()) * 100

        win_rate = float((rets > 0).sum() / len(rets) * 100)

        results[regime] = {
            "count_bars": int(mask.sum()),
            "pct_time": round(mask.sum() / len(df) * 100, 1),
            "total_return": round(total_ret * 100, 2),
            "annualized_return": round(ann_ret * 100, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown": round(max_dd, 2),
            "win_rate": round(win_rate, 1),
            "volatility": round(vol * 100, 2),
        }

    return results


# ─── Transition matrix ──────────────────────────────────────────────────────

def _transition_matrix(states, n_states):
    """Calcula matriz de transicao empirica (state x state)."""
    mat = np.zeros((n_states, n_states))
    for i in range(1, len(states)):
        mat[states[i - 1], states[i]] += 1

    row_sums = mat.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    mat = mat / row_sums
    return np.round(mat * 100, 1).tolist()


# ─── Main entry point ───────────────────────────────────────────────────────

def detect_regimes(
    df: pd.DataFrame,
    method: str = "hmm",
    n_states: int = 0,
    features: list = None,
    vol_window: int = 20,
) -> dict:
    """
    Detecta regimes de mercado.

    Parameters
    ----------
    df : DataFrame com colunas OHLCV e DatetimeIndex
    method : "hmm", "markov_switching" ou "changepoint"
    n_states : numero de estados (0 = auto via BIC, so para HMM/MS)
    features : lista de features ["log_return", "volatility", "volume"]
    vol_window : janela para calculo de volatilidade realizada

    Returns
    -------
    dict com: dates, prices, regimes, regime_probs, metrics_by_regime,
              transition_matrix, state_names, method, n_states, bic_scores
    """
    if features is None:
        features = ["log_return", "volatility"]

    feat_df = _compute_features(df, features, vol_window)
    X = feat_df.values

    close = df["Close"] if "Close" in df.columns else df["close"]
    close_aligned = close.loc[feat_df.index]

    bic_scores = None

    if method == "markov_switching":
        # Usa statsmodels MarkovRegression (apenas 1D: log_return)
        log_ret_series = feat_df["log_return"] if "log_return" in feat_df.columns else feat_df.iloc[:, 0]

        if n_states <= 0:
            # Seleciona via BIC
            bic_list = []
            best_bic = np.inf
            best_n = 2
            for n in range(2, 5):
                try:
                    res = _fit_markov_switching(log_ret_series, n)
                    bic_val = float(res.bic)
                    bic_list.append({"n": n, "bic": round(bic_val, 2)})
                    if bic_val < best_bic:
                        best_bic = bic_val
                        best_n = n
                except Exception:
                    pass
            n_states = best_n
            bic_scores = bic_list

        ms_result = _fit_markov_switching(log_ret_series, n_states)

        # Smoothed probabilities
        smoothed = ms_result.smoothed_marginal_probabilities
        states = np.array(smoothed.values.argmax(axis=1), dtype=int)
        posteriors = smoothed.values

        labels, label_map = _label_regimes(states, n_states, close_aligned)

        state_names_ordered = []
        for s in range(n_states):
            state_names_ordered.append(label_map.get(s, f"state_{s}"))

        transition = _transition_matrix(states, n_states)

        regime_probs = {
            state_names_ordered[s]: [round(float(p), 4) for p in posteriors[:, s]]
            for s in range(n_states)
        }

    elif method == "hmm":
        # Usa sklearn GMM + Viterbi
        if n_states <= 0:
            # Coleta BIC para selecao
            bic_list = []
            best_bic = np.inf
            best_n = 2
            for n in range(2, 6):
                try:
                    result = _fit_gmm_hmm(X, n)
                    bic_val = float(result["bic"])
                    bic_list.append({"n": n, "bic": round(bic_val, 2)})
                    if bic_val < best_bic:
                        best_bic = bic_val
                        best_n = n
                except Exception:
                    pass
            n_states = best_n
            bic_scores = bic_list

        hmm_result = _fit_gmm_hmm(X, n_states)
        states = hmm_result["states"]
        posteriors = hmm_result["posteriors"]

        labels, label_map = _label_regimes(states, n_states, close_aligned)

        state_names_ordered = []
        for s in range(n_states):
            state_names_ordered.append(label_map.get(s, f"state_{s}"))

        transition = _transition_matrix(states, n_states)

        regime_probs = {
            state_names_ordered[s]: [round(float(p), 4) for p in posteriors[:, s]]
            for s in range(n_states)
        }

    else:
        # changepoint
        states, labels = _detect_changepoints(X, close_aligned)
        unique_labels = sorted(set(labels))
        n_states = len(unique_labels)
        state_names_ordered = unique_labels
        transition = _transition_matrix(states, n_states)
        regime_probs = None

    # Build output
    dates = [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in feat_df.index]
    prices = [round(float(v), 6) for v in close_aligned.values]

    metrics = _metrics_by_regime(close_aligned, labels)

    return {
        "dates": dates,
        "prices": prices,
        "regimes": labels,
        "regime_probs": regime_probs,
        "metrics_by_regime": metrics,
        "transition_matrix": transition,
        "state_names": state_names_ordered,
        "method": method,
        "n_states": n_states,
        "bic_scores": bic_scores,
    }
