Variant reclassification
========================

In variant classification, we use phenotype and genotype observations
to classify mutations as benign, pathogenic, or uncertain.

Requirements for reclassification procedure
===========================================

Informally:

1. Stronger family disease history in close relatives of VUS positives
  is evidence of a causal VUS.
2. Co-segregation of disease status and VUS in pedigrees is evidence of
  a causal VUS.

Summary
=======

The following proposal is based on what Myriad does (Myriad 2013a,
2013b; Easton et al. 2007; Thompson et al. 2003).

- We compute a Variant Causality Score (VCS) for each VUS.
- The VCS quantifies the evidence that the VUS is causal.
- This score is a likelihood ratio (LR) comparing the likelihood of
  the observed phenotype and genotype data under a model of a causal VUS
  against that under a non-causal model.
- The analysis falls into two independent parts corresponding to
  requirements (1) and (2) above.


Details
=======

We consider data from a single family initially (the LR for data from
all families is simply a product of family LRs).


| Symbol     | Meaning                                                                |
|------------|------------------------------------------------------------------------|
| G_p        | VUS genotype of patient                                                |
| G_rel      | VUS genotypes of relatives                                             |
| Y_p        | Disease phenotype of patient                                           |
| Y_rel      | Disease phenotypes of relatives                                        |
| Asc        | Ascertainment conditions (e.g. only affected relatives were sequenced) |


The likelihood ratio, taking account of data ascertainment, is:

```
Pr(G_p, Y_p, G_rel, Y_rel | Asc, causal)
------------------------------------------
Pr(G_p, Y_p, G_rel, Y_rel | Asc, noncausal)
```

This is factorized into a family disease history component
(`LR_famhist`), and a pedigree segregation component
(`LR_seg`):

```
Pr(G_p, Y_p, Y_rel | Asc, causal)        Pr(G_rel | G_p, Y_p, Y_rel, Asc, causal)
------------------------------------- x -------------------------------------------  =
Pr(G_p, Y_p, Y_rel | Asc, noncausal)     Pr(G_rel | G_p, Y_p, Y_rel, Asc, noncausal)  
```

```
             LR_famhist               x                   LR_seg
```

`LR_famhist` summarizes the information on disease incidence among
relatives; `LR_seg` summarizes information on cosegregation of the VUS
with disease phenotype status -- it requires that we have sequenced
additional relatives.


Family history analysis
=======================



Segregation analysis
====================

The following is based on Peterson et al. (1998).

TODO: Would we need to make use of anything in Myriad's paper
(D. Thompson et al. 2003)?

The analysis depends on the study design (ascertainment of sequenced
relatives). We first consider a design in which affected relatives are
the only relatives to be sequenced (Peterson et al. 1998). The patient
genotype is `Aa` (het for a dominant VUS allele `A`). The pedigree is
known, and is implicit in the notation below. We consider the
numerator and denominator of the LR separately:

### Denominator: Segregation likelihood assuming VUS is non-causal

If the VUS is noncausal, phenotype does not predict genotype and the
likelihood is simply the probability of the vector of relative
genotypes conditional on the patient being positive for the VUS:

```
Pr(G_rel | G_p, Y_p, Y_rel, Asc, noncausal) = Pr(G_rel | G_p=Aa, Y_p, Y_rel=aff, noncausal)
                                            = Pr(G_rel | G_p=Aa)
```

If there is only a single relative, this can be worked out on
paper. E.g. for a single `Aa` sib, the probability is evaluated by
noting that there are two ways of sampling an `A` allele: as an
identical-by-descent (IBD) allele inherited from the sib; or as an
allele drawn at random from the population frequency `p`. (And the
same for `a` with population frequency `q=1-p`)

```
Pr(G_rel=Aa | G_p=Aa) = 2  x  (1/2 x 1/2 + 1/2 x p)  x  (1/2 x 1/2 + 1/2 * (1-p))
                      = (3/4 + pq)/2
```

<!-- = 2  x  (1/4 + p/2)  x  (3/4 - p/2) -->
<!-- = 2  x [  3/16 + 3p/8 - p/8 - pp/4 ] -->
<!-- = 3/8 + p/2 - pp/2 -->
<!-- = 1/2 (3/4 + p(1-p)) -->

(TODO: Hm, it should be `(1+pq)/2` according to Peterson et al. 1998)


If multiple relatives are sequenced then it is a bit more
complicated. Their genotypes can not be treated as independent due to
the shared pedigree; instead we calculate the likelihood by averaging
over the prior probability distribution of a latent variable `S` which
describes unknown aspects of the pedigree.

```
Pr(G_rel | G_p) = sum_S Pr(S|G_p) Pr(G_rel | S)
```

