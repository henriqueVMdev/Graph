import plotly.express as px
import pandas as pd


def _filter_cols(df, cols):
    """Retorna apenas as colunas que existem no dataframe."""
    return [c for c in cols if c in df.columns]


def plot_return_vs_drawdown(df: pd.DataFrame):
    """Scatter: Retorno (%) vs Max Drawdown (%), colorido por Score."""
    plot_df = df.reset_index(drop=True)
    hover = _filter_cols(plot_df, ["rank", "ma", "periodo", "lookback", "profit_factor", "sharpe"])
    fig = px.scatter(
        plot_df,
        x="max_dd_pct",
        y="return_pct",
        color="score",
        color_continuous_scale="RdYlGn",
        custom_data=_filter_cols(plot_df, ["rank"]),
        hover_data=hover,
        labels={
            "max_dd_pct": "Max Drawdown (%)",
            "return_pct": "Retorno (%)",
            "score": "Score",
        },
        title="Retorno vs Max Drawdown",
        template="plotly_white",
    )
    fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="DarkSlateGrey")))
    fig.update_layout(
        height=500,
        xaxis_title="Max Drawdown (%)",
        yaxis_title="Retorno (%)",
    )
    return fig


def plot_return_vs_sharpe(df: pd.DataFrame):
    """Scatter: Retorno (%) vs Sharpe, colorido por Win Rate."""
    plot_df = df.reset_index(drop=True)
    hover = _filter_cols(plot_df, ["rank", "trades", "max_dd_pct", "profit_factor", "ma"])
    fig = px.scatter(
        plot_df,
        x="sharpe",
        y="return_pct",
        color="win_rate_pct",
        color_continuous_scale="Viridis",
        custom_data=_filter_cols(plot_df, ["rank"]),
        hover_data=hover,
        labels={
            "sharpe": "Sharpe Ratio",
            "return_pct": "Retorno (%)",
            "win_rate_pct": "Win Rate (%)",
        },
        title="Retorno vs Sharpe Ratio",
        template="plotly_white",
    )
    fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="DarkSlateGrey")))
    fig.update_layout(
        height=500,
        xaxis_title="Sharpe Ratio",
        yaxis_title="Retorno (%)",
    )
    return fig


def plot_return_vs_trades(df: pd.DataFrame):
    """Scatter: Retorno (%) vs Numero de Trades, colorido por Profit Factor."""
    plot_df = df.reset_index(drop=True)
    hover = _filter_cols(plot_df, ["rank", "sharpe", "max_dd_pct", "win_rate_pct", "ma"])
    fig = px.scatter(
        plot_df,
        x="trades",
        y="return_pct",
        color="profit_factor",
        color_continuous_scale=[
            [0.0, "#d32f2f"],
            [0.05, "#e53935"],
            [1 / 20, "#ffeb3b"],
            [2 / 20, "#66bb6a"],
            [5 / 20, "#2e7d32"],
            [1.0, "#1b5e20"],
        ],
        range_color=[0, 20],
        custom_data=_filter_cols(plot_df, ["rank"]),
        hover_data=hover,
        labels={
            "trades": "Numero de Trades",
            "return_pct": "Retorno (%)",
            "profit_factor": "Profit Factor",
        },
        title="Retorno vs Numero de Trades",
        template="plotly_white",
    )
    fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="DarkSlateGrey")))
    fig.update_layout(
        height=500,
        xaxis_title="Trades",
        yaxis_title="Retorno (%)",
    )
    return fig
                                                                                                                                                                                                            