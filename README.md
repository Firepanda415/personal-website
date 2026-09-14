# Muqing Zheng

Personal website: [mqzh.science](https://mqzh.science/).

A static site built with Node.js, with pages for biography, professional experience, projects, and publications.

## Local development

Clone [Starfield Skill Planner](https://github.com/Firepanda415/Starfield_SkillTree_Generator) alongside this repository, or set "SF_SKILLS_DIR" to its local directory. The build includes it at /sf_skills/.

```sh
conda env create -f environment.yml
conda activate personal-website
npm run dev
```

Open http://127.0.0.1:4173. Run `npm run build` and refresh the browser after editing.

## Source files

- `data.mjs`: biography, projects, and publications.
- `build.mjs`: HTML generation and page content.
- `style.css`: layout and typography.
- `site.js`: biography copy button.

## Build and deployment

```sh
npm test
npm run build
```

Generated files are written to `dist/`. Pushes to `main` are tested and deployed to GitHub Pages by `.github/workflows/pages.yml`.

The deployment fetches the planner repository each time. After planner updates, run the Publish website workflow to refresh the hosted copy.
