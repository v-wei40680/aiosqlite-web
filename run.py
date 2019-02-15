import sys
import os


argv = sys.argv

if len(argv) == 2:
    os.system('python3 ' + argv[1])
elif len(argv) == 1:
    print('hello world!')
else:
    print('too long!')
