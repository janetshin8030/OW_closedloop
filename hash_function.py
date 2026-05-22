import murmurhash
name = "Janet Shin" #type name to be encrypted
hash_value = murmurhash.hash(name)
print(f"MurmurHash32: {hash_value}")