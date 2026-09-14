import { BottomNav } from "@/components/nav/BottomNav";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen pb-20">
      <main className="mx-auto max-w-md px-6 py-10 sm:max-w-lg">{children}</main>
      <BottomNav />
    </div>
  );
}
