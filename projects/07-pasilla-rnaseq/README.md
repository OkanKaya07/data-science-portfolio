# Exploring Pasilla RNA-seq counts

[← All projects](../../README.md#projects) · [Source code](analyze.py) · [Results](reports/samples.csv)

**Tools** · Python · pandas · NumPy

This analysis compares three Pasilla knockdown libraries with four controls. It also checks how single-read and paired-end sequencing relate to the sample differences.

## Questions I wanted to answer

1. How do the seven libraries differ after accounting for library size?
2. Do the main sample patterns align with knockdown status, sequencing layout, or both?
3. Which genes have the largest descriptive knockdown differences after adjusting for layout?

## Tools and why I used them

| Tool | Role in this project |
|---|---|
| pandas | Read count and annotation files, align sample IDs, filter low-count genes and export tables |
| NumPy | Transform normalized counts, compute PCA through SVD and fit the layout-adjusted linear model |
| Python standard library | Download pinned inputs, verify Git blob hashes and write the labeled SVG plot |

The figure is generated as SVG directly; this script does not use Matplotlib, Seaborn or a differential-expression package.

## Step-by-step walkthrough

1. **Align counts with sample labels.** I matched each Drosophila RNA-seq count column to its treatment and sequencing-layout annotation. Of 14,599 genes, 8,148 had at least ten counts in three or more libraries.
2. **Normalize and compare samples.** I used pandas to calculate log2(1 + counts per million), then NumPy SVD on the 500 most variable genes. Sequencing layout remained visible in the sample metadata. [Open the implementation](analyze.py#L37-L43).

```python
log_cpm = np.log2(1 + counts.loc[keep].div(sizes, axis="columns") * 1_000_000)
# Sample-level PCA on centered log-CPM for the 500 most variable genes.
top = log_cpm.var(axis=1).nlargest(500).index
X = log_cpm.loc[top].T.to_numpy()
U, s, _ = np.linalg.svd(X - X.mean(axis=0), full_matrices=False)
fraction = s**2 / (s**2).sum()
scores = U[:, :2] * s[:2]
```

<details>
<summary>Open the annotated code screenshot</summary>

![Source walkthrough showing the input, method and exact code excerpt](walkthrough/source.png)

</details>

3. **Inspect the output.** Open [samples.csv](reports/samples.csv) and the [analysis figure](reports/pca.svg). The screenshot puts the saved output beside a short explanation.
4. **Interpret the result.** PC1 (52.6%) separates the three knockdown libraries from the four controls. PC2 (32.1%) separates read layouts. Both patterns matter when interpreting a gene-level comparison in seven samples.

![Output walkthrough showing measured values and their interpretation](walkthrough/result.png)

## Data and method

I used the [Bioconductor pasilla gene counts and sample annotations](https://github.com/bioc/pasilla/tree/3c91e8df8add3549129e46b7a7a078fda4e2755a/inst/extdata) from the Brooks et al. experiment. The inputs are gene-level counts, already aligned and summarized. There are four untreated libraries and three knockdown libraries. Both groups include single-read and paired-end libraries.

I used **pandas** to match sample identifiers, inspect library sizes, and retain 8,148 of 14,599 genes with at least 10 counts in at least three libraries. I divided counts by the original library totals and applied log2(1 + counts per million). With **NumPy**, I centered the 500 most variable genes across samples and computed a singular value decomposition for PCA. I then fitted a separate descriptive linear model per retained gene, estimating the knockdown-minus-control difference after accounting for read layout.

![Sample PCA with condition shown by color and sequencing layout by shape](reports/pca.svg)


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

## What I learned

- **Sample alignment comes before statistics.** The count matrix and annotation table must refer to the same samples in the same order. The script checks their identifiers and reorders metadata explicitly.
- **Normalization and transformation solve different problems.** Counts per million adjusts for library totals; `log2(1 + CPM)` compresses the range. Neither step by itself supplies a model of biological variability.
- **PCA is a sample diagnostic.** Here it helps inspect variation associated with condition and read layout. Separation in a PCA plot is not a gene-level significance test.
- **Effect size and statistical significance are different outputs.** The largest adjusted contrast is **−4.2415** for **FBgn0039155** on the transformed scale. That ranks an observed difference; it does not establish a statistically significant gene or a causal effect.

## Challenges and decisions

The experiment has only **seven libraries**, and read layout varies alongside condition. I keep both annotations visible in the plot and include layout in the descriptive gene comparison:

```python
design = np.column_stack([np.ones(len(meta)), paired, treated])
assert np.linalg.matrix_rank(design) == 3
beta = np.linalg.lstsq(design, log_cpm.T, rcond=None)[0][2]
```

The three columns represent an intercept, paired-end layout and treatment status. The treatment coefficient therefore compares conditions while accounting for a separate layout offset in this model.

The code checks that both conditions contain both layouts and that the design has full column rank. Those checks make the coefficient estimable, but they do not remove the limitations of a small experiment or simple library-size normalization.

## What I would improve next

For differential-expression inference, I would use a count-based method with dispersion estimation, a design that includes layout and multiple-testing correction. I would also check sensitivity to filtering and normalization. An exon-level splicing question would require different inputs from the gene totals used here.

