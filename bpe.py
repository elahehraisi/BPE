from collections import defaultdict


# following text is from https://www.reedbeta.com/blog/programmers-intro-to-unicode/

text = ("Ｕｎｉｃｏｄｅ! 🅤🅝🅘🅒🅞🅓🅔‽ 🇺‌🇳‌🇮‌🇨‌🇴‌🇩‌🇪! 😄 The very name strikes fear and awe "
        "into the hearts of programmers worldwide. We all know we ought to “support Unicode”"
        " in our software (whatever that means—like using wchar_t for all the strings, right?). "
        "But Unicode can be abstruse, and diving into the thousand-page Unicode Standard plus "
        "its dozens of supplementary annexes, reports, and notes can be more than a little "
        "intimidating. I don’t blame programmers for still finding the whole thing mysterious, "
        "even 30 years after Unicode’s inception.")


# In Python,the encode() method is used to convert a string into a bytes object,
# which is a sequence of bytes representing the string's characters in a specific encoding format.

# utf-8 encoding is backward compatible
byte_tokens = text.encode("utf-8") #raw bytes
print(byte_tokens)
# b'\xef\xbc\xb5\xef\xbd\x8e\xef\xbd\x89\xef\xbd\x83\xef\xbd\x8f\xef\xbd\x84\xef\xbd\x85! ...

#convert to a list of integers in range 0...255 for convenience
tokens = list(map(int,byte_tokens))
print(tokens)
# [239, 188, 181, 239, 189, 142, 239, 189, 137, 239, 189, 131, 239, 189, 143, 239, 189, ...

print('len(text): ', len(text)) # 533
print('len(tokens): ', len(tokens)) # 616


# find the co-occurred pairs with their frequencies
def get_pairs(ids):
    count = defaultdict(int)
    for pair in zip(ids, ids[1:]):
        count[pair] += 1
    return count

pairs = get_pairs(tokens)
sorted_pairs = sorted(pairs.items(), key=lambda x:x[1], reverse=True)
print(sorted_pairs)

# [((101, 32), 20), ((240, 159), 15), ((226, 128), 12), ((105, 110), 12), ((115, 32), 10),...

max_pair = sorted_pairs[0]
chr(101) # e
chr(32) # white space
# the max frequncy is for pair 'e ' in the above text

# replace the most frequent pair (101, 32), with new id e.g., 256 in the list of ids
def merge(ids, pair, new_id):
#     in the list of ids, replace all occurrences of pair with the new token idx
    new_ids = []
    i = 0
    while i< len(ids):
        # if we are not at the very last position AND the pair matched, replace it
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
            new_ids.append(new_id)
            i += 2
        else:
            new_ids.append(ids[i])
            i += 1
    return new_ids

new_token_list = merge(tokens, max_pair[0], 256)

print(len(new_token_list)) #596
# number of tokens reduced from 616 to 596


# ##############################################
# ############## implementing BPE ##############
# ##############################################

vocab_size = 276 # the desired final vocab size

# Step 1. Create a dictionary merged_pairs: {(token_id 1, token_id 2):new_id}

num_merges = vocab_size - 256
ids = list(tokens)

# merged_pairs is a dictionary, key is a tuple of most co-occurred token ids, value is new token id
merged_pairs = {} # (int, int) -> int
for i in range(num_merges):
    all_pairs = get_pairs(ids)
    max_pair = max(all_pairs, key=all_pairs.get)
    new_id = 256+i
    print(f"merging {max_pair} into a new token {new_id}")
    ids = merge(ids, max_pair, new_id)
    merged_pairs[max_pair] = new_id
print(merged_pairs)

print("old token list: ", len(tokens)) # 616
print("new token list: ", len(ids)) # 451
print("compression ratio: ", len(tokens)/len(ids)) # 1.365


# ############## Encoding using BPE ##############
# Step 2: encoding using BPE

def encode(text):
#     given a string, return list of integers (the tokens)

#     get a list of tokens
    tokens = list(text.encode("utf-8"))
    print(tokens)
    while len(tokens) >=2:

        # get the pair of token ids with frequency
        pairs = get_pairs(tokens)

        # find the pairs that have the lowest index in the dictionary (min number)
        # the reason of min number is that we started to create new token id from
        # 256 till 276. so, it is possible that token 256 with another token create
        # a new token later (e.g., 266), so we should first have token 256 to create token 266
        pair = min(pairs, key=lambda p: merged_pairs.get(p, float("inf")))

        # the above code is equivalent to the following
        # num = float("inf")
        # pair = None
        # for p in pairs:
        #     if merged_pairs[p] < num:
        #         num = merged_pairs[p]
        #         pair = p

        # no pair found to be merged
        if pair not in merged_pairs:
            break
        idx = merged_pairs[pair]

        # now that we have found the most frequent pair, replace the pair with the new token id
        tokens = merge(tokens, pair, idx)
    return tokens

print(encode("how are you doing ;)"))


# ############## Decoding BPE ##############
# Step 3. Decoding
# given tokenizer, and the tokenized text, return the raw text

vocab = {idx: bytes([idx]) for idx in range(256)}

for (t0,t1), t2 in merged_pairs.items():
    vocab[t2] = vocab[t0]+vocab[t1]
print(vocab)
# {0: b'\x00', 1: b'\x01', 2: b'\x02', 3: b'\x03', 4: b'\x04', 5: b'\x05', 6: b'\x06', 7: b'\x07',
# 8: b'\x08', 9: b'\t', 10: b'\n', 11: b'\x0b', 12: b'\x0c', 13: b'\r', 14: b'\x0e', 15: b'\x0f',
# ...
# 268: b'\xe2\x80\x8c\xf0\x9f\x87', 269: b'er', 270: b'or', 271: b't ', 272: b'ing',
# 273: b'st', 274: b'and', 275: b' th'}

def decode(ids):
#  given ids (list of integers), return string
#  put b before string to specify the string as a “byte string“
    tokens = b"".join([vocab[idx] for idx in ids])
    text = tokens.decode("utf-8", errors = 'replace')
    return text

text = "One Sample Text"
print(decode(encode(text)))
