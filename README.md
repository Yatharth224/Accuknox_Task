# Accuknox Django Assignment

This project was given to me as a company assignment. It has two parts:

1. Practical proof for three questions related to Django Signals
2. A custom Rectangle class that can be iterated over

---

## Project Structure

```
Accuknox_Task/
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

## Local Setup

Clone the repo and go inside the project folder:

```bash
git clone <repo-url>
cd Accuknox_Task
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate      # on windows: venv\Scripts\activate
```

Install the requirements:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Start the server (optional, just to confirm everything is set up correctly):

```bash
python manage.py runserver
```

---

## How to open the Django shell

All the testing for this assignment is done through the Django shell, not through views/urls.

```bash
python manage.py shell
```

This opens an interactive Python shell where Django is already set up, so you can directly import models and run code.

---

## Part 1 - Django Signals

I created a simple model called `Demo_model`, just to trigger the `post_save` signal. It has no other purpose.

```python
# signals_task/models.py
from django.db import models


class Demo_model(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
```

All three signal functions below are connected to the `post_save` signal of `Demo_model`. So whenever `Demo_model.objects.create()` is called, all three functions run together - that's why all three outputs (sync delay, thread name, transaction status) show up together in every test case, even when we're checking only one question.

---

### Question 1: Are django signals executed synchronously or asynchronously?

**My answer:** Synchronously.

```python
# signals_task/signals.py
@receiver(post_save, sender=Demo_model)
def first_question(sender, instance, **kwargs):
    print("Signal started")
    time.sleep(7)
    print("Signal finished")
```

**Why?**

I added `time.sleep(7)` inside this function. If signals were asynchronous, `create()` would return immediately and "Signal finished" would print later in the background. But the `create()` call gets blocked for 7 seconds, and only after that the return value is printed. This proves the main code waits for the signal to finish - i.e. it is **synchronous**.

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
(waits 7 seconds)
Signal finished
MainThread
Not inside transaction
<Demo_model: Test1>
Time taken: 7.00xx
```

If "Time taken" is around 7 seconds, that confirms the proof.

---

### Question 2: Do django signals run in the same thread as the caller?

**My answer:** Yes, same thread.

```python
# signals_task/signals.py
@receiver(post_save, sender=Demo_model)
def second_question(sender, instance, **kwargs):
    print(threading.current_thread().name)
```

**Why?**

I print the current thread name inside the signal. If I also print the thread name in my own code (before calling `create()`), and both show the same name (`MainThread`), it means the signal did not create a separate thread - it ran in the same thread as the caller.

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
(waits 7 seconds)
Signal finished
MainThread
Not inside transaction
<Demo_model: Test2>
```

Both lines show `MainThread` - one from my own print, one from inside the signal. This confirms same thread.

---

### Question 3: By default do django signals run in the same database transaction as the caller?

**My answer:** Yes, by default they run in the same transaction.

```python
# signals_task/signals.py
@receiver(post_save, sender=Demo_model)
def third_question(sender, instance, **kwargs):
    if connection.in_atomic_block:
        print("Inside transaction")
    else:
        print("Not inside transaction")
```

**Why?**

`connection.in_atomic_block` tells whether Django is currently inside a transaction or not. I tested this in two ways: a normal `create()` outside any transaction, and a `create()` inside `transaction.atomic()` followed by a forced error (so the whole block rolls back).

**Test case (run in shell):**

```python
from django.db import transaction
from signals_task.models import Demo_model

# normal create - no transaction
Demo_model.objects.create(name="Test3")

# inside an atomic block, then force an error
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
(waits 7 seconds)
Signal finished
MainThread
Not inside transaction
<Demo_model: Test3>

Signal started
(waits 7 seconds)
Signal finished
MainThread
Inside transaction
<Demo_model: Test4>
Error: forcing rollback
False
```

The last line is `False` - Test4 was never actually saved, it got rolled back along with the outer transaction. This proves the signal ran inside the same transaction as the caller. If it had run in a separate transaction, Test4 would still exist in the database even after the error.

---

## Part 2 - Rectangle Class

```python
# rectangle_task/models.py
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
- `__iter__` makes the class iterable, so it can be used in a `for` loop.
- `yield` returns one value at a time - first the length dictionary, then the width dictionary.

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

## Running all test cases together

If you run all the test cases above one after another in the same shell session, the output of all of them will appear together in one continuous block, in the order the code runs. The content is the same as shown above for each question - it just won't be separated.

```python
from signals_task.models import Demo_model
from rectangle_task.models import Rectangle
from django.db import transaction
import time
import threading

# Q1
start = time.time()
Demo_model.objects.create(name="Test1")
print("Time taken:", time.time() - start)

# Q2
print("Main thread name:", threading.current_thread().name)
Demo_model.objects.create(name="Test2")

# Q3
Demo_model.objects.create(name="Test3")
try:
    with transaction.atomic():
        Demo_model.objects.create(name="Test4")
        raise Exception("forcing rollback")
except Exception as e:
    print("Error:", e)
print("Test4 exists?", Demo_model.objects.filter(name="Test4").exists())

# Rectangle
rect = Rectangle(10, 5)
for item in rect:
    print(item)
```