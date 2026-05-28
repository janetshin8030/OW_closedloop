import murmurhash
name = "Janet Shin" #type name to be encrypted
test = "stroop"
hash_value = murmurhash.hash(name)
hash_and_test = f"{test}_{hash_value}"
print(f"MurmurHash32: {hash_and_test}")