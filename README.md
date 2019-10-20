# Full Profiler
Profile asyncio code in addition to normal sync code

## Why?
For this piece of code:

```python
async def do_sleep():
    await asyncio.sleep(.3)
```

Most profilers produce something that looks like this:

| Filename | First line | Name | Call Count | Total Time | Min | Mean | Max |
|- | - | - | - | - | - | - | - |
/usr/lib/python3.6/asyncio/base_events.py | 449 | run_until_complete | 1 | 0.30283427238464355 | 0.30283427238464355 | 0.30283427238464355 | 0.30283427238464355
/usr/lib/python3.6/asyncio/base_events.py | 421 | run_forever | 1 | 0.3022620677947998 | 0.3022620677947998 | 0.3022620677947998 | 0.3022620677947998
/usr/lib/python3.6/asyncio/base_events.py | 1355 | _run_once | 4 | 0.30194830894470215 | 0.00011038780212402344 | 0.07548707723617554 | 0.30086636543273926
/usr/lib/python3.6/selectors.py | 428 | select | 4 | 0.3006551265716553 | 2.765655517578125e-05 | 0.07516378164291382 | 0.3004953861236572
? | ? | epoll.poll | 4 | 0.3003730773925781 | 3.814697265625e-06 | 0.07509326934814453 | 0.30034446716308594
fullprofiler/tests/test_profiler.py | 44 | do_sleep | 2 | 0.00041365623474121094 | 4.6253204345703125e-05 | 0.00020682811737060547 | 0.0003674030303955078


Granted no one ever means to leave something like an `await asyncio.sleep(.3)` in code (it has been known to happen),
more inconspicuous things end up blocking for longer than expected, and can take a tax on runtime. For example:

```python
async def foo(count)
    requests_to_make = [request_coroutine() for _ in range(count)]
    await asyncio.wait(requests_to_make)
```

In certain circumstances, such as a low count value and/or quick requests, this could be very fast.
In other circumstances, such as a very large count value and/or very slow requests, this could be horrible.
How do you know if it isn't through profiling all of your code?

**How can you know where the real bottleneck is when the profiler says all of your coroutines take microseconds to execute?**

The sync version, afterall, returns output like this:

| Filename | First line | Name | Call Count | Total Time | Min | Mean | Max |
|- | - | - | - | - | - | - | - |
fullprofiler/tests/test_profiler.py | 20 | do_sleep | 1 | 0.3004031181335449 | 0.3004031181335449 | 0.3004031181335449 | 0.3004031181335449
time | ? | sleep | 1 | 0.3003404140472412 | 0.3003404140472412 | 0.3003404140472412 | 0.3003404140472412

## What is going on?
In python 3.6 (likely other revs as well. This is the default py3 rev on the ubuntu 18.04 LTS release),
when a coroutine is called, the following happens:
1. The `call` event is sent to the profiler to notify it that it is entering a function.
1. The `return` event is sent to the profiler microseconds later with a `Future` object.
1. When the coroutine is finished, another `call` event is raised for the same function
(note the call count is 2 in this example).
1. The `return` event is raised immediately, holding the result of the future.

## How can this be fixed?
The current approach is to add a callback to the future when it's returned in step 2 above. This callback
will finish reporting the total run time. Additionally, other work should be done to prevent the call count from going up more than once when the coroutine is only called once.

Is it perfect? No.

Will it work in every circumstance? No.

Is it free from strange issues, such as race conditions when the profiler is turned off in the middle of a coroutine? Probably not.

Will it do a decent job at providing info about code bottlenecks? Yes!

## Where to next?
There are already so many wonderful profilers out there. Ideally, they will be updated to include a similar fix
(please cite your sources!). If that doesn't happen, and this tool starts to become something more serious than
it was intended to be, it should:
1. Get compiled to avoid overhead
1. Allow the user to specify the timer, as other profilers do
1. Allow statistical profiling
1. Allow profiles to be run with a syntax like `python -m fullprofiler script.py`
1. Add an atexit handler
1. Avoid using the `print` function
1. Improve unit tests
1. Handle the imperfections mentioned above
