Backtesting Strategy Dashboard

Dashboard interativo para analise de resultados de backtesting + engine da Estrategia DePaula v2.

Duas interfaces disponiveis: Streamlit (tudo-em-um) ou Flask + Vue.js (backend/frontend separados).

Instalacao

bash
Backend (Python)
pip install -r requirements.txt

Frontend (Node)
cd frontend
npm install

Como Rodar

#Opcao 1 - Streamlit (interface simples)

bash
streamlit run app.py


Abre em `http://localhost:8501`.

### Opcao 2 - Flask + Vue.js (backend/frontend separados)

Terminal 1 - Backend:
```bash
python server.py
```
Roda em `http://localhost:5000`.

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```
Abre em `http://localhost:5173`.

Para build de producao do frontend:
```bash
cd frontend
npm run build
```

### Backtesting standalone

```bash
python backtesting.py                          # dados via yfinance (BTCUSDT)
python backtesting.py --csv dados.csv          # dados de CSV local
python backtesting.py --symbol ETHUSDT --ma-type EMA --ma-length 20
```

Use `python backtesting.py --help` para ver todos os parametros.

## Formato dos CSVs

**Dashboard** - colunas obrigatorias: `Retorno (%), Max DD (%), Trades, Win Rate (%), Profit Factor, Sharpe, Score`

**Backtesting** - colunas obrigatorias: `Date, Open, High, Low, Close`
