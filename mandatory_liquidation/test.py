path = 'C:/pythonProj/data/mandatory_liquidation'
#
# for root, dirs, files in os.walk(path):
#     for filename in files:
#         data = pd.read_csv(os.path.join(path, filename))
#         print(filename.split('_', 1)[0], data['datetime'].iloc[0])

dict = {'a': 1, 'b': 2, 'c': 1, 'd': 2}
print(dict.get('a','b'))