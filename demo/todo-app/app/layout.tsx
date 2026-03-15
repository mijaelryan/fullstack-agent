import './globals.css';
import { ReactNode } from 'react';

export const metadata = {
  title: 'Lista de Tareas (Windows 95)',
  description: 'Una aplicación de lista de tareas inspirada en Windows 95.',
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white text-black font-sans">{children}</body>
    </html>
  );
}