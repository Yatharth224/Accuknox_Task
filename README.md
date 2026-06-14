# Accuknox Django Assignment

This project was given to me as a company assignment. It has two parts:

1. Practical proof for three questions related to Django Signals
2. A custom Rectangle class that can be iterated over

Below I have explained everything step by step - what I did, why I did it, and what output should come.

---

## Project Structure

```
Accuknox/
    manage.py
    requirements.txt
    README.md
    Accuknox_task/
        settings.py
        urls.py
        wsgi.py
    signals_task/
        models.py
        signals.py
        apps.py
        __init__.py
    rectangle_task/
        models.py
        apps.py
        __init__.py
```

---

## Setup Steps

```bash
python -m venv venv
source venv/bin/activate      # on windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
```

---

## Part 1 - Django Signals

I created a simple model for testing purposes, called `Demo_model`. It has no special purpose, it's only used to trigger the signal.

### models.py (signals_task)

```python
from django.db import models


class Demo_model(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
```

### signals.py (signals_task)

```python
import time
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from .models import Demo_model


# Q1 - Are django signals executed synchronously or asynchronously?
@receiver(post_save, sender=Demo_model)
def first_question(sender, instance, **kwargs):
    print("Signal started")
    time.sleep(7)
    print("Signal finished")


# Q2 - Do django signals run in the same thread as the caller?
@receiver(post_save, sender=Demo_model)
def second_function(sender, instance, **kwargs):
    print(threading.current_thread().name)


# Q3 - Do django signals run in the same database transaction as the caller?
@receiver(post_save, sender=Demo_model)
def thirdfunction(sender, instance, **kwargs):
    if connection.in_atomic_block:
        print("Inside transaction")
    else:
        print("Not inside transaction")
```

### apps.py (signals_task)

```python
from django.apps import AppConfig


class SignalsTaskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'signals_task'

    def ready(self):
        import signals_task.signals
```

### __init__.py (signals_task)

```python
default_app_config = 'signals_task.apps.SignalsTaskConfig'
```

---

## Question wise explanation

### Question 1: Are django signals executed synchronously or asynchronously?

**My answer:** Synchronously.

**Why?**

I added `time.sleep(7)` inside the `first_question` function. This means the signal will take 7 seconds to finish when it runs.

When I call `Demo_model.objects.create(name="something")`, if the signal was asynchronous, the `create()` call would return immediately and "Signal finished" would print later, in the background.

But when I ran this, the `create()` line was **blocked for 7 seconds** and only after that did the return value (`<Demo_model: ...>`) get printed. This shows that Django waits for the signal to fully complete before moving on - which means it is **synchronous**.

**Test case (run in shell):**

```python
from signals_task.models import Demo_model
import time

start = time.time()
Demo_model.objects.create(name="Test1")
print("Time taken:", time.time() - start)
```

**Expected output:**

```
Signal started
(it will wait here for 7 seconds)
Signal finished
MainThread
Not inside transaction
<Demo_model: Test1>
Time taken: 7.00xx
```

If "Time taken" is around 7 seconds, that confirms the proof.

Note: All three signals (`first_question`, `second_function`, `thirdfunction`) are connected to the same `post_save` signal of `Demo_model`. So whenever `Demo_model.objects.create()` is called - even while testing just Q1 - all three of them run together. That's why "MainThread" and "Not inside transaction" also show up in the output above, even though we are only checking Q1 here. The `<Demo_model: Test1>` line is just the return value of `create()` being displayed by the shell, and "Time taken" is from my own print statement.

---

### Question 2: Do django signals run in the same thread as the caller?

**My answer:** Yes, same thread.

**Why?**

In `second_function`, I printed `threading.current_thread().name`. If I also print this same line in my normal code (outside the signal), and both show the same name (`MainThread`), it means the signal is not creating a separate thread - it is using the same thread that the caller (my code) was using.

**Test case (run in shell):**

```python
import threading
from signals_task.models import Demo_model

print("Main thread name:", threading.current_thread().name)
Demo_model.objects.create(name="Test2")
```

**Expected output:**

```
Main thread name: MainThread
Signal started
(7 sec wait)
Signal finished
MainThread
Not inside transaction
<Demo_model: Test2>
```

