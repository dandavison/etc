  ---------- --------------------------------------------------------------
    $Y_i$    Phenotype of individual $i$ ($0=$ unaffected, $1=$ affected)
   $G_{il}$  Genotype at individual $i$ locus $l$
   $\phi_l$  Phenotypic effect of non-reference allele at locus $l$
  ---------- --------------------------------------------------------------

Introduction
============

 \
In variant classification, we use phenotype and genotype observations to
decide which mutations should be reported as pathogenic. The available
data is a matrix of $n$ individuals x $L$ genomic locations of SNP or
indel variants, together with a column of $n$ phenotype scores, and a
pedigree (multiple disconnected pedigrees) specifying relationships
between the $n$ individuals. Entire rows of the matrix will typically be
missing, corresponding to unsequenced individuals (relatives of a
sequenced individual), and phenotype labels may be missing for some
individuals (e.g. if they have not reached age-of-onset).

 \
Myriad treat the data as containing the following independent sources of
information about VUS effects:

1.  Occurrence of VUS *in trans* with known deleterious variant

2.  Variation in family disease incidence between individuals with and
    without the VUS

3.  Cosegregation of VUS with disease status in pedigrees

4.  Sequence/transcript-based effect prediction

5.  Phylogenetic conservation

Sources
=======

#### Easton et al. [Myriad] (2007) Am. J. Hum. Genet. 81:873

Useful. Describes mathematical details for (1), (2) and (3).

Questions
=========

-   Should we collect data on numbers of non-affected relatives in
    addition to affected?

 \
The main scenario is:

#### Scenario 1: A VUS associated with disease incidence in relatives:

We have performed exon sequencing of the relevant disease genes for an
individual and discovered a Variant of Uncertain Significance (VUS).
Initially we lack any further evidence regarding whether or not the
variant is causative. Subsequently, we discover the same VUS in other
individuals, some of which have affected relatives. How many other
individuals, with what sorts of patterns of family disease incidence,
are sufficient to conclude that the variant should be reported as likely
deleterious?

 \
We may also sequence some affected individuals. This is equivalent to a
sequenced individual having an affected relative with relatedness
coefficient equal to 1 (identical twin).

 \
Consider a VUS at locus $l$ which has been observed in several
individuals. A variant classification algorithm should have the
following properties:

1.  The strength of evidence for pathogenicity of $l$ increases with the
    number of families in which there are affected individuals related
    to an individual with the VUS

2.  The evidence for pathogenicity of $l$ is stronger if the affected
    individuals are more closely related to the sequenced individual
    with the VUS.

Model and variant classification algorithm
==========================================

Test for linkage between marker and trait locus
-----------------------------------------------

 \
Let $\theta$ be the recombination fraction between the VUS locus and the
trait locus. We compute a likelihood ratio comparing the hypothesis of
$\theta=0$ (VUS locus is causative) versus $\theta=0.5$ (VUS locus is
not linked to trait locus).

Test for per-locus effect indicators
------------------------------------

 \
Let $\phi_l$ represent the phenotypic effect of the non-reference
genotypes at locus $l$. We can initially consider an extremely simple
disease model: a locus $l$ has either $\phi_l=0$ (non-causative) or
$\phi_l=1$ (causative); any individual with 1 or more non-reference
alleles in any causative locus will certainly have the disease phenotype
from birth. (dominant, early onset, fully penetrant). Otherwise the
individual will certainly not display the disease phenotype. (The
sequenced genes explain all disease incidence.)

 \
The variant classification problem is inference for the effect
indicators $\phi_l$. The pedigree in each family is known. We introduce
latent “meiosis indicator” variables: $S_{ml}=0$ if meiosis $m$
transmitted the maternal allele at locus $l$; $S_{ml}=1$ if the paternal
allele was transmitted. $S_{m\bold{\cdot}}$ denotes the sequence of
meiosis indicator values for all loci at meiosis $m$.

 \
The likelihood is

$$\begin{aligned}
\Pr(Y, G|\phi)
=& \sum_S \Pr(S) \Pr(Y,G|S,\phi)\\
=& \sum_S \Pr(S) \Pr(G|S) \Pr(Y|G,\phi)\\
=& \sum_S \Big(\prod_mS_{m\bold{\cdot}}\Big) \Pr(G|S) \Pr(Y|G,\phi)\\\end{aligned}$$

 \
In words: we compute the likelihood by averaging over all possible
histories of recombination breakpoints in the pedigrees, weighted by
their prior probabilities (these can be computed easily from the
recombination map). Given a particular history $S$ of meiosis
indicators, the contribution to the likelihood is the product of the
prior probability $\Pr(S)$ of that meiotic history, the probability
$\Pr(G|S)$ of the observed genotypes given the meiotic indicators, and
the probability $\Pr(Y|G,\phi)$ of the phenotype data given the
genotypes.
