import "../styles/globals.css";
import { ReactNode } from "react";

export const metadata = {
  title: "Trade Journal",
  description: "Taiwan & global trade analytics"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <div className="min-h-screen">{children}</div>
      </body>
    </html>
  );
}
