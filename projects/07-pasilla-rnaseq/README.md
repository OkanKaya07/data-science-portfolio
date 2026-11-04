# Pasilla knockdown RNA-seq in Drosophila cells

I asked whether gene expression differed between Pasilla knockdown and untreated cells, and whether sequencing layout could affect that comparison.

## Step-by-step walkthrough

1. **Align counts with sample labels.** I matched each Drosophila RNA-seq count column to its treatment and sequencing-layout annotation. Of 14,599 genes, 8,148 had at least ten counts in three or more libraries.
2. **Normalize and compare samples.** I used pandas to calculate log2(1 + counts per million), then NumPy SVD on the 500 most variable genes. Sequencing layout remained visible in the sample metadata. [Open the implementation](analyze.py#L37-L43).

![Source walkthrough showing the input, method and exact code excerpt](walkthrough/source.png)

3. **Inspect the output.** Open [samples.csv](reports/samples.csv) and the [analysis figure](reports/pca.svg). The browser capture below shows values from that artifact.
4. **Interpret the result.** PC1 (52.6%) separates the three knockdown libraries from the four controls. PC2 (32.1%) separates read layouts. Both patterns matter when interpreting a gene-level comparison in seven samples.

![Output walkthrough showing measured values and their interpretation](walkthrough/result.png)

## Data and method

I used the [Bioconductor pasilla gene counts and sample annotations](https://github.com/bioc/pasilla/tree/3c91e8df8add3549129e46b7a7a078fda4e2755a/inst/extdata) from the Brooks et al. experiment. The inputs are gene-level counts, already aligned and summarized. There are four untreated libraries and three knockdown libraries. Both groups include single-read and paired-end libraries.

I used **pandas** to match sample identifiers, inspect library sizes, and retain 8,148 of 14,599 genes with at least 10 counts in at least three libraries. I divided counts by the original library totals and applied log2(1 + counts per million). With **NumPy**, I centered the 500 most variable genes across samples and computed a singular value decomposition for PCA. I then fitted a separate descriptive linear model per retained gene, estimating the knockdown-minus-control difference after accounting for read layout.

![Sample PCA with condition shown by color and sequencing layout by shape](reports/pca.svg)

## What the figure tells us

Each point is one library. Along PC1 (52.6%), all three knockdown samples sit apart from the four controls. Along PC2 (32.1%), the single-read samples sit apart from the paired-end samples. Both condition and sequencing layout matter when reading these seven samples. The first two axes together capture 84.7% of variation among these 500 genes. This pattern motivates including layout in the gene comparison. PCA does not establish which genes respond directly to knockdown.

## What the gene comparison tells us

**FBgn0039155** had the largest absolute adjusted difference, **−4.24** on the log2(1 + CPM) scale. Its normalized expression was lower in knockdown libraries after accounting for layout. This is an exploratory ranking by effect size. The small experiment and simple library-size normalization limit the conclusion. A differential-expression significance analysis would require a count model with dispersion estimates and multiple-testing correction. Gene counts also cannot resolve exon-level splicing changes.

[Sample scores and library totals](reports/samples.csv) · [Top 20 descriptive contrasts](reports/largest_contrasts.csv) · [Analysis code](analyze.py)

## Reproduce

From the repository root, run the following with Python 3.12. The script downloads the two study files from a pinned commit, checks their Git blob hashes, then regenerates the CSVs and SVG. Tested with NumPy 2.3.5 and pandas 3.0.1.

```sh
python -m pip install numpy==2.3.5 pandas==3.0.1
python projects/07-pasilla-rnaseq/analyze.py
```

**Source:** Brooks et al., *Conservation of an RNA regulatory map between Drosophila and mammals* (2011). [Bioconductor dataset and citation](https://bioconductor.org/packages/pasilla/). Input data retain their original terms.
