import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Heart, Sparkles } from "lucide-react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: "Fairy Story Generator",
  description: "Create magical AI-powered stories for your child",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen flex flex-col`}
        suppressHydrationWarning
      >
        <main className="flex-grow">
          {children}
        </main>

        {/* FOOTER SIÊU NHỎ GỌN - HÀNG NGANG */}
        <footer className="w-full py-4 border-t border-gray-100 bg-white/50 backdrop-blur-sm">
          <div className="container mx-auto px-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
            
            {/* Copyright */}
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">
              © 2025 FAIRY STORY AI
            </span>

            {/* Author - Gradient nhỏ gọn */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">
                Handcrafted by
              </span>
              <span className="text-xs font-black bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-500 tracking-tighter">
                TRUNG TRỊNH
              </span>
            </div>

            {/* Slogan & Icon */}
            <div className="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase">
              <div className="h-3 w-px bg-gray-200 hidden sm:block" />
              <span className="flex items-center gap-1">
                MADE WITH <Heart className="w-2.5 h-2.5 text-pink-400 fill-pink-400" /> FOR KIDS
                <Sparkles className="w-2.5 h-2.5 text-yellow-500" />
              </span>
            </div>

          </div>
        </footer>
      </body>
    </html>
  );
}