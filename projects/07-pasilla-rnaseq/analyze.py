"""Explore gene-level Pasilla knockdown RNA-seq counts. Run with Python 3, numpy and pandas."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "reports"
SOURCE = "https://raw.githubusercontent.com/bioc/pasilla/3c91e8df8add3549129e46b7a7a078fda4e2755a/inst/extdata/"


def input_file(name, blob_sha):
    DATA.mkdir(exist_ok=True)
    path = DATA / name
    if not path.exists():
        path.write_bytes(urlopen(SOURCE + name, timeout=60).read())
    # Canonicalize line endings so Windows checkouts give the same Git blob hash.
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == blob_sha
    return path


def main():
    OUT.mkdir(exist_ok=True)
    counts = pd.read_csv(input_file("pasilla_gene_counts.tsv", "2b97b671474cc8a22e934ed3466d16d8726b25fd"), sep="\t", index_col=0)
    meta = pd.read_csv(input_file("pasilla_sample_annotation.csv", "05cfa1573c8294093429a4ff21ec3556287f4c53"))
    meta.index = meta.file.str.removesuffix("fb")
    assert counts.index.is_unique and meta.index.is_unique and set(counts) == set(meta.index)
    meta = meta.loc[counts.columns]
    assert counts.notna().all().all() and (counts >= 0).all().all()
    sizes = counts.sum()
    keep = (counts >= 10).sum(axis=1) >= 3
    log_cpm = np.log2(1 + counts.loc[keep].div(sizes, axis="columns") * 1_000_000)
    # Sample-level PCA on centered log-CPM for the 500 most variable genes.
    top = log_cpm.var(axis=1).nlargest(500).index
    X = log_cpm.loc[top].T.to_numpy()
    U, s, _ = np.linalg.svd(X - X.mean(axis=0), full_matrices=False)
    fraction = s**2 / (s**2).sum()
    scores = U[:, :2] * s[:2]
    paired = meta.type.eq("paired-end")
    treated = meta.condition.eq("treated")
    assert pd.crosstab(paired, treated).shape == (2, 2) and pd.crosstab(paired, treated).min().min() > 0
    # One common treatment contrast, with a separate intercept for sequencing layout.
    design = np.column_stack([np.ones(len(meta)), paired, treated])
    assert np.linalg.matrix_rank(design) == 3
    beta = np.linalg.lstsq(design, log_cpm.T, rcond=None)[0][2]
    contrast = pd.DataFrame({"gene": log_cpm.index, "adjusted_log2_cpm_difference": beta})
    contrast["absolute_difference"] = np.abs(beta)
    ranked = contrast.sort_values("absolute_difference", ascending=False).head(20)
    ranked.to_csv(OUT / "largest_contrasts.csv", index=False, float_format="%.4f")
    samples = meta.loc[:, ["condition", "type"]].assign(count_sum=sizes, PC1=scores[:, 0], PC2=scores[:, 1])
    samples.rename_axis("sample").to_csv(OUT / "samples.csv", float_format="%.4f")
    # Inline SVG has no plotting dependency. Labels identify each sample directly.
    def scale(values, lo, hi):
        return lo + (hi-lo) * (values-values.min()) / np.ptp(values)
    colors = {"treated":"#a84219", "untreated":"#245d89"}
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420" role="img"><title>Sample PCA of Pasilla RNA-seq counts</title><rect width="760" height="420" fill="white"/>',
           '<g font-family="sans-serif" fill="#1e293b"><text x="50" y="30" font-size="21">Pasilla RNA-seq | sample PCA</text>',
           '<text x="50" y="55">Blue: untreated · Orange: knockdown · Circles: single-read · Squares: paired-end</text>',
           '<path d="M55 80V355H710" stroke="#64748b" fill="none"/>',
           f'<text x="310" y="398">PC1 ({fraction[0]:.1%})</text><text x="19" y="250" transform="rotate(-90 19 250)">PC2 ({fraction[1]:.1%})</text>']
    for (sample, row), x, y in zip(samples.iterrows(), scale(scores[:,0],100,635), scale(scores[:,1],325,110)):
        color = colors[row.condition]
        mark = f'<rect x="{x-5}" y="{y-5}" width="10" height="10"' if row.type == "paired-end" else f'<circle cx="{x}" cy="{y}" r="5"'
        svg.append(f'{mark} fill="{color}"/><text x="{x+8}" y="{y-6}" font-size="12">{escape(sample)}</text>')
    (OUT / "pca.svg").write_text("\n".join(svg + ["</g></svg>"]), encoding="utf-8")
    print(len(counts), keep.sum(), fraction[:2], ranked.head(3).to_string(index=False), samples.to_string(), sep="\n")


if __name__ == "__main__":
    main()
