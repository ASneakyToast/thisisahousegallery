# House Gallery Email Editor — Spec Sheet v0.1

> **Context:** This spec defines the email editor for the planned Starlette headless backend rewrite.
> The editor lives in the Starlette admin, replaces Wagtail's StreamField newsletter body editor,
> and produces send-ready HTML for the newsletter send pipeline.
>
> **Status:** Design spec — not yet implemented.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Document Schema](#2-document-schema)
3. [Design Token System](#3-design-token-system)
4. [Block Taxonomy](#4-block-taxonomy)
5. [Columns Block](#5-columns-block)
6. [Mobile Override System](#6-mobile-override-system)
7. [Merge Tag System](#7-merge-tag-system)
8. [Rendering Pipeline](#8-rendering-pipeline)
9. [Open UX Decisions](#9-open-ux-decisions)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  EDITOR (client-side, vanilla JS)                       │
│  • Document state (flat dict, in-memory)                │
│  • Token resolver ({path} → literal value)              │
│  • Block renderers (per type → HTML string)             │
│  • Live preview (re-renders on change)                  │
│  • Mobile preview (applies _mobile overrides)           │
└───────────────┬─────────────────────────────────────────┘
                │ POST { document: {...}, tokens: {...} }
┌───────────────▼─────────────────────────────────────────┐
│  STARLETTE ADMIN (server-side, Python)                  │
│  • Token resolver (Python, identical logic to JS)       │
│  • Block renderers (Python string templates)            │
│  • Newsletter merge tag substitution (Pass 1)           │
│  • Per-recipient merge tag substitution (Pass 2)        │
│  • Custom CSS inliner (token refs → inline style="")    │
│  • Output: complete <!DOCTYPE html> email               │
└─────────────────────────────────────────────────────────┘
```

The client-side editor and server-side renderer are **separate implementations of the same spec**.
Both consume the same `tokens.json` and the same document JSON. Both must produce identical output.

### Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Document schema | Flat dictionary | Diffable, DB-friendly, no deep nesting |
| Mobile/responsive | Unlayer-style sparse diff (`_mobile`) | Best email-compatible pattern; media queries unreliable in Outlook |
| Design tokens | DTCG 2025.10 format | Figma-compatible; flows directly from Figma → tokens.json → editor |
| Token resolution | Literal values at render time | Email clients don't support CSS custom properties |
| Client-side | Vanilla JS, no framework | No build step complexity in the admin |
| Server-side render | Python | No Node.js dependency |
| CSS strategy | Inline from token resolution | No post-processing inliner needed for token-derived styles |
| Gallery blocks | Inline snapshot + model ID | Newsletters are historical documents; snapshot prevents retroactive data changes |

---

## 2. Document Schema

### Top-level envelope

```json
{
  "schemaVersion": "1.0",
  "meta": {
    "contentWidth": 600,
    "preheader": "See what's new at the gallery this month."
  },
  "tokenOverrides": {},
  "document": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `schemaVersion` | string | Schema version for future migrations |
| `meta.contentWidth` | integer (px) | Email envelope width — typically 600 |
| `meta.preheader` | string | Plain text shown in inbox preview before open |
| `tokenOverrides` | object | Sparse DTCG object merged on top of base tokens before render. Use for per-newsletter accent colors, seasonal overrides, etc. |

### Document body — flat dictionary

Every block is a top-level key. Children reference each other by ID. No nesting.

```json
{
  "root": {
    "type": "Root",
    "data": {
      "style": {
        "backgroundColor": "{color.surface.backdrop}",
        "fontFamily": "{font.family.body}"
      },
      "childrenIds": ["sec-header", "sec-body", "sec-footer"]
    }
  },

  "sec-header": {
    "type": "Section",
    "data": {
      "props": { "anchor": "header" },
      "style": {
        "backgroundColor": "{color.surface.canvas}",
        "padding": { "top": 32, "bottom": 24, "left": 24, "right": 24 }
      },
      "childrenIds": ["img-logo"]
    }
  },

  "img-logo": {
    "type": "Image",
    "data": {
      "props": {
        "src": "https://cdn.example.com/logo.png",
        "alt": "This is a House Gallery",
        "width": 160,
        "linkHref": "{{gallery.website}}"
      },
      "style": {
        "align": "center",
        "padding": { "top": 0, "bottom": 0, "left": 0, "right": 0 }
      },
      "_mobile": {
        "props": { "width": 120 }
      }
    }
  }
}
```

### Block ID format

```
{type-prefix}-{nanoid6}
```

Examples: `sec-k3n2p`, `head-x7r1q`, `cols-j5w9v`, `btn-p2m4k`

Type prefixes:

| Type | Prefix |
|---|---|
| Root | `root` (singleton) |
| Section | `sec` |
| Columns | `cols` |
| Heading | `head` |
| Text | `text` |
| Image | `img` |
| Button | `btn` |
| Divider | `div` |
| Spacer | `spc` |
| Html | `html` |
| SocialLinks | `soc` |
| UnsubscribeFooter | `unsub` (singleton) |
| FeaturedArtwork | `art` |
| ExhibitionDetails | `exh` |
| ArtistFeature | `artist` |

### Structural rules

- `Root` and `Section` carry `childrenIds` (ordered array of block IDs)
- `Columns` carries `columns[n].childrenIds` (one per column slot)
- All other block types are **leaves** — no children permitted
- `_mobile` is a sparse diff at the `data` level — only changed keys are present
- Block order within `childrenIds` is the render order top-to-bottom

### Per-block data structure

```
block.data
  .props      — semantic content (text, src, href, level, etc.)
  .style      — visual properties (color, padding, fontSize, etc.)
  ._mobile    — sparse diff applied at mobile breakpoint (≤480px)
               may contain props and/or style sub-objects
```

Token references (`{path.to.token}`) are valid in any `style` value and in select `props` values where visual output is expected.

---

## 3. Design Token System

### Format

[W3C Design Tokens Community Group](https://tr.designtokens.org/format/) format (DTCG 2025.10).
String shorthand for dimension and color values (object form reserved for future tooling migration).
Stored as `tokens.json` on the backend, editable via admin settings page.

Figma-compatible: tokens flow Figma Variables → exported `tokens.json` → editor → rendered email
without format conversion.

### Two-tier architecture

**Tier 1 — Primitives** (raw values, no aliases, not consumed by blocks directly)

```json
{
  "primitive": {
    "color": {
      "$type": "color",
      "black":     { "$value": "#0A0A0A" },
      "white":     { "$value": "#FFFFFF" },
      "gray-100":  { "$value": "#F5F5F4" },
      "gray-200":  { "$value": "#E7E5E4" },
      "gray-500":  { "$value": "#78716C" },
      "gray-900":  { "$value": "#1C1917" },
      "brand-100": { "$value": "#F0EAFB" },
      "brand-500": { "$value": "#7C3AED" },
      "brand-700": { "$value": "#5B21B6" }
    },
    "font": {
      "family": {
        "heading": {
          "$type": "fontFamily",
          "$value": ["'GT Alpina'", "Georgia", "serif"]
        },
        "body": {
          "$type": "fontFamily",
          "$value": ["'Inter'", "Helvetica Neue", "sans-serif"]
        }
      },
      "weight": {
        "regular": { "$type": "fontWeight", "$value": 400 },
        "medium":  { "$type": "fontWeight", "$value": 500 },
        "bold":    { "$type": "fontWeight", "$value": 700 }
      },
      "size": {
        "$type": "dimension",
        "xs":  { "$value": "12px" },
        "sm":  { "$value": "14px" },
        "md":  { "$value": "16px" },
        "lg":  { "$value": "20px" },
        "xl":  { "$value": "24px" },
        "2xl": { "$value": "32px" },
        "3xl": { "$value": "48px" }
      }
    },
    "spacing": {
      "$type": "dimension",
      "0":  { "$value": "0px" },
      "1":  { "$value": "4px" },
      "2":  { "$value": "8px" },
      "3":  { "$value": "12px" },
      "4":  { "$value": "16px" },
      "6":  { "$value": "24px" },
      "8":  { "$value": "32px" },
      "12": { "$value": "48px" }
    },
    "radius": {
      "$type": "dimension",
      "none": { "$value": "0px" },
      "sm":   { "$value": "4px" },
      "md":   { "$value": "8px" },
      "full": { "$value": "9999px" }
    }
  }
}
```

**Tier 2 — Semantic** (aliases consumed by blocks)

```json
{
  "color": {
    "$type": "color",
    "text": {
      "primary":   { "$value": "{primitive.color.gray-900}" },
      "secondary": { "$value": "{primitive.color.gray-500}" },
      "inverse":   { "$value": "{primitive.color.white}" },
      "link":      { "$value": "{primitive.color.brand-500}" }
    },
    "surface": {
      "backdrop": { "$value": "{primitive.color.gray-100}" },
      "canvas":   { "$value": "{primitive.color.white}" },
      "accent":   { "$value": "{primitive.color.brand-100}" }
    },
    "action": {
      "primary":       { "$value": "{primitive.color.brand-500}" },
      "primary-hover": { "$value": "{primitive.color.brand-700}" }
    },
    "border": {
      "default": { "$value": "{primitive.color.gray-200}" }
    }
  },
  "font": {
    "family": {
      "heading": {
        "$type": "fontFamily",
        "$value": "{primitive.font.family.heading}"
      },
      "body": {
        "$type": "fontFamily",
        "$value": "{primitive.font.family.body}"
      }
    }
  },
  "typography": {
    "heading-xl": {
      "$type": "typography",
      "$value": {
        "fontFamily":    "{font.family.heading}",
        "fontWeight":    "{primitive.font.weight.bold}",
        "fontSize":      "{primitive.font.size.3xl}",
        "lineHeight":    1.1,
        "letterSpacing": "-1px"
      }
    },
    "heading-lg": {
      "$type": "typography",
      "$value": {
        "fontFamily":    "{font.family.heading}",
        "fontWeight":    "{primitive.font.weight.bold}",
        "fontSize":      "{primitive.font.size.2xl}",
        "lineHeight":    1.2,
        "letterSpacing": "-0.5px"
      }
    },
    "heading-md": {
      "$type": "typography",
      "$value": {
        "fontFamily":    "{font.family.heading}",
        "fontWeight":    "{primitive.font.weight.bold}",
        "fontSize":      "{primitive.font.size.xl}",
        "lineHeight":    1.3,
        "letterSpacing": "0px"
      }
    },
    "body-default": {
      "$type": "typography",
      "$value": {
        "fontFamily":    "{font.family.body}",
        "fontWeight":    "{primitive.font.weight.regular}",
        "fontSize":      "{primitive.font.size.md}",
        "lineHeight":    1.6,
        "letterSpacing": "0px"
      }
    },
    "body-small": {
      "$type": "typography",
      "$value": {
        "fontFamily":    "{font.family.body}",
        "fontWeight":    "{primitive.font.weight.regular}",
        "fontSize":      "{primitive.font.size.sm}",
        "lineHeight":    1.5,
        "letterSpacing": "0px"
      }
    },
    "label": {
      "$type": "typography",
      "$value": {
        "fontFamily":    "{font.family.body}",
        "fontWeight":    "{primitive.font.weight.medium}",
        "fontSize":      "{primitive.font.size.xs}",
        "lineHeight":    1.4,
        "letterSpacing": "0.08em"
      }
    }
  }
}
```

### Token resolution rules

1. Resolve depth-first — an alias pointing to an alias resolves all the way to a literal value
2. Circular references are a schema error — validate on load, reject the token file
3. At render time, **all token references become literal values** — no `var(--token)` in output
4. `tokenOverrides` in the document envelope are merged on top of the base token file before any resolution begins
5. Token references in `_mobile` overrides resolve identically to desktop values
6. Invalid token paths (referencing a non-existent key) resolve to empty string and log a warning

### Token path syntax

```
{group.subgroup.name}
```

Examples:
- `{color.text.primary}` → `#1C1917`
- `{primitive.font.size.xl}` → `24px`
- `{font.family.heading}` → `'GT Alpina', Georgia, serif`

Aliases must be the **entire** `$value` — embedding a reference inside a string (`"rgba({color.primary}, 0.5)"`) is not supported. Use a dedicated token for compound values.

---

## 4. Block Taxonomy

### Layout blocks

#### `Root`

Singleton. The document root node.

```json
{
  "type": "Root",
  "data": {
    "style": {
      "backgroundColor": "{color.surface.backdrop}",
      "fontFamily": "{font.family.body}"
    },
    "childrenIds": ["sec-001", "sec-002"]
  }
}
```

#### `Section`

Full-width row. Top-level structural unit. Can contain any block type including `Columns`.

```json
{
  "type": "Section",
  "data": {
    "props": {
      "anchor": ""
    },
    "style": {
      "backgroundColor": "{color.surface.canvas}",
      "backgroundImage": null,
      "padding": { "top": 24, "bottom": 24, "left": 24, "right": 24 },
      "borderTop": null,
      "borderBottom": null
    },
    "childrenIds": [],
    "_mobile": {}
  }
}
```

#### `Columns`

See [Section 5](#5-columns-block) for full spec.

---

### Content blocks (leaves)

#### `Heading`

```json
{
  "type": "Heading",
  "data": {
    "props": {
      "text": "Currently on view",
      "level": "h2"
    },
    "style": {
      "color": "{color.text.primary}",
      "fontFamily": "{font.family.heading}",
      "fontSize": "{primitive.font.size.2xl}",
      "fontWeight": "{primitive.font.weight.bold}",
      "lineHeight": 1.2,
      "letterSpacing": "-0.5px",
      "textAlign": "left",
      "padding": { "top": 0, "bottom": 12, "left": 0, "right": 0 }
    },
    "_mobile": {
      "style": {
        "fontSize": "{primitive.font.size.xl}",
        "textAlign": "center"
      }
    }
  }
}
```

`level`: `"h1"` | `"h2"` | `"h3"`

#### `Text`

Rich text paragraph. Content stored as an HTML string with inline styles. Supports bold, italic, underline, links. No block-level elements inside.

```json
{
  "type": "Text",
  "data": {
    "props": {
      "html": "<p>Join us for the opening reception on <strong>April 12</strong>.</p>"
    },
    "style": {
      "color": "{color.text.primary}",
      "fontFamily": "{font.family.body}",
      "fontSize": "{primitive.font.size.md}",
      "fontWeight": "{primitive.font.weight.regular}",
      "lineHeight": 1.6,
      "textAlign": "left",
      "padding": { "top": 0, "bottom": 16, "left": 0, "right": 0 }
    },
    "_mobile": {}
  }
}
```

#### `Image`

```json
{
  "type": "Image",
  "data": {
    "props": {
      "src": "https://cdn.example.com/image.jpg",
      "alt": "",
      "width": null,
      "fullWidth": true,
      "linkHref": null,
      "linkTarget": "_blank"
    },
    "style": {
      "align": "center",
      "borderRadius": "{primitive.radius.none}",
      "padding": { "top": 0, "bottom": 0, "left": 0, "right": 0 }
    },
    "_mobile": {}
  }
}
```

`width`: integer px or `null` (full container width). `fullWidth: true` overrides `width` to 100%.

#### `Button`

```json
{
  "type": "Button",
  "data": {
    "props": {
      "text": "View exhibition",
      "href": "{{gallery.website}}/exhibitions/current",
      "target": "_blank",
      "variant": "fill"
    },
    "style": {
      "backgroundColor": "{color.action.primary}",
      "color": "{color.text.inverse}",
      "borderColor": "{color.action.primary}",
      "borderRadius": "{primitive.radius.sm}",
      "fontSize": "{primitive.font.size.sm}",
      "fontWeight": "{primitive.font.weight.medium}",
      "paddingVertical": 12,
      "paddingHorizontal": 24,
      "align": "center",
      "fullWidth": false
    },
    "_mobile": {
      "style": { "fullWidth": true }
    }
  }
}
```

`variant`: `"fill"` | `"outline"` | `"text"`

For `"outline"`: `backgroundColor` is transparent, border uses `borderColor`.
For `"text"`: no background or border, renders as a styled link.

#### `Divider`

```json
{
  "type": "Divider",
  "data": {
    "props": {
      "lineStyle": "solid"
    },
    "style": {
      "lineColor": "{color.border.default}",
      "lineThickness": 1,
      "width": "100%",
      "padding": { "top": 16, "bottom": 16, "left": 0, "right": 0 }
    },
    "_mobile": {}
  }
}
```

`lineStyle`: `"solid"` | `"dashed"` | `"dotted"`

#### `Spacer`

```json
{
  "type": "Spacer",
  "data": {
    "props": { "height": 32 },
    "_mobile": {
      "props": { "height": 16 }
    }
  }
}
```

No `style` object — only `height` (integer px).

#### `Html`

```json
{
  "type": "Html",
  "data": {
    "props": {
      "html": "<table>...</table>"
    }
  }
}
```

Raw HTML. Not processed by the token system. Not styled. Power-user escape hatch only.

#### `SocialLinks`

```json
{
  "type": "SocialLinks",
  "data": {
    "props": {
      "items": [
        { "platform": "instagram", "url": "https://instagram.com/...", "label": "Instagram" },
        { "platform": "facebook",  "url": "https://facebook.com/...",  "label": "Facebook" }
      ],
      "iconStyle": "circle",
      "iconSize": 32
    },
    "style": {
      "align": "center",
      "gap": 12,
      "iconColor": "{color.text.secondary}",
      "padding": { "top": 16, "bottom": 16, "left": 0, "right": 0 }
    },
    "_mobile": {}
  }
}
```

`platform`: `"instagram"` | `"facebook"` | `"twitter"` | `"linkedin"` | `"youtube"` | `"vimeo"` | `"tiktok"` | `"website"`

`iconStyle`: `"circle"` | `"square"` | `"none"` (logo mark only, no background shape)

#### `UnsubscribeFooter`

Pre-composed footer block. **Locked — not deletable, not movable.** Always the last block in `root.childrenIds`.

```json
{
  "type": "UnsubscribeFooter",
  "data": {
    "props": {
      "addressLine": "{{gallery.address}}",
      "unsubscribeText": "Unsubscribe",
      "preferencesText": "Manage preferences"
    },
    "style": {
      "backgroundColor": "{color.surface.backdrop}",
      "color": "{color.text.secondary}",
      "fontFamily": "{font.family.body}",
      "fontSize": "{primitive.font.size.xs}",
      "textAlign": "center",
      "padding": { "top": 24, "bottom": 24, "left": 24, "right": 24 }
    },
    "_mobile": {}
  }
}
```

Merge tags `{{subscriber.unsubscribe_url}}` and `{{subscriber.preferences_url}}` are injected by the renderer automatically — they do not need to be in the document.

---

### Gallery blocks (leaves with model snapshot)

Gallery blocks store a `snapshot` of the model data at time of placement. The snapshot is what renders. The model ID is retained for the "Refresh from model" editor action.

#### `FeaturedArtwork`

```json
{
  "type": "FeaturedArtwork",
  "data": {
    "props": {
      "artworkId": 42,
      "imagePosition": "left",
      "showPrice": false,
      "linkToGallery": true,
      "snapshot": {
        "title": "Untitled (Red Field)",
        "artistName": "Jane Smith",
        "year": 2023,
        "medium": "Oil on canvas",
        "dimensions": "48\" × 60\"",
        "price": "NFS",
        "imageUrl": "https://cdn.example.com/artworks/42-medium.jpg",
        "imageAlt": "Abstract painting with large red field"
      }
    },
    "style": {
      "backgroundColor": "{color.surface.canvas}",
      "labelColor": "{color.text.secondary}",
      "titleColor": "{color.text.primary}",
      "metaColor": "{color.text.secondary}",
      "padding": { "top": 24, "bottom": 24, "left": 24, "right": 24 }
    },
    "_mobile": {
      "props": { "imagePosition": "top" }
    }
  }
}
```

`imagePosition`: `"left"` | `"right"` | `"top"`

`_mobile` defaults to `imagePosition: "top"` (image above text when stacked).

#### `ExhibitionDetails`

```json
{
  "type": "ExhibitionDetails",
  "data": {
    "props": {
      "exhibitionId": 17,
      "showDates": true,
      "showDescription": true,
      "snapshot": {
        "title": "Presence / Absence",
        "artistNames": ["Jane Smith", "Wei Chen"],
        "startDate": "2026-04-05",
        "endDate": "2026-05-18",
        "location": "Main Gallery",
        "description": "An exploration of negative space and material absence...",
        "coverImageUrl": "https://cdn.example.com/exhibitions/17-cover.jpg",
        "coverImageAlt": "Installation view of Presence / Absence"
      }
    },
    "style": {
      "backgroundColor": "{color.surface.accent}",
      "titleColor": "{color.text.primary}",
      "metaColor": "{color.text.secondary}",
      "descriptionColor": "{color.text.primary}",
      "padding": { "top": 32, "bottom": 32, "left": 24, "right": 24 }
    },
    "_mobile": {}
  }
}
```

#### `ArtistFeature`

```json
{
  "type": "ArtistFeature",
  "data": {
    "props": {
      "artistId": 8,
      "showBio": true,
      "bioTruncate": 180,
      "snapshot": {
        "name": "Jane Smith",
        "bio": "Jane Smith is a painter based in Los Angeles whose work...",
        "portraitUrl": "https://cdn.example.com/artists/8-portrait.jpg",
        "portraitAlt": "Portrait of Jane Smith",
        "website": "https://janesmith.com"
      }
    },
    "style": {
      "backgroundColor": "{color.surface.canvas}",
      "nameColor": "{color.text.primary}",
      "bioColor": "{color.text.secondary}",
      "padding": { "top": 24, "bottom": 24, "left": 24, "right": 24 }
    },
    "_mobile": {}
  }
}
```

---

## 5. Columns Block

Full spec for the `Columns` layout block.

```json
{
  "type": "Columns",
  "data": {
    "props": {
      "preset": "one-third-two-thirds",
      "widths": [4, 8],
      "gap": 24,
      "verticalAlign": "top",
      "mobileStack": true,
      "mobileOrder": [1, 0]
    },
    "style": {
      "backgroundColor": null,
      "padding": { "top": 0, "bottom": 0, "left": 0, "right": 0 }
    },
    "columns": [
      { "childrenIds": ["img-x7r1q"] },
      { "childrenIds": ["head-p2m4k", "text-n8q3z", "btn-j5w9v"] }
    ],
    "_mobile": {
      "props": { "gap": 16 }
    }
  }
}
```

### Column presets

| `preset` | `widths` | Label | Notes |
|---|---|---|---|
| `full` | `[12]` | Full width | Single column — use Section instead unless you need column-specific styling |
| `half` | `[6, 6]` | Half / Half | |
| `thirds` | `[4, 4, 4]` | Equal thirds | |
| `quarters` | `[3, 3, 3, 3]` | Equal quarters | |
| `one-third-two-thirds` | `[4, 8]` | 1/3 → 2/3 | Image + content pattern |
| `two-thirds-one-third` | `[8, 4]` | 2/3 → 1/3 | Content + image pattern |
| `sidebar-left` | `[3, 9]` | Narrow left sidebar | |
| `sidebar-right` | `[9, 3]` | Narrow right sidebar | |
| `custom` | `[n, ...]` sum = 12 | Free | Set by drag-resize in editor |

When a preset is selected, `widths` is set automatically. When columns are drag-resized to a non-preset ratio, `preset` becomes `"custom"`.

Widths are fractions of a 12-unit grid. Values must be positive integers summing to exactly 12.

### Props reference

| Prop | Type | Default | Description |
|---|---|---|---|
| `preset` | string | `"half"` | Named layout; see table above |
| `widths` | int[] | `[6, 6]` | Column widths as 12-grid fractions |
| `gap` | integer (px) | `24` | Horizontal gap between columns |
| `verticalAlign` | string | `"top"` | Vertical alignment of column content: `"top"` / `"middle"` / `"bottom"` |
| `mobileStack` | boolean | `true` | Collapse to single column on mobile |
| `mobileOrder` | int[] | `[0, 1, ...]` | Column index order when stacked on mobile |

### Mobile behavior

- `mobileStack: true` — columns collapse below 480px, stacking vertically in `mobileOrder` sequence
- `mobileStack: false` — columns stay side-by-side at all widths (use sparingly; narrow columns break on small screens)
- `mobileOrder: [1, 0]` — puts column B above column A when stacked (image-below-text → image-above-text on mobile)
- Individual blocks within columns can have their own `_mobile` overrides independent of the column's stacking behavior

---

## 6. Mobile Override System

### Overview

Follows Unlayer's sparse diff pattern. `_mobile` is an optional key at the `data` level of any block. It contains only the properties that differ from the desktop values — not a full copy of `data`.

The mobile breakpoint is **480px**.

### Merge behavior

At render time, when producing mobile output:

```
resolved_data = deep_merge(block.data, block.data._mobile)
```

Keys present in `_mobile.style` override `data.style`. Keys absent from `_mobile` inherit desktop values unchanged. `_mobile` itself is stripped before rendering.

### Hide on mobile

```json
"_mobile": {
  "hidden": true
}
```

`hidden: true` in `_mobile` omits the block from mobile output entirely. Rendered via:

```css
@media screen and (max-width: 480px) {
  .blk-{id} { display: none !important; }
}
```

### Hide on desktop

```json
"props": { "hideDesktop": true }
```

Block is omitted from desktop render but appears in mobile output. Use for mobile-only content (e.g. a stacked layout version of a complex desktop section).

### Example — heading with mobile size and alignment override

```json
"head-p2m4k": {
  "type": "Heading",
  "data": {
    "props": { "text": "Currently on view", "level": "h2" },
    "style": {
      "fontSize": "{primitive.font.size.2xl}",
      "textAlign": "left"
    },
    "_mobile": {
      "style": {
        "fontSize": "{primitive.font.size.xl}",
        "textAlign": "center"
      }
    }
  }
}
```

### CSS strategy for mobile

Token-derived styles are always written as `style=""` attributes — no class-based CSS.

Mobile overrides are the **one exception**: they are emitted as a `@media` block in `<style>` in `<head>`, using generated class names derived from block IDs:

```html
<style>
  @media screen and (max-width: 480px) {
    .blk-head-p2m4k { font-size: 24px !important; text-align: center !important; }
    .blk-cols-k3n2p-col-0 { display: block !important; width: 100% !important; }
    .blk-cols-k3n2p-col-1 { display: block !important; width: 100% !important; }
  }
</style>
```

Outlook ignores media queries — Outlook users receive the desktop layout. All other major clients support the mobile breakpoint.

---

## 7. Merge Tag System

### Two resolution passes

**Pass 1 — Newsletter-level** (Python, once per send, before batching)

Resolved against newsletter and site settings data. Same output for all recipients.

| Tag | Source | Example output |
|---|---|---|
| `{{newsletter.title}}` | `Newsletter.title` | `"March 2026 — From the Gallery"` |
| `{{newsletter.sent_date}}` | `Newsletter.sent_at` (formatted) | `"March 31, 2026"` |
| `{{gallery.name}}` | `EmailSettings.gallery_name` | `"This is a House Gallery"` |
| `{{gallery.website}}` | `EmailSettings.gallery_website` | `"https://thisisahousegallery.com"` |
| `{{gallery.address}}` | `EmailSettings.gallery_address` | `"123 Main St, Portland OR 97201"` |

**Pass 2 — Subscriber-level** (Python, per-recipient in send loop)

Resolved per subscriber. Each recipient gets unique output.

| Tag | Source | Notes |
|---|---|---|
| `{{subscriber.first_name}}` | `Subscriber.first_name` | Supports fallback syntax |
| `{{subscriber.email}}` | `Subscriber.email` | |
| `{{subscriber.unsubscribe_url}}` | Generated per-token | `{base_url}/newsletter/unsubscribe/{token}` |
| `{{subscriber.preferences_url}}` | Generated per-token | `{base_url}/newsletter/preferences/{token}` |

### Fallback syntax

```
{{subscriber.first_name | "friend"}}
```

If the value is null or empty string, the fallback is used. Fallback is a double-quoted string literal.

```python
import re

MERGE_TAG_RE = re.compile(r'\{\{(\w+\.\w+)(?:\s*\|\s*"([^"]*)")?\}\}')

def resolve_subscriber_tags(html: str, data: dict) -> str:
    def replace(m):
        key = m.group(1)
        fallback = m.group(2) or ""
        parts = key.split(".", 1)
        value = data.get(parts[0], {}).get(parts[1]) if len(parts) == 2 else None
        return str(value) if value else fallback
    return MERGE_TAG_RE.sub(replace, html)
```

### Merge tags in the editor

- Tags are stored as literal `{{tag}}` strings in `Text`, `Heading`, `Button`, and footer block content
- Editor renders tags as highlighted inline pills (visually distinct from surrounding text)
- Desktop preview substitutes newsletter-level tags with real values; subscriber-level tags render as `[First Name]`, `[Email]` placeholders
- A merge tag picker dropdown in the text toolbar exposes available tags grouped by category

---

## 8. Rendering Pipeline

### Client-side (vanilla JS, live preview)

```
document + tokens
  → merge tokenOverrides onto tokens
  → resolveTokens(document, mergedTokens)     // {path} → literal string, depth-first
  → if mobilePreview: applyMobileOverrides(document)
  → renderBlock("root", resolvedDocument)     // recursive, returns HTML string
  → collectMobileCSS(document)               // build @media block from _mobile diffs
  → wrapEnvelope(html, mobileCSS, meta)       // <!DOCTYPE html>...<style>...</style>
  → inject into preview <iframe srcdoc="...">
```

The preview iframe is fully re-rendered on every document change. No partial DOM patching — the preview is always a pixel-accurate email render.

### Server-side (Python, send-time)

```
document + tokens + newsletter + subscribers
  → merge tokenOverrides onto tokens
  → resolve_tokens(document, tokens)          // identical logic to JS resolver
  → render_document(document)                // block renderers → HTML string
  → collect_mobile_css(document)             // @media block
  → wrap_envelope(html, mobile_css, meta)    // <!DOCTYPE html>
  → substitute_newsletter_tags(html, newsletter, settings)   // Pass 1 — once
  → for each recipient:
      html_out = substitute_subscriber_tags(html, subscriber) // Pass 2 — per recipient
      send(html_out, subscriber.email)
```

### Token resolver (pseudocode — implement identically in JS and Python)

```
function resolveValue(value, tokens, depth=0):
  if depth > 10: raise CircularReferenceError
  if value is string and matches /^\{[\w.]+\}$/:
    path = value[1:-1].split(".")
    referenced = getTokenAtPath(tokens, path)
    if referenced is None: return ""          // log warning
    return resolveValue(referenced.$value, tokens, depth+1)
  return value                                // literal — return as-is

function resolveTokens(document, tokens):
  for each block in document:
    for each value in block.data.style:
      block.data.style[key] = resolveValue(value, tokens)
    for each value in block.data._mobile.style (if exists):
      block.data._mobile.style[key] = resolveValue(value, tokens)
  return document
```

### CSS output strategy

| Style type | Output mechanism |
|---|---|
| Token-derived block styles | `style=""` attribute — inline, no class needed |
| Mobile override styles | `@media (max-width: 480px)` block in `<head><style>` |
| Column stacking on mobile | Generated class + `@media` block per Columns block |
| `Html` block raw content | Pass through `css-inline` (Python, Rust-backed) if the block contains `<style>` tags |

No external CSS inliner (`juice`, `premailer`) is needed for the standard rendering path. `css-inline` is imported as an optional dependency only for the `Html` escape hatch.

---

## 9. Open UX Decisions

The following are intentionally not defined in this spec — they are UX design decisions.

### Editor layout
- Panel arrangement and proportions (canvas vs. sidebars)
- How the block selection state is communicated visually
- Whether property panels are persistent or popover-style
- Toolbar placement and contents

### Block insertion
- How blocks are discovered and added (drag from palette? click to insert? slash command? all three?)
- How the block palette is organized (flat list, grouped by category, searchable?)
- How gallery blocks are differentiated from standard content blocks

### Property panel
- How token references are selected — does the user see `{color.text.primary}` or a resolved color swatch?
- How token overrides vs. literal values are expressed (can a user break out of the token system for one block?)
- How composite typography tokens are applied (one-click apply a full `typography` token vs. individual fields)

### Gallery block UX
- How the artwork/exhibition/artist picker modal works (search, filters, preview)
- Where the "Refresh from model" affordance lives and how it communicates staleness
- What happens when the referenced model is deleted

### Column editing
- How the preset picker is presented (visual grid thumbnails vs. dropdown vs. both)
- How custom column width drag-resize works
- How `mobileOrder` is expressed visually (drag to reorder a mobile stack preview?)

### Mobile preview
- How the desktop ↔ mobile preview toggle is positioned and animated
- Whether mobile preview shows the actual rendered output or a wireframe approximation

### Merge tags
- Keyboard shortcut or slash command for inserting tags inline
- How tag validation is shown (tag for a missing field, tag with no fallback on a nullable field)

### Editor state
- Undo/redo depth and visual indicator
- Autosave behavior and cadence
- "Unsaved changes" indicator and save confirmation

### Token editor
- How gallery staff edit token values (visual color pickers? raw JSON editor? Figma sync?)
- Whether primitive and semantic tiers are exposed separately or as a unified view
- How `tokenOverrides` in a specific newsletter are edited (inline in the editor? separate panel?)

---

*Last updated: 2026-03-31*
*See also: [`PROJECT_EPIC_HEADLESS_CMS_API.md`](../PROJECT_EPIC_HEADLESS_CMS_API.md) for the broader Starlette rewrite context.*
