from django.db import models



class Demo_model(models.Model):              #creating model name Demo_model ,so we can trigger the signal.
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
