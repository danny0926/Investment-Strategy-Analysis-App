"use client";

import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { apiClient, setAuthToken } from "../../lib/api";
import { useAuthToken } from "../../lib/useAuth";

interface Account {
  id: number;
  account_code: string;
}

interface KPIResponse {
  win_rate: number | null;
  avg_win: number | null;
  avg_loss: number | null;
  profit_factor: number | null;
  expectancy: number | null;
  mdd: number | null;
  total_trades: number;
}

interface EquityPoint {
  date: string;
  equity: number;
  net_pnl_day: number;
}

export default function DashboardPage() {
  const { token } = useAuthToken();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null);
  const [kpi, setKpi] = useState<KPIResponse | null>(null);
  const [equity, setEquity] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      loadAccounts();
    }
  }, [token]);

  const loadAccounts = async () => {
    const { data } = await apiClient.get<Account[]>("/accounts");
    setAccounts(data);
    if (data.length) {
      setSelectedAccount(data[0].id);
    }
  };

  useEffect(() => {
    if (!selectedAccount) return;
    const fetchData = async () => {
      setLoading(true);
      const start = new Date();
      start.setMonth(start.getMonth() - 1);
      const end = new Date();
      const params = {
        account_id: selectedAccount,
        start: start.toISOString(),
        end: end.toISOString()
      };
      const [kpiRes, equityRes] = await Promise.all([
        apiClient.get<KPIResponse>("/kpis/summary", { params: { ...params, scope: "account" } }),
        apiClient.get<EquityPoint[]>("/equity/daily", { params })
      ]);
      setKpi(kpiRes.data);
      setEquity(equityRes.data);
      setLoading(false);
    };
    void fetchData();
  }, [selectedAccount]);

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <select
          className="bg-slate-900 px-3 py-2 rounded"
          value={selectedAccount ?? ""}
          onChange={(event) => setSelectedAccount(Number(event.target.value))}
        >
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.account_code}
            </option>
          ))}
        </select>
      </header>
      {loading && <p>Loading metrics…</p>}
      {kpi && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Metric label="Win Rate" value={kpi.win_rate ? `${(kpi.win_rate * 100).toFixed(1)}%` : "-"} />
          <Metric label="Profit Factor" value={kpi.profit_factor?.toFixed(2) ?? "-"} />
          <Metric label="Expectancy" value={kpi.expectancy?.toFixed(2) ?? "-"} />
          <Metric label="Max Drawdown" value={kpi.mdd?.toFixed(2) ?? "-"} />
        </div>
      )}
      <section className="bg-slate-900 rounded-xl p-6">
        <h2 className="font-medium mb-4">Equity Curve</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={equity}>
              <XAxis dataKey="date" hide />
              <YAxis hide domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b" }} />
              <Line type="monotone" dataKey="equity" stroke="#34d399" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-900 rounded-xl p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
    </div>
  );
}
