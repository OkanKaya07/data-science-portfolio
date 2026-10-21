# Run from the repository root: Rscript projects/06-r-bioinformatics/analyze.R
# Base R only. Extract data from multtest without installing or executing package code.
args <- commandArgs(trailingOnly=TRUE)
archive <- if (length(args)) args[1] else 'data/raw/multtest.tar.gz'
out <- 'projects/06-r-bioinformatics/reports'
dir.create(out, recursive=TRUE, showWarnings=FALSE)
if (!file.exists(archive)) {
  dir.create(dirname(archive), recursive=TRUE, showWarnings=FALSE)
  download.file('https://bioconductor.uib.no/packages/3.23/bioc/src/contrib/multtest_2.68.0.tar.gz', archive, mode='wb')
}
members <- untar(archive, list=TRUE)
data_file <- grep('/data/golub\\.(rda|RData|rdata)$', members, value=TRUE)
stopifnot(length(data_file)==1)
scratch <- tempfile('golub-'); dir.create(scratch)
untar(archive, files=data_file, exdir=scratch)
env <- new.env(); load(file.path(scratch,data_file), envir=env)
x <- env$golub; labels <- env$golub.cl; annotations <- env$golub.gnames
stopifnot(identical(dim(x), c(3051L,38L)), length(labels)==38L, sum(labels==0)==27L, sum(labels==1)==11L, all(is.finite(x)))
group <- factor(labels, levels=c(0,1), labels=c('ALL','AML'))
# Already processed expression values. Differences are on the supplied scale, NOT log2 fold changes.
tests <- lapply(seq_len(nrow(x)), function(i) t.test(x[i,group=='AML'], x[i,group=='ALL'], var.equal=FALSE))
effect <- rowMeans(x[,group=='AML'])-rowMeans(x[,group=='ALL'])
p <- vapply(tests,function(test) test$p.value,numeric(1))
results <- data.frame(gene_index=annotations[,1],gene_description=annotations[,2],probe_id=annotations[,3],
 mean_difference_AML_minus_ALL=effect,p_value=p,fdr_BH=p.adjust(p,method='BH'),
 ci_low=vapply(tests,function(test) test$conf.int[1],numeric(1)),
 ci_high=vapply(tests,function(test) test$conf.int[2],numeric(1)))
results <- results[order(results$fdr_BH,results$p_value),]
stopifnot(all(results$fdr_BH>=results$p_value-1e-15),all(results$fdr_BH<=1))
write.csv(results,file.path(out,'gene_statistics.csv'),row.names=FALSE)
# PCA uses variance-ranked genes without looking at class labels.
selected <- order(apply(x,1,var),decreasing=TRUE)[seq_len(500)]
pca <- prcomp(t(x[selected,]),center=TRUE,scale.=TRUE)
variance <- pca$sdev^2/sum(pca$sdev^2)
colors <- ifelse(group=='ALL','#2878A5','#CB654A')
png(file.path(out,'pca.png'),width=1100,height=750,res=130)
plot(pca$x[,1:2],col=colors,pch=19,cex=1.3,
 xlab=sprintf('PC1 (%.1f%%)',100*variance[1]),ylab=sprintf('PC2 (%.1f%%)',100*variance[2]),
 main='Golub leukemia expression: unsupervised PCA')
legend('topright',legend=levels(group),col=c('#2878A5','#CB654A'),pch=19,bty='n')
dev.off()
png(file.path(out,'differential_expression.png'),width=1100,height=750,res=130)
plot(results$mean_difference_AML_minus_ALL,-log10(pmax(results$fdr_BH,.Machine$double.xmin)),
 pch=19,cex=.6,col=ifelse(results$fdr_BH<.05,'#CB654A','#A2ADB6'),
 xlab='Mean difference (AML - ALL), supplied expression scale',ylab='-log10(BH-adjusted p)',
 main='Welch tests across 3,051 expression features')
abline(h=-log10(.05),lty=2,col='#2878A5');dev.off()
write.csv(data.frame(sample=paste0('sample_',seq_len(ncol(x))),group=group,PC1=pca$x[,1],PC2=pca$x[,2]),file.path(out,'pca_scores.csv'),row.names=FALSE)
summary <- data.frame(genes=nrow(x),samples=ncol(x),ALL=sum(group=='ALL'),AML=sum(group=='AML'),
 bh_below_005=sum(results$fdr_BH<.05),pc1_variance=variance[1],pc2_variance=variance[2])
write.csv(summary,file.path(out,'summary.csv'),row.names=FALSE)
capture.output(sessionInfo(),file=file.path(out,'sessionInfo.txt'))
cat('Validation passed: dimensions, class counts, finite values, BH bounds.\n')
print(summary)
unlink(scratch,recursive=TRUE)
