import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VendorCheck — Trust Every Payment Before You Send It",
  description:
    "VendorCheck is an AI-powered inbox that catches suspicious vendor requests, bank changes, and urgent payment scams — before your team sends money.",
  keywords: [
    "payment verification",
    "vendor trust",
    "payment fraud prevention",
    "SMB payments",
    "AI trust inbox",
    "bank change detection",
  ],
  openGraph: {
    title: "VendorCheck — Trust Every Payment Before You Send It",
    description:
      "An AI-powered inbox that catches suspicious vendor requests before your team sends money.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
