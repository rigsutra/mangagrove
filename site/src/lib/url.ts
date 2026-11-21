import series from '../data/series.json';
export type Chapter = { n: number; title: string; date: string; langs: Record<string, [number, number][]> };
export type Series = { slug: string; title: string; genres: string[]; status: string; synopsis: string; langs: string[]; credit?: string; chapters: Chapter[] };
export const allSeries = series as unknown as Series[];
export const SITE_NAME = 'MangaGrove';
export const REPO_URL = 'https://github.com/rigsutra/mangagrove';
export const LANG_LABEL: Record<string, string> = { en: 'English', hi: 'हिन्दी', hinglish: 'Hinglish' };
// BCP 47 tags for <html lang> and hreflang ("hinglish" is not a valid tag).
export const hreflang = (l: string) => ({ hinglish: 'hi-Latn' } as Record<string, string>)[l] ?? l;
export const u = (p: string) => (import.meta.env.BASE_URL.replace(/\/$/, '') + p);
export const cover = (s: Series) => u(`/series/${s.slug}/cover.webp`);
export const latest = (s: Series) => [...s.chapters].sort((a, b) => b.n - a.n);
export const oldest = (s: Series) => [...s.chapters].sort((a, b) => a.n - b.n);
export const seriesUrl = (s: Series) => u(`/series/${s.slug}/`);
export const readUrl = (s: Series, n: number, lang = 'en') => u(`/series/${s.slug}/${lang}/${n}/`);
export const pageUrl = (s: Series, lang: string, n: number, i: number) => u(`/series/${s.slug}/${lang}/ch-${n}/${String(i).padStart(2, '0')}.webp`);
export const primaryLang = (c: Chapter) => (c.langs.en ? 'en' : Object.keys(c.langs)[0]);
