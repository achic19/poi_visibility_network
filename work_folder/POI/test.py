test_str = '3.10.3-A Coruña'
compare = test_str.split('-')[0]
print(compare)
print('true') if compare >= '3.10.3' else print('false')
