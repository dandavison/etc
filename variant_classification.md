Variant reclassification
========================

In variant classification, we use phenotype and genotype observations to classify mutations as benign, pathogenic, or uncertain.

The following notes are based on what Myriad has described (Myriad 2013a, 2013b; Easton et al. 2007; Thompson et al. 2003), and on Peterson et al. (1998), which uses sequencing of affected relatives to classify VUSs.

### Requirements for family history-based reclassification procedure

Informally:

1. Stronger family disease history in close relatives of VUS positives is evidence of a causal VUS.
2. Co-segregation of disease status and VUS in pedigrees is evidence of a causal VUS.

### Summary of procedure

- We compute a Variant Causality Score (VCS) for each VUS (recalculated periodically)
- The VCS quantifies the evidence that the VUS is causal.
- This score is a likelihood ratio (LR) comparing the likelihood of the observed phenotype and genotype data under a model of a causal VUS against that under a non-causal model.
- One way to use the VCS for a VUS would be to compare it to the distribution of VCSs for known deleterious/benign variants.

### Sources of information used by Myriad

Myriad treat the following as independent sources of information for VUS classification (roughly in order of importance). These notes cover only (1) and (3). Easton et al. (2007) additionally describes likelihood-ratio approaches for (2) and (4).

1. "History weighting algorithm": If a VUS is deleterious then family history of individuals with that VUS will resemble family history of individuals with known deleterious variants.

2. "in trans" / "co-occurence": Occurence of VUS *in trans* with known deleterious variant in the same gene, or with a known deleterious variant in a different gene, suggests VUS is benign.

3. "Segregation": Cosegregation of VUS with disease status in pedigrees

4. Sequence/transcript-based effect prediction and phylogenetic conservation

### Details of family history and pedigree segregation analysis

We consider data from a single family initially (the LR for data from all families is simply a product of family LRs). 

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

This is factorized into a family disease history component (`LR_famhist`), and a pedigree segregation component (`LR_seg`):

```
Pr(G_p, Y_p, Y_rel | Asc, causal)        Pr(G_rel | G_p, Y_p, Y_rel, Asc, causal)
------------------------------------- x -------------------------------------------  =
Pr(G_p, Y_p, Y_rel | Asc, noncausal)     Pr(G_rel | G_p, Y_p, Y_rel, Asc, noncausal)
```

```
             LR_famhist               x                   LR_seg
```

`LR_famhist` summarizes the information on disease incidence among relatives; `LR_seg` summarizes information on cosegregation of the VUS with disease phenotype status -- it requires that we have sequenced additional relatives. The rest of this document describes how to compute these LRs.


### Family history likelihood ratio `LR_famhist`

This section corresponds to Myriad's "History Weighting Algorithm" (Myriad 2013a, Easton et al. 2007).

##### Numerator

```
  Pr(G_p, Y_p, Y_rel | Asc, causal)
= Pr(G_p, Y_p, Y_rel | causal)          # There is no ascertainment bias
= Pr(G_p) Pr(Y_p, Y_rel | G_p, causal)  # Patient genotype unaffected by causal/noncausal
```

##### Denominator

```
  Pr(G_p, Y_p, Y_rel | Asc, noncausal)
= Pr(G_p, Y_p, Y_rel | noncausal)                 # There is no ascertainment bias
= Pr(G_p | noncausal) Pr(Y_p, Y_rel | noncausal)  # VUS genotypes do not predict phenotype
= Pr(G_p) Pr(Y_p, Y_rel | noncausal)   # Patient genotype unaffected by causal/noncausal
```

##### Likelihood Ratio

The likelihood ratio is

```
              Pr(Y_p, Y_rel | G_p, causal)
LR_famhist =  ----------------------------
              Pr(Y_p, Y_rel | noncausal)
```

Using Bayes rule this is

```
              Pr(Y_p, Y_rel, causal, G_p) / Pr(causal, G_p)
LR_famhist =  ---------------------------------------------
              Pr(Y_p, Y_rel, noncausal)   / Pr(noncausal)

              Pr(causal, G_p | Y_p, Y_rel) / Pr(causal, G_p)
           =  ----------------------------------------------
              Pr(noncausal | Y_p, Y_rel)   / Pr(noncausal)
```

TODO: Is what Myriad do in the rest of this section reasonable?

For the family of a positive patient (`G_p=Aa`), Myriad estimate this as

```
              Pr(del | Y_p, Y_rel)       / Pr(del)
LR_famhist =  -----------------------------------------
              [1 - Pr(del | Y_p, Y_rel)] / [1 - Pr(del)]
```

where `del` is the event "the patient has a deleterious mutation".

For the family of a negative patient, the numerator and the denominator are the same, so these families are uninformative.

Myriad estimate `Pr(del|Y_p, Y_rel)` by fitting a logistic regression model to a data set comprising multiple tested individuals and various summaries of the disease history of themselves and their family (Easton et al. 2007). The individuals are either positive for a known deleterious mutation, or lack any VUS. Fitting the model provides the required function predicting the probability that the patient has a deleterious mutation, given their family disease history. They estimate `Pr(del)` as the overall proportion of individuals with a known deleterious mutation.


### Segregation likelihood ratio `LR_seg`

The following is based on Peterson et al. (1998). See below for partial description of Myriad's pedigree segregation method (D. Thompson et al. 2003).

The analysis depends on the study design (ascertainment of sequenced relatives). We first consider a design in which affected relatives are the only relatives to be sequenced (`Y_rel=aff`; Peterson et al. 1998). The pedigree is known, and is implicit in the notation below. We consider the numerator and denominator of the LR separately:

