# Muqing Zheng

Personal website: [mqzh.science](https://mqzh.science/).

A static site built with Node.js, with pages for biography, professional experience, projects, and publications.

## Local development

The site serves three tools from separate repositories. For a local build, check out a tool next to this repository or set the corresponding environment variable. The build skips tools that are absent. An explicitly configured directory must exist.

| Tool | Site path | Source directory override |
| --- | --- | --- |
| [Starfield Skill Planner](https://github.com/Firepanda415/Starfield_SkillTree_Generator) | `/sfskills/` | `SF_SKILLS_DIR` |
| [WARDOGS Map & Range Tool](https://github.com/Firepanda415/MZ-Wardogs) | `/wdtool/` | `WDTOOL_DIR` |
| [Stellaris Atlas](https://github.com/Firepanda415/stellaris_save_visualization) | `/stellaris/` | `STELLARIS_DIR` |

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

Each deployment fetches the three tool repositories. Starfield and WARDOGS also trigger this workflow when a commit is pushed to their `main` branches.

For cross-repository publishing, create a fine-grained GitHub token restricted to `Firepanda415/personal-website`, with repository permission **Actions: Read and write**. Save it as the Actions secret `WEBSITE_PUBLISH_TOKEN` in the Starfield and WARDOGS repositories. Renew the secret when the token expires. The default `GITHUB_TOKEN` cannot trigger workflows in another repository.

Run the Publish website workflow manually to pick up a Stellaris Atlas update or refresh all three tools.
