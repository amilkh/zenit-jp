# ZenIT archive

Static archive of the ZenIT website and its 2018–2019 activities. The site is
designed for GitHub Pages at `https://zenit.jp` and contains local copies of
the original public Wix-hosted images.

## Publishing

1. Create the public GitHub repository `amilkh/zenit-jp`.
2. Push this directory to the repository's `main` branch.
3. Enable GitHub Pages from the root of `main`.
4. Confirm the custom domain is `zenit.jp` and enable HTTPS.

Only the web DNS records should be changed. Preserve all Google Workspace MX
records and any mail-related TXT records.

## Rebuilding

The `archive/` directory contains the captured public source material. Run:

```sh
/usr/bin/python3 scripts/build_site.py
```

The migration scripts are retained for provenance; routine site operation does
not depend on Wix or Python.
