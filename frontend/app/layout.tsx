import type { Metadata } from "next";
import "./globals.css";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

export const metadata: Metadata = {
  title: "Havana University Chat",
  description: "Chat with our AI assistant to learn more about Havana University",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <SidebarProvider>
          <div className="flex h-screen w-full">
            <AppSidebar />
            <main className="flex-1 overflow-hidden">
              {children}
            </main>
          </div>
        </SidebarProvider>
      </body>
    </html>
  );
}
