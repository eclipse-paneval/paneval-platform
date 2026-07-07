# PanEval Docs

PanEval Docs is a VitePress documentation site for the PanEval platform user manual.

## Project Structure

```text
.
├── docs/
│   ├── .vitepress/
│   │   ├── config.mts
│   │   └── theme/
│   └── src/
│       ├── index.md
│       └── manual/
├── package.json
└── pnpm-lock.yaml
```

Markdown files are stored under `docs/src` because VitePress is configured with `srcDir: 'src'`.

## Development

Install dependencies:

```sh
pnpm install
```

Start the local documentation server:

```sh
pnpm run docs:dev
```

Build the static site:

```sh
pnpm run docs:build
```

Preview the production build:

```sh
pnpm run docs:preview
```

## Documentation Content

The main documentation pages are in `docs/src/manual`:

- `platform-overview.md`
- `basic-concepts.md`
- `quick-start.md`
- `evaluation-operation-process.md`
- `faq.md`
- `contact-us.md`

Update the navigation and sidebar in `docs/.vitepress/config.mts` when adding or removing documentation pages.

## Asset Naming

Use lowercase file extensions for image assets, for example `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, and `.svg`.
