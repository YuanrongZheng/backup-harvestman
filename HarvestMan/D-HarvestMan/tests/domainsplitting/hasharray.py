import timeit
import random

array = {}
array_size = 3000000
array_item = "http://www.yahoo.com/some/path:"
def test(current_array_size):
    intkey = random.randint(0, current_array_size-1)
    key = array_item+str(intkey)
    if array.has_key(key):
        value = array[key]
    else:
        print "item not found in hash array: " + str(key)

if __name__=='__main__':
    print "starting test..."
    step = int(array_size/100)
    resultlist = []
    
    for i in range(1, array_size):
        if i%step == 0:
            t = timeit.Timer("test("+str(i)+")", "from __main__ import test")
            res = t.repeat(1, 1)
            resultlist += res
        array[array_item+str(i)] = array_item + str(i)
    
    print "length of hash array: " + str(len(array))
    for j in resultlist:
        print j

    