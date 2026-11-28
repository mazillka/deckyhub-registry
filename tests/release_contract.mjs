// Run the plugin's actual pure filters against the same examples as validate.py.
import { pathToFileURL } from 'node:url';
const { matchingAssets, matchesReleaseTag } = await import(pathToFileURL(process.argv[2]).href);
const { inChannel } = await import(pathToFileURL(process.argv[3]).href);
let input = '';
for await (const chunk of process.stdin) input += chunk;
const cases = JSON.parse(input);
const result = cases.map(({ app, releases }) => {
  const selected = releases.filter(r => !r.draft && matchesReleaseTag(r.tag_name || r.name, app.releaseTagInclude))
    .map(r => ({ ...r, assets: matchingAssets(app, r.assets) }))
    .filter(r => r.assets.length)
    .sort((a, b) => (Date.parse(b.published_at || '') || 0) - (Date.parse(a.published_at || '') || 0));
  return Object.fromEntries(['stable', 'prerelease'].map(channel => {
    const r = selected.find(item => inChannel(item, channel));
    return [channel, r ? { tag: r.tag_name || r.name, assets: r.assets.map(a => a.name) } : null];
  }));
});
process.stdout.write(JSON.stringify(result));
