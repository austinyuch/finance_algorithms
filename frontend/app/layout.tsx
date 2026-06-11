import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantLab Showcase Dashboard",
  description: "Local runtime dashboard for QuantLab research evidence"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
