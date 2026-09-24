# Muqing Zheng

Personal website: [mqzh.science](https://mqzh.science/).

A static site built with Node.js, with pages for biography, professional experience, projects, and publications.

## Local development

Clone [Starfield Skill Planner](https://github.com/Firepanda415/Starfield_SkillTree_Generator) and [WARDOGS Map & Range Tool](https://github.com/Firepanda415/MZ-Wardogs) alongside this repository, or set `SF_SKILLS_DIR` and `WDTOOL_DIR` to their local directories. The build includes them at `/sfskills/` and `/wdtool/`.

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
- `site.js`: biography copy button and explainer video player.
- `explainers/`: narrated explainer videos with burned-in subtitles and their posters, built from `animations/` (see `animations/README.md`).

## Build and deployment

```sh
npm test
npm run build
```

Generated files are written to `dist/`. Pushes to `main` are tested and deployed to GitHub Pages by `.github/workflows/pages.yml`.

The deployment fetches both tool repositories each time. Each tool repository triggers this workflow when a commit is pushed to `main`.

For cross-repository publishing, create a fine-grained GitHub token restricted to `Firepanda415/personal-website`, with repository permission **Actions: Read and write**. Save it as the Actions secret `WEBSITE_PUBLISH_TOKEN` in both tool repositories. Renew the secret when the token expires. The default `GITHUB_TOKEN` cannot trigger workflows in another repository.

You can also run the Publish website workflow manually to refresh both tools.
