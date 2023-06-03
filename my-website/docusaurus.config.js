const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

// With JSDoc @type annotations, IDEs can provide config autocompletion
/** @type {import('@docusaurus/types').DocusaurusConfig} */
(module.exports = {
  title: 'Quadroid',
  tagline: 'The Smart AI Voice Assistant To Help Humans',
  url: 'https:/Curious-Squad.github.io',
  baseUrl: '/quadroid-docs/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'Curious-Squad', // Usually your GitHub org/user name.
  projectName: 'quadroid-docs', // Usually your repo name.

  presets: [
    [
      '@docusaurus/preset-classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // editUrl: 'https://github.com/Curious-Squad',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'Quadroid',
        logo: {
          alt: 'My Site Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'doc',
            docId: 'beginners/intro',
            position: 'left',
            label: 'Beginner',
          },
          {
            type: 'doc',
            docId: 'developers/intro',
            position: 'left',
            label: 'Developer',
          },
          {
            href: 'https://github.com/Curious-Squad',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      trailingSlash: true, // Add this line to enable trailing slashes
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Beginners',
                to: '/docs/beginners/intro',
              },
              {
                label: 'Developers',
                to: '/docs/developers/intro',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Stack Overflow',
                href: '#',
              },
              {
                label: 'Discord',
                href: '#',
              },
              {
                label: 'Twitter',
                href: '#',
              },
            ],
          },
          {
            title: 'More',
            items: [
              /*{
                label: 'Blog',
                to: '/blog',
              },*/
              {
                label: 'GitHub',
                href: 'https://github.com/Curious-Squad',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} <a href="https://github.com/Curious-Squad/Quadroid" target="_blank">Quadroid</a>`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
});
