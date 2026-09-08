import "./styles.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Электротехника 2026/27", description: "База знаний курса" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body>{children}</body></html>;
}
