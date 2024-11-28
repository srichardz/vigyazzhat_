table = [[40, 96],
         [19],
         [32],
         [23]]

def validator(card):
    row_dist = [card-c[-1] for c in table]
    if all([True if ele < 0 else False for ele in row_dist]):
        return ("Húzás!")
    print(row_dist)
    set_zero = lambda x: 0 if x < 0 else x
    print([set_zero(ele) for ele in row_dist])
    row_idx = [set_zero(ele) for ele in row_dist].index(min([set_zero(ele) for ele in row_dist]))
    return row_idx

for i in [82]:
    print(validator(i))


# card kisebb mint bármelyik sor
# card szabályosan lerakható



# egyeb sufni juniteszt
bh_in_cin = [
    sum([
        (2 if str(card)[-1] == '5' else 0) + (3 if str(card)[-1] == '0' else 0) + (5 if len(str(card)) != 1 and str(card)[0] == str(card)[1] else 0) for card in row
    ]) 

    for row in table
]

print(bh_in_cin)