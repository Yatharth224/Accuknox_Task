from django.db import models

class Rectangle:
    def __init__(self, length: int, width: int):  # Here we are setting the length and width of the rectangle 
        self.length = length
        self.width = width

    def __iter__(self):  #  Here it returns the length and width of the rectangle when we iterate over it
        yield {'length': self.length}
        yield {'width': self.width}