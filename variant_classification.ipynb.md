# What are we trying to do?

The combination of sequence data and family disease data contains
information about whether mutations are disease-causing.

If we have a large data set, and we observe a rare VUS mutation in 20
families, and all those families have a high disease incidence, then
we need to seriously consider the possibility that the VUS is causal.

So we should:

1. Take all historical data into account when first releasing results.
2. Continually revise tjhis classification as we accumulate more
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

