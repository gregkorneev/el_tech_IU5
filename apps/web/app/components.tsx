import Link from "next/link";

export const nav = [{ href: "/", label: "Обзор" }, { href: "/materials", label: "Материалы" }, { href: "/lectures", label: "Лекции" }, { href: "/labs", label: "Лабораторные" }, { href: "/recordings", label: "Записи" }, { href: "/topics", label: "Темы" }, { href: "/updates", label: "Обновления" }];

export function Sidebar() {
  return <aside><Link className="brand" href="/"><span>ЭТ</span><b>Электротехника</b><small>2026 / 27</small></Link><nav>{nav.map(item => <Link key={item.href} href={item.href}>{item.label}</Link>)}</nav><p className="sync-note"><i />Синхронизация с Диском<br /><small>Автоматически каждые 3 часа</small></p></aside>;
}

export function Shell({ children }: { children: React.ReactNode }) { return <div className="shell"><Sidebar/><main>{children}</main></div>; }
