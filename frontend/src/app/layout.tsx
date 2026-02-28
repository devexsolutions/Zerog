'use client';

import { Sniglet } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

const sniglet = Sniglet({
  variable: "--font-sniglet-sans",
  subsets: ["latin"],
  weight: ["400", "800"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${sniglet.variable} antialiased font-sans`}
        suppressHydrationWarning
      >
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
