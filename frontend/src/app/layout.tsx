import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MediVault",
  description: "Secure Medical Records & AI Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}