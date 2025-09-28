"use client";

import { useEffect, useState } from "react";

export function useAuthToken() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem("access_token");
    if (stored) {
      setToken(stored);
    }
  }, []);

  const updateToken = (value: string | null) => {
    if (value) {
      window.localStorage.setItem("access_token", value);
    } else {
      window.localStorage.removeItem("access_token");
    }
    setToken(value);
  };

  return { token, setToken: updateToken };
}
