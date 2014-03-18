# What are we trying to do?

The combination of sequence data and family disease data contains
information about whether mutations are disease-causing.

**Intuition**: If we have a large data set, and we observe a rare VUS
  mutation in 20 families, and all those families have a high disease
  incidence, then the VUS may be causal.

So we should:

1. Take all historical data into account when first releasing results.
2. Continually revise this classification as we accumulate more
   sequence data and family disease data.


# What does out data set look like?

A collection of families. Ideally *LOTS* of familes!


## We'll focus on one family, but remember we'd be analysing many families.

We might or might not know the family tree (pedigree).

Typically, we have genotype data for one individual, and some patchy phenotype data:

| Person  | Genotype at VUS | Disease Phenotype |
|---------|-----------------|-------------------|
| Patient | $$G_p$$         | $$Y_p$$           |
| Sister  | $$?$$           | $$Y_{rel,1}$$     |
| Aunt 1  | $$?$$           | $$Y_{rel,2}$$     |
| Aunt 2  | $$?$$           | $$?$$             |


In the future we might sequence relatives:

| Person  | Genotype at VUS | Disease Phenotype |
|---------|-----------------|-------------------|
| Patient | $$G_p$$         | $$Y_p$$           |
| Sister  | $$G_{rel,1}$$   | $$Y_{rel,1}$$     |
| Aunt 1  | $$G_{rel,2}$$   | $$Y_{rel,2}$$     |
| Aunt 2  | $$G_{rel,3}$$   | $$?$$             |


# How do we make this quantitative?

Our data "looks like" it might suggest a causal variant.

But could it have happened by chance? (p-value)

What's the probability it's causal? (Bayesian posterior probability)


## Write down the likelihood: probability of observed data

$$Pr(G_p, Y_p, G_{rel}, Y_{rel})$$


$$ Pr(A ~\text{and}~ B) = Pr(A) ~ Pr(B ~~|~~ A) $$

$$ Pr(G_p, Y_p, Y_{rel} ) Pr(G_{rel} ~|~ G_p, Y_p, Y_{rel}) $$


## Let's ignore sequenced relatives

## We can quantify the evidence for causality by calculating a *likelihood ratio*

\newcommand{\Pr}{\text{Pr}}



$$\frac{ \Pr(G, Y ~|~ \text{causal}) }{ \Pr(G, Y ~|~ \text{noncausal}) }$$


## Putting it together across all families

$$ \text{LR} = \prod_{families} \frac{ \Pr(G, Y ~|~ \text{causal}) }{ \Pr(G, Y ~|~ \text{noncausal}) }$$


## OK...so how does this connect with reality?

Just a tiny bit more rearranging...

$$ \Pr(G, Y ~|~ \text{causal}) = \Pr(G) \Pr(Y ~|~ G, \text{causal}) = \Pr(G) \Pr(Y ~|~ \text{del}) $$ 


$$~$$


$$ \text{LR} = \prod_{families} \frac{ \Pr(Y ~|~ \text{del}) }
                                     { \Pr(Y ~|~ \text{benign}) }$$

$$~$$


( Bayes Rule $ \Pr(X|Y) = \Pr(X)~\Pr(Y|X) ~/~ \Pr(Y) $ )

$$~$$


$$ \text{LR} = \prod_{families} \frac{     \Pr(\text{del} ~|~ Y) }
                                     { 1 - \Pr(\text{del} ~|~ Y) }
/
                                \frac{     \Pr(\text{del}) }
                                     { 1 - \Pr(\text{del}) }$$



## How do we use this?

#### $ \Pr(\text{del}) $ => fraction of people with any known deleterious mutation.

#### $ \Pr(\text{del} ~|~ Y) $ => probability of deleterious mutation given family history


## Logistic Regression


| Family | Patient has Known Del? | BRCA < 50 score | BRCA > 50 score | Ovarian < 50 score | ... |
|--------|------------------------|-----------------|-----------------|--------------------|-----|
|      1 | No                     |               0 |               0 |                  0 | ... |
|      2 | No                     |               0 |               1 |                  0 | ... |
|      3 | Yes                    |               2 |               0 |                  0 | ... |
|      4 | Yes                    |               0 |               1 |                  0 | ... |
|      5 | No                     |               0 |               0 |                  0 | ... |


## Classification Algorithm


1. Estimate $ \Pr(\text{del}) $

2. Fit logistic regression

3. Calculate LR for each VUS
```
for each VUS
    for each family with the VUS
        calculate LR using family history data
    calculate product over families
```

4. Compare LRs for VUSs to LRs for known benign and known deleterious mutations
   VUS LRs that look like they come from the deleterious distribution => reclassify as deleterious

5. Let our physicians and patients know about the reclassifications if they have asked to be kept informed.

6. Publish the reclassification.


