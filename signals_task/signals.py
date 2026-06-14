import time
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Demo_model
from django.db import connection


# Q1:
# Are django signals executed synchronously or asynchronously?


@receiver(post_save, sender=Demo_model)
def first_question(sender, instance, **kwargs):
    print("Signal started")
    time.sleep(7)  # Hence it proves that django signals works synchronously . 
    print("Signal finished")



# Q2:
# Do django signals run in the same thread as the caller?


@receiver(post_save, sender=Demo_model)
def second_question(sender, instance, **kwargs):
    print(threading.current_thread().name)      # here signal and caller print same thread name then it show it runs in same thread 




    
# Q3:
# Do django signals run in the same database transaction as the caller?
@receiver(post_save, sender=Demo_model)
def third_question(sender, instance, **kwargs):
    if connection.in_atomic_block:
        print("Inside transaction") #  If this prints "Inside transaction" while the caller is inside a transaction, it indicates that the signal is running in the same database transaction as the caller.
    else:
        print("Not inside transaction")