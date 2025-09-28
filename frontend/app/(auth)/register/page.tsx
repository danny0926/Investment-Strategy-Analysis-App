"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClient } from "../../../lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiClient.post("/auth/register", form);
      router.push("/login");
    } catch (err) {
      setError("Unable to register");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <form onSubmit={submit} className="space-y-4 bg-slate-900 p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold">Register</h1>
        {error && <p className="text-red-400">{error}</p>}
        <div>
          <label className="block text-sm text-slate-300">Email</label>
          <input
            type="email"
            className="w-full rounded bg-slate-800 px-3 py-2"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm text-slate-300">Password</label>
          <input
            type="password"
            className="w-full rounded bg-slate-800 px-3 py-2"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <button type="submit" className="w-full bg-emerald-500 hover:bg-emerald-400 text-black py-2 rounded">
          Create Account
        </button>
        <p className="text-sm text-slate-400">
          Already have an account? <Link href="/login" className="text-emerald-400">Login</Link>
        </p>
      </form>
    </div>
  );
}
