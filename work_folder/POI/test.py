test_str = '3.4.2-A Coruña'
compare = int(test_str.split('-')[0].split('.')[1])
print(compare)
print('true') if compare >= 2 else print('false')
