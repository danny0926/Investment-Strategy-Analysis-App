"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [shioajiKey, setShioajiKey] = useState("");
  const [ibkrToken, setIbkrToken] = useState("");

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-semibold">Connections</h1>
      <section className="bg-slate-900 p-6 rounded-xl space-y-4">
        <div>
          <h2 className="text-xl font-medium">Shioaji</h2>
          <p className="text-sm text-slate-400">Mock integration placeholder.</p>
          <input
            value={shioajiKey}
            onChange={(event) => setShioajiKey(event.target.value)}
            className="mt-2 bg-slate-800 px-3 py-2 rounded w-full"
            placeholder="API Token"
          />
        </div>
        <div>
          <h2 className="text-xl font-medium">IBKR</h2>
          <input
            value={ibkrToken}
            onChange={(event) => setIbkrToken(event.target.value)}
            className="mt-2 bg-slate-800 px-3 py-2 rounded w-full"
            placeholder="Client Portal token"
          />
        </div>
        <button className="bg-emerald-500 hover:bg-emerald-400 text-black px-4 py-2 rounded">
          Save Connections
        </button>
      </section>
    </div>
  );
}
