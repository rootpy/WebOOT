pep8:
	pep8 -r weboot scripts/* setup.py --max-line-length=100 --count

autopep8:
	autopep8 -r weboot scripts/* setup.py -i --max-line-length=100