##### Denominator: Segregation likelihood assuming VUS is non-causal

If the VUS is noncausal, phenotype does not predict genotype and the likelihood is simply the probability of the vector of relative genotypes conditional on the patient being positive for the VUS:

```
Pr(G_rel | G_p, Y_p, Y_rel, Asc, noncausal) = Pr(G_rel | G_p, Y_p, Y_rel=aff, noncausal)
                                            = Pr(G_rel | G_p)
```

If there is only a single relative, this can be worked out on paper. But if multiple relatives are sequenced their genotypes can not be treated as independent, due to the shared pedigree; instead we calculate the likelihood by averaging over the prior probability distribution of a latent variable `S` which describes unknown aspects of the pedigree.

```
Pr(G_rel | G_p) = sum_S Pr(S|G_p) Pr(G_rel | S)
```

`S` could be unknown ancestral genotypes, or equivalently one can consider the alleles in the founder genotypes to be drawn at random from the population allele frequencies, and then average over 'meiosis indicator' variables specifying which parent transmitted each allele at meiosis (see e.g. E. A. Thompson 2007)


##### Numerator: Segregation likelihood assuming VUS is causal

```
  Pr(G_rel | G_p, Y_p, Y_rel, Asc, causal)

= Pr(G_rel | G_p, Y_rel=aff, causal)  # given G_p, Y_p is uninformative about G_rel

=             Pr(G_rel | G_p) Pr(Y_rel=aff|G_rel, causal)
  -------------------------------------------------------
  sum_{G_rel} Pr(G_rel | G_p) Pr(Y_rel=aff|G_rel, causal)
```

where the sum is over all possible relative genotype vectors.

```
P_aa = Pr(affected|aa genotype)   # similar to population prevalence
P_Aa = Pr(affected|Aa genotype)   # based on penetrance for known deleterious alleles
```

`Pr(G_rel | G_p)` is as in the denominator section above. Given the
penetrances, the phenotype probabilities are:

```
Pr(Y_rel=aff|G_rel, causal) = P_aa ^ #{aa relatives}  x  P_Aa ^ #{Aa relatives}
```


### Myriad's segregation likelihood ratio method (Thompson et al. 2003)

Thompson et al. (2003) claim that their method has several advantages over Peterson et al. (1998). They take a traditional linkage analysis formulation, considering the recombination fraction between the VUS locus and the disease locus. The define the LR as a comparison of a full-linkage model versus a no-linkage model:

```
         Pr(G_rel | G_p, Y, linked)
LR_seg = ----------------------------
         Pr(G_rel | G_p, Y, unlinked)

         Pr(Y, G_rel, G_p | linked)     Pr(Y, G_p | unlinked)
	   = ---------------------------- x ---------------------
		 Pr(Y, G_rel, G_p | unlinked)   Pr(Y, G_p | linked)
```

These likelihoods could be calculated using the latent variable approaches outlined above (e.g. E. A. Thompson 2007). Myriad (D. Thompson et al. 2003) say that they calculate these likelihoods using software called LINKAGE. They don't describe how they deal with ascertainment of sequenced relatives.


### References

1. Myriad (2013a)
   [**A clinical history weighting algorithm accurately classifies BRCA1 and BRCA2 variants.**]
   (https://docs.google.com/a/counsyl.com/document/d/1NE_1j3H5N5sqvXVHUnshbNBT7itFeKTGoxV2FD92s3w/edit#heading=h.jw4sind13pop)
   ESHG Product Literature
2. Myriad (2013b)
   [**Segregation analysis offers a mechanism for variant reclassification...**]
   (https://docs.google.com/a/counsyl.com/document/d/1NE_1j3H5N5sqvXVHUnshbNBT7itFeKTGoxV2FD92s3w/edit#heading=h.u92owrh3qhv6)
   ESHG Product Literature
3. Easton et al. \[Myriad\] (2007)
   [**A systematic genetic assessment of 1,433 sequence variants of unknown significance in the BRCA1 and BRCA2 breast cancer-predisposition genes.**]
   (http://download.cell.com/AJHG/pdf/PIIS0002929707638658.pdf)
   Am. J. Hum. Genet. 81:873
   *[Useful. Describes mathematical details for History-weighting, Co-occurrence and Segregation analyses.]*
4. Goldgar et al. \[Myriad\] (2008)
   [**Genetic evidence and intergration of various data sources for classifying uncertain variants into a single model.**]
   (http://onlinelibrary.wiley.com/doi/10.1002/humu.20897/pdf)
   Hum. Mutat. 29:1265
   *[Mostly a rehash of Easton et al. (2007); discusses two-component mixture model approach]*
5. D. Thompson et al. (2003)
   **[A full-likelihood method for the evaluation of causality of sequence variants from family data.]
   (http://download.cell.com/AJHG/pdf/PIIS000292970762028X.pdf)**
   Am. J. Hum. Genet. 73:652
   *[Myriad's main reference for their pedigree segregation analysis.  Presented as an advance over Peterson, Parmigiani et al. (1998).  Minimal mathematical detail.]*
6. Peterson, Parmigiani and Thomas (1998)
   **[Missense mutations in disease genes: a Bayesian approach to evaluate causality.]
   (http://download.cell.com/AJHG/pdf/PIIS0002929707627955.pdf)**
   Am. J. Hum. Genet. 62:1516
   *[Very useful; clear mathematical presentation.]*
7. E. A. Thompson (2007) **Linkage Analysis** ch.33 [Handbook of Statistical Genetics 3rd Ed.](http://medacadem.chita.ru/docs/medstat/14.pdf)
