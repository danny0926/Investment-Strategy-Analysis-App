"use client";

import { useEffect, useState } from "react";

import { apiClient, setAuthToken } from "../../lib/api";
import { useAuthToken } from "../../lib/useAuth";

interface TradeRow {
  id: number;
  symbol: string;
  side: string;
  qty: number;
  price: number;
  trade_ts: string;
}

export default function TradesPage() {
  const { token } = useAuthToken();
  const [trades, setTrades] = useState<TradeRow[]>([]);

  useEffect(() => {
    if (!token) return;
    setAuthToken(token);
    const load = async () => {
      const accounts = await apiClient.get("/accounts");
      const first = accounts.data[0];
      if (!first) return;
      const { data } = await apiClient.get(`/accounts/${first.id}/trades`);
      setTrades(data);
    };
    void load();
  }, [token]);

  return (
    <div className="p-8 space-y-4">
      <h1 className="text-3xl font-semibold">Trades</h1>
      <table className="min-w-full text-left bg-slate-900 rounded-xl overflow-hidden">
        <thead className="bg-slate-800 text-sm uppercase text-slate-400">
          <tr>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Symbol</th>
            <th className="px-4 py-3">Side</th>
            <th className="px-4 py-3">Qty</th>
            <th className="px-4 py-3">Price</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.id} className="border-t border-slate-800">
              <td className="px-4 py-3">{new Date(trade.trade_ts).toLocaleString()}</td>
              <td className="px-4 py-3">{trade.symbol}</td>
              <td className="px-4 py-3">{trade.side}</td>
              <td className="px-4 py-3">{trade.qty}</td>
              <td className="px-4 py-3">{trade.price.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