Both places show `MainThread` - once from my print statement, and once from inside the signal. This confirms same thread.

---

### Question 3: By default do django signals run in the same database transaction as the caller?

**My answer:** Yes, by default they run in the same transaction.

**Why?**

In `thirdfunction`, I checked `connection.in_atomic_block` - this tells whether Django is currently inside a transaction or not.

I tested this in two ways:

1. First I ran a normal `create()` - it printed "Not inside transaction" because by default Django uses a separate auto-commit transaction for each query.
2. Then I created an object inside a `transaction.atomic()` block and raised an error right after, so the whole block fails (rollback happens).

The result was that the object created through the signal also got rolled back - meaning the signal was part of the **same transaction** as my code. If the signal was running in a separate transaction, its work would still be saved in the database even after the error.

**Test case (run in shell):**

```python
from django.db import transaction
from signals_task.models import Demo_model

# normal create - no transaction
Demo_model.objects.create(name="Test3")

# now try inside an atomic block and raise an error
try:
    with transaction.atomic():
        Demo_model.objects.create(name="Test4")
        raise Exception("forcing rollback")
except Exception as e:
    print("Error:", e)

# check if Test4 still exists or not
print(Demo_model.objects.filter(name="Test4").exists())
```

**Expected output:**

```
Signal started
(7 sec wait)
Signal finished
MainThread
Not inside transaction
<Demo_model: Test3>

Signal started
(7 sec wait)
Signal finished
MainThread
Inside transaction
<Demo_model: Test4>
Error: forcing rollback
False
```

The last line is `False` - meaning Test4 was never actually saved, it got rolled back. This is the proof that the signal was part of the same transaction.

---

## Part 2 - Rectangle Class

### models.py (rectangle_task)

```python
class Rectangle:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width

    def __iter__(self):
        yield {'length': self.length}
        yield {'width': self.width}
```

**Explanation:**

- `__init__` stores the length and width, both are integers.
- `__iter__` is a special method that makes the class "iterable", meaning it can be used in a `for` loop.
- `yield` returns one value at a time, one after another - first the length dictionary, then the width dictionary.

**Test case (run in shell):**

```python
from rectangle_task.models import Rectangle

rect = Rectangle(10, 5)
for item in rect:
    print(item)
```

**Expected output:**

```
{'length': 10}
{'width': 5}
```

---

## All test cases together (copy-paste in shell)

Note: Above, I showed the output for each question separately (Q1's output, then Q2's output, then Q3's output, one by one). That was when I ran each test case on its own.

But if you run the combined block below all at once, all of that output will come together, one after another, in the same order as the code runs (Q1's output first, then Q2's, then Q3's, then Rectangle's). It's the same output as above, just not separated - it will appear as one continuous block in the shell.

```python
from signals_task.models import Demo_model
from rectangle_task.models import Rectangle
from django.db import transaction
import time
import threading

# Q1 - synchronous check
print("---- Q1 ----")
start = time.time()
Demo_model.objects.create(name="Test1")
print("Time taken:", time.time() - start)

# Q2 - thread check
print("---- Q2 ----")
print("Main thread name:", threading.current_thread().name)
Demo_model.objects.create(name="Test2")

# Q3 - transaction check
print("---- Q3 ----")
Demo_model.objects.create(name="Test3")

try:
    with transaction.atomic():
        Demo_model.objects.create(name="Test4")
        raise Exception("forcing rollback")
except Exception as e:
    print("Error:", e)

print("Test4 exists?", Demo_model.objects.filter(name="Test4").exists())

# Rectangle check
print("---- Rectangle ----")
rect = Rectangle(10, 5)
for item in rect:
    print(item)
```

---

## Summary

So to quickly sum up what I found out:

- Q1: Django signals run **synchronously** - the main code waits for the signal to finish before moving forward.
- Q2: Signals run in the **same thread** as the caller, no separate thread is created.
- Q3: By default, signals are part of the **same database transaction** as the caller - if the transaction rolls back, whatever the signal did also gets rolled back.

I have explained the reasoning and shown the test cases with expected output for each of these above.