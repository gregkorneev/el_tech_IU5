import { Shell } from "../components";

const names: Record<string, string> = { lectures: "Лекции", labs: "Лабораторные", recordings: "Записи занятий", topics: "Темы", updates: "Обновления" };
type Material = { id: number; name: string; path: string; type: string; status: string; category: string; excerpt?: string };

async function getItems(category: string): Promise<Material[]> {
  try {
    const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${api}/materials?category=${category}`, { cache: "no-store" });
    return res.ok ? res.json() : [];
  } catch { return []; }
}

export default async function Section({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const title = names[section] ?? "Материалы";
  const items = ["lectures", "labs", "recordings"].includes(section) ? await getItems(section) : [];
  return <Shell><section className="page-head"><p className="eyebrow">Электротехника 2026/27</p><h1>{title}</h1><p>{section === "topics" ? "Связанные понятия появятся после AI-обработки материалов." : "Источник, текст и будущий конспект каждого материала собраны в одной странице."}</p></section>{items.length ? <div className="material-list library-list">{items.map(item => <a href={`/${section}/${item.id}-${encodeURIComponent(item.name)}`} key={item.id}><span className="file-icon">{item.type}</span><span><b>{item.name}</b><small>{item.path}{item.excerpt && ` · ${item.excerpt}`}</small></span><i className={`status ${item.status}`}>{item.status}</i><em>→</em></a>)}</div> : <div className="empty"><h2>Раздел ожидает данные</h2><p>Синхронизируйте папку Яндекс.Диска, чтобы создать первые страницы.</p></div>}</Shell>;
}