`S` could be unknown ancestral genotypes, or equivalently one can
consider the alleles in the founder genotypes to be drawn at random
from the population allele frequencies, and then average over the
'meiosis indicator' variables specifying which parent transmitted each
allele at meiosis (see e.g. E. A. Thompson 2007)


### Numerator: Segregation likelihood assuming VUS is causal

```
  Pr(G_rel | G_p, Y_p, Y_rel, Asc, causal)

= Pr(G_rel | G_p, Y_rel=aff, causal)  # given G_p, Y_p is uninformative

=             Pr(G_rel | G_p) Pr(Y_rel=aff|G_rel, causal)
  ----------------------------------------------------
  sum_{G_rel} Pr(G_rel | G_p) Pr(Y_rel=aff|G_rel, causal)
```

where the sum is over all possible relative genotypes.

<!-- = Pr(G_rel, Y_rel=aff | G_p, causal) / Pr(Y_rel=aff | G_p, causal) -->

```
P_aa = Pr(affected|aa genotype)   # similar to population prevalence
P_Aa = Pr(affected|Aa genotype)   # based on penetrance for known deleterious alleles
```

`Pr(G_rel | G_p)` is as in the denominator section above. Given the
penetrances, the phenotype probabilities are:

```
Pr(Y_rel=aff|G_rel, causal) = P_aa ^ #{aa relatives}  x  P_Aa ^ #{Aa relatives}
```




<!-- Myriad -->
XXXXXX
======

Myriad [1,2,3] treat the following as independent sources of
information for VUS classification (roughly in order of importance)

1. "History weighting algorithm": If a VUS is deleterious then family
   history of individuals with that VUS will resemble family history
   of individuals with known deleterious variants.

2. "in trans": Occurence of VUS *in trans* with known deleterious
   variant suggests VUS is benign.

3. "Segregation": Cosegregation of VUS with disease status in pedigrees

4. Sequence/transcript-based effect prediction and phylogenetic
   conservation

References
==========

1. Myriad (2013a) **A clinical history weighting algorithm accurately
   classifies BRCA1 and BRCA2 variants.** ESHG Product Literature
2. Myriad (2013b) **Segregation analysis offers a mechanism for
   variant reclassification...** ESHG Product Literature
3. Easton et al. \[Myriad\] (2007) **A systematic genetic assessment
   of 1,433 sequence variants of unknown significance in the BRCA1
   and BRCA2 breast cancer-predisposition genes.** Am. J. Hum. Genet. 81:873
   *[Useful. Describes mathematical details for History-weighting, Co-occurrence and Segregation analyses.]*
4. Goldgar et al. \[Myriad\] (2008) **Genetic evidence and
   intergration of various data sources for classifying uncertain
   variants into a single model.** Hum. Mutat. 29:1265
   *[Mostly a rehash of Easton et al. (2007); discusses two-component mixture model approach]*
5. D. Thompson et al. (2003) **A full-likelihood method for the
   evaluation of causality of sequence variants from family data.**
   Am. J. Hum. Genet. 73:652
   *[Myriad's main reference for their pedigree segregation analysis.
   Presented as an advance over Peterson, Parmigiani et al. (1998).
   Minimal mathematical detail.]*
6. Peterson, Parmigiani and Thomas (1998) **Missense mutations in
   disease genes: a Bayesian approach to evaluate causality.**
   Am. J. Hum. Genet. 62:1516 *[Very useful; clear mathematical presentation.]*
7. E. A. Thompson (2007) **Linkage Analysis** ch.33 Handbook of
   Statistical Genetics 3rd Ed.

Questions
=========

-   Should we collect data on numbers of non-affected relatives in
    addition to affected?

TODO
====

- Power analysis
- Validation on existing data?


sensitivity: Compute causality score for each known deleterious variant.
specificity: Compute causality score for probands with neither VUS nor known del.

evidence:

- Their variant's causality score compared to those of known deleterious variants



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

We may also sequence some affected individuals. This is equivalent to a
sequenced individual having an affected relative with relatedness
coefficient equal to 1 (identical twin).

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

The available data is a matrix of $n$ individuals x $L$ genomic
locations of SNP or indel variants, together with a column of $n$
phenotype scores, and a pedigree (multiple disconnected pedigrees)
specifying relationships between the $n$ individuals. Entire rows of
the matrix will typically be missing, corresponding to unsequenced
individuals (relatives of a sequenced individual), and phenotype
labels may be missing for some individuals (e.g. if they have not
reached age-of-onset).


Test for linkage between marker and trait locus
-----------------------------------------------

Let $\theta$ be the recombination fraction between the VUS locus and the
trait locus. We compute a likelihood ratio comparing the hypothesis of
$\theta=0$ (VUS locus is causative) versus $\theta=0.5$ (VUS locus is
not linked to trait locus).

Test for per-locus effect indicators
------------------------------------

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
