import itertools as it

def boolean(s):
	return set(frozenset(x) for x in it.chain.from_iterable(it.combinations(s, r=i) for i in range(len(s) + 1)))

def cartesian_product(*sets):
	return set(it.product(*sets))