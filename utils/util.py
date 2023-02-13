import pathlib

cws = pathlib.Path(__file__).parent.parent.absolute().joinpath('configs')

print(cws)