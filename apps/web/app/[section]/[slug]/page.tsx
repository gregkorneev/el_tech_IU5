import Link from "next/link";
import { notFound } from "next/navigation";
import { Shell } from "../../components";

type Material = { id: number; name: string; path: string; type: string; status: string; category: string; originalUrl?: string; text?: string; summary?: { short: string; detail: string; topics: string[]; formulas: string[] } };
async function getItem(id: string): Promise<Material | null> {
  try { const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"; const res = await fetch(`${api}/materials/${id}`, { cache: "no-store" }); return res.ok ? res.json() : null; } catch { return null; }
}
export default async function MaterialPage({ params }: { params: Promise<{ section: string; slug: string }> }) {
  const { section, slug } = await params;
  const id = slug.match(/^\d+/)?.[0];
  if (!id) notFound();
  const item = await getItem(id);
  if (!item || item.category !== section) notFound();
  const parent = section === "lectures" ? "Лекции" : section === "labs" ? "Лабораторные" : "Записи занятий";
  return <Shell><article className="reading"><Link className="back" href={`/${section}`}>← {parent}</Link><p className="eyebrow">{item.type} · {item.status}</p><h1>{item.name}</h1><p className="source-path">{item.path}</p>{item.originalUrl && <a className="source-link" href={item.originalUrl} target="_blank">Открыть оригинал на Яндекс.Диске ↗</a>}{item.summary && <section className="summary"><h2>Кратко</h2><p>{item.summary.short}</p><h2>Подробный конспект</h2><div className="source-text">{item.summary.detail}</div>{item.summary.topics.length > 0 && <><h2>Темы</h2><div className="tags">{item.summary.topics.map(topic => <span key={topic}>{topic}</span>)}</div></>}</section>}<section><h2>Извлечённый текст</h2>{item.text ? <div className="source-text">{item.text}</div> : <div className="empty"><p>Материал обнаружен, но ещё ожидает обработки. После команды <code>python -m worker.process</code> здесь появится текст и конспект.</p></div>}</section></article></Shell>;
}
