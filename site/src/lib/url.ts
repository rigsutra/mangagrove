import series from '../data/series.json';
export type Chapter = { n: number; title: string; pages: number; date: string };
export type Series = { slug: string; title: string; genres: string[]; status: string; synopsis: string; chapters: Chapter[] };
export const allSeries = series as Series[];
export const u = (p: string) => (import.meta.env.BASE_URL.replace(/\/$/, '') + p);
export const cover = (s: Series) => u(`/series/${s.slug}/cover.webp`);
export const latest = (s: Series) => [...s.chapters].sort((a, b) => b.n - a.n);
