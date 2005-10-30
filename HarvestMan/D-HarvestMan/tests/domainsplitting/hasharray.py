import timeit
import random

array = {}
array_size = 10000000
array_item = "http://localhost:"

def test():
    key = random.randint(0, array_size-1)
    if str(key) in array.keys():
        value = array[str(key)]
    else:
        print "item not found in hash array"

if __name__=='__main__':
    print "setting up hash array with " + str(array_size) + " elements..."
    for i in range(0, array_size):
        array[str(i)] = array_item + str(i)
    
    print "starting performance test"
    t = timeit.Timer("test()", "from __main__ import test")
    res = t.repeat(10, 1)
    for i in res:
        print i