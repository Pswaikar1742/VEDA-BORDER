import React from "react";
import "./globals.css";

export const metadata = {
  title: "VEDA-BORDER · Forensic Identity & Document Screening Workstation",
  description: "AI-Based Fake Identity & Document Screening System — Ministry of Home Affairs / SSB PS 26188",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
