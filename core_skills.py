import random
# rand_list =

rand_list = []
for i in range(10):
    rand_list.append(random.randint(1, 20))

print(rand_list)

# list_comprehension_below_10 =

# I am assuming this is our input list
input_list = [1 ,2, 5, 10, 15, 20]

list_comprehension_below_10 = [
    item
    for item in input_list
    if item < 10
]

print(list_comprehension_below_10)

# list_comprehension_below_10 =

list_comprehension_below_10 = list(filter(lambda x : x < 10, input_list))

print(list_comprehension_below_10)
