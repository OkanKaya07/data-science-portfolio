# Base R plotting helpers. Source this file from the repository root.
report_dir <- "projects/06-r-bioinformatics/reports"

plot_volcano <- function(results) {
  effect <- results$mean_difference_AML_minus_ALL
  fdr <- results$fdr_BH
  stopifnot(nrow(results) > 0L, length(effect) == nrow(results),
            length(fdr) == nrow(results), all(is.finite(effect)),
            all(is.finite(fdr)), all(fdr >= 0 & fdr <= 1))

  # These processed values support mean differences, not log2 fold changes.
  score <- -log10(pmax(fdr, .Machine$double.xmin))
  significant <- fdr < 0.05
  higher_all <- significant & effect < 0
  higher_aml <- significant & effect > 0
  point_colors <- rep("#B4BEC8", length(effect))
  point_colors[higher_all] <- "#2878A5"
  point_colors[higher_aml] <- "#CB654A"

  old_par <- par(mar=c(6, 5, 4.5, 1.5), las=1)
  on.exit(par(old_par))
  span <- max(abs(effect), 0.1) * 1.08
  plot(effect, score, type="n", xlim=c(-span, span),
       ylim=c(0, max(score, 2) * 1.22),
       xlab="Mean expression difference (AML - ALL)",
       ylab="-log10(BH-adjusted p value)",
       main="Golub leukemia expression | Volcano-style plot")
  grid(col="#E8EDF1", lty=1)
  abline(v=0, col="#8795A1", lty=3)
  abline(h=-log10(0.05), col="#526779", lty=2)
  # Draw non-significant points first so significant features remain visible.
  order_points <- order(significant)
  points(effect[order_points], score[order_points], pch=16, cex=0.75,
         col=adjustcolor(point_colors[order_points], alpha.f=0.8))
  legend("topleft", bty="n", pch=16, cex=0.87,
         col=c("#2878A5", "#CB654A", "#B4BEC8"),
         legend=c(sprintf("Higher in ALL, FDR < 0.05 (n = %d)", sum(higher_all)),
                  sprintf("Higher in AML, FDR < 0.05 (n = %d)", sum(higher_aml)),
                  sprintf("FDR >= 0.05 (n = %d)", sum(!significant))))
  mtext(sprintf("%s features | %s below FDR 0.05 | 27 ALL and 11 AML samples",
                format(nrow(results), big.mark=","),
                format(sum(significant), big.mark=",")), side=3, line=0.4, cex=0.82)
  mtext("Supplied expression scale; exploratory group comparison.",
        side=1, line=4.5, cex=0.82, col="#526779")
  invisible(c(higher_ALL=sum(higher_all), higher_AML=sum(higher_aml),
              not_below_FDR=sum(!significant)))
}

show_volcano <- function(directory=report_dir) {
  results <- read.csv(file.path(directory, "gene_statistics.csv"),
                      check.names=FALSE)
  plot_volcano(results)
}

show_pca <- function(directory=report_dir) {
  scores <- read.csv(file.path(directory, "pca_scores.csv"))
  summary <- read.csv(file.path(directory, "summary.csv"))
  stopifnot(nrow(scores) == summary$samples, all(is.finite(scores$PC1)),
            all(is.finite(scores$PC2)), all(scores$group %in% c("ALL", "AML")))
  old_par <- par(mar=c(5, 5, 4, 2), las=1)
  on.exit(par(old_par))
  plot(scores$PC1, scores$PC2, pch=19, cex=1.25,
       col=ifelse(scores$group == "ALL", "#2878A5", "#CB654A"),
       xlab=sprintf("PC1 (%.1f%%)", 100 * summary$pc1_variance),
       ylab=sprintf("PC2 (%.1f%%)", 100 * summary$pc2_variance),
       main="Golub leukemia expression | Unsupervised PCA")
  legend("topright", legend=c("ALL (n = 27)", "AML (n = 11)"),
         col=c("#2878A5", "#CB654A"), pch=19, bty="n")
  invisible(scores)
}
