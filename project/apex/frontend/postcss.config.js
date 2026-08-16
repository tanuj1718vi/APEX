// This project does not use PostCSS plugins (no Tailwind, no
// autoprefixer). This file exists purely so PostCSS's config
// resolver stops its upward directory search *here* instead of
// climbing into a parent folder (e.g. Downloads/) and picking up an
// unrelated postcss.config.js from a different project.
export default {
  plugins: {},
};
