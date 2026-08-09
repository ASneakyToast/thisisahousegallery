/**
 * CMS API client — build-time data source for the static site.
 *
 * Fetches content from the headless CMS at build time and returns it for
 * Astro pages. The base URL is env-overridable so the same code can build
 * against localhost (default) or a public/remote CMS URL.
 *
 *   CMS_API_URL=http://localhost:8000/v1   npm run build
 */
const BASE =
  (import.meta.env?.PUBLIC_CMS_API_URL as string | undefined) ??
  'http://localhost:8000/v1';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`CMS ${path} -> HTTP ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface Rendition {
  filter_spec: string;
  file_path: string;
  width: number;
  height: number;
  url: string;
}

export interface Image {
  id: number;
  title: string;
  alt: string;
  credit: string;
  description: string;
  file_path: string;
  width: number;
  height: number;
  file_url: string;
  renditions: Rendition[];
}

export interface Artist {
  id: number;
  name: string;
  slug: string;
  bio: string;
  website: string;
  email: string;
  birth_year: number | null;
  socials: Record<string, unknown>[];
  profile_image: Image | null;
}

export interface Artwork {
  id: number;
  title: string;
  slug: string;
  description: string;
  size: string;
  width_inches: number | null;
  height_inches: number | null;
  depth_inches: number | null;
  date: string | null;
  price: string;
  artifacts: Record<string, unknown>[];
  artists: Artist[];
  images: Image[];
  tags: { id: number; name: string; slug: string }[];
}

export interface Exhibition {
  id: number;
  title: string;
  slug: string;
  start_date: string | null;
  end_date: string | null;
  description: string;
  body: Record<string, unknown>[];
  video_embed_url: string;
  listing_title: string;
  listing_summary: string;
  listing_image: Image | null;
  artists: Artist[];
  artworks: Artwork[];
  photos?: { id: number; category: string; sort_order: number; image: Image | null }[];
}

export interface SiteSettings {
  site_title: string;
  tagline: string;
  nav: Record<string, unknown>[];
  contact: Record<string, unknown>;
  socials: Record<string, unknown>[];
}

export interface EventItem {
  id: number;
  title: string;
  slug: string;
  event_type: string;
  tagline: string;
  start_date: string | null;
  end_date: string | null;
  start_time: string | null;
  end_time: string | null;
  all_day: boolean;
  custom_venue_name: string;
  custom_address: string;
  location_details: string;
  description: string;
  capacity: number | null;
  registration_required: boolean;
  registration_link: string;
  ticket_price: string;
  contact_email: string;
  external_link: string;
  featured_on_schedule: boolean;
  related_exhibition: Exhibition | null;
  featured_image: Image | null;
}

export const cms = {
  siteSettings: () => get<SiteSettings>('/site-settings'),
  exhibitions: () => get<Exhibition[]>('/exhibitions'),
  exhibition: (slug: string) => get<Exhibition>(`/exhibitions/${slug}`),
  artists: () => get<Artist[]>('/artists'),
  artist: (slug: string) => get<Artist & { artworks: Artwork[] }>(`/artists/${slug}`),
  artworks: () => get<Artwork[]>('/artworks'),
  artwork: (slug: string) => get<Artwork>(`/artworks/${slug}`),
  tags: () => get<{ id: number; name: string; slug: string }[]>('/tags'),
    events: () => get<EventItem[]>('/events'),
    image: (id: number) => get<Image>(`/images/${id}`),
  };

/**
 * Pick the best image URL for a given display context.
 * Falls back through rendition sizes (web-optimized -> thumbnail -> file_url).
 */
export function bestImageUrl(
  image: Image | null | undefined,
  opts: { max?: number } = {},
): string | undefined {
  if (!image) return undefined;
  const urls = image.renditions.map((r) => ({ ...r }));
  urls.sort((a, b) => a.width - b.width);
  // Pick the smallest rendition >= max, else the largest available.
  const target = urls.filter((r) => opts.max ? r.width >= opts.max! : true);
  const pick = (target.length ? target : urls).at(-1);
  return pick?.url || image.file_url || undefined;
}

/** First showcard (promotional flyer) photo image for an exhibition, if any. */
export function showcardImage(ex: Exhibition): Image | null {
  return ex.photos?.find((p) => p.category === 'showcard')?.image ?? null;
}

/** Photos grouped by category, in source order (installation/opening/…). */
export function photosByCategory(ex: Exhibition): Record<string, Image[]> {
  const groups: Record<string, Image[]> = {};
  for (const p of ex.photos ?? []) {
    if (!p.image) continue;
    (groups[p.category] ??= []).push(p.image);
  }
  return groups;
}

/**
 * Replicates the original Wagtail `get_filtered_gallery_images` rule for the
 * exhibitions index page:
 *   1. first showcard,
 *   2. installation photos + each artwork's COVER image (first image), shuffled,
 *   3. remaining showcards,
 *   — opening-reception and in-progress photos are excluded.
 */
export function filteredGalleryImages(ex: Exhibition): Image[] {
  if (!ex.photos?.length && !(ex.artworks ?? []).some((a) => a.images?.length)) {
    return ex.listing_image ? [ex.listing_image] : [];
  }
  const byCat = photosByCategory(ex);
  const showcards = byCat['showcard'] ?? [];
  const installation = byCat['installation'] ?? [];

  const ordered = [...showcards];
  // First showcard at the front
  const first = ordered.shift();

  // Middle: installation photos + first image of every artwork-with-image
  const middle: Image[] = [...installation];
  for (const a of ex.artworks ?? []) {
    if (a.images?.length) middle.push(a.images[0]); // cover shot only
  }
  // Random shuffle (matches original `random.shuffle`)
  for (let i = middle.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [middle[i], middle[j]] = [middle[j], middle[i]];
  }

  // Reassemble: first showcard, shuffled middle, remaining showcards last.
  const out: Image[] = [];
  if (first) out.push(first);
  out.push(...middle);
  out.push(...ordered); // remaining showcards at end
  return out;
}