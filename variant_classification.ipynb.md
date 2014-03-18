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


$$\frac{ Pr(G, Y ~|~ \text{causal}) }{ Pr(G, Y ~|~ \text{benign}) }$$


## Putting it together across all families

$$ \text{LR} = \prod_{families} \frac{ Pr(G, Y ~|~ \text{causal}) }{ Pr(G, Y ~|~ \text{benign}) }$$


## So what is that? How do we calculate it?

$$ Pr(G, Y ~|~ \text{causal}) = Pr(G) Pr(Y ~|~ G, \text{causal}) $$ 


$$~$$


$$ \text{LR} = \prod_{families} \frac{ Pr(Y ~|~ G, \text{causal}) }
                                     { Pr(Y ~|~ G, \text{benign}) }$$

$$~$$


$$ \text{LR} = \prod_{families} \frac{ Pr(\text{causal}, G ~|~ Y) ~/~ Pr(\text{causal}, G) }
                                     { Pr(\text{benign} ~|~ Y)    ~/~ Pr(\text{benign}) }$$


$$~$$


$$ \text{LR} = \prod_{families} \frac{ Pr(\text{del} ~|~ Y) }
                                     { Pr(\text{benign} ~|~ Y) }
/
                                \frac{ Pr(\text{del}) }
                                     { Pr(\text{benign}) }$$



