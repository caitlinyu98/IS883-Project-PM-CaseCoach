"""Context-local, opt-in measurements; no keys, prompts, or error messages logged."""
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

_sink = ContextVar('measurement_sink', default=None)
_stage = ContextVar('measurement_stage', default='generation')

@contextmanager
def capture(records):
    token = _sink.set(records)
    try:
        yield records
    finally:
        _sink.reset(token)

@contextmanager
def stage(name):
    token = _stage.set(name)
    try:
        yield
    finally:
        _stage.reset(token)

def measured(request, client, model):
    start = perf_counter()
    record = dict(call_id=str(uuid4()), stage=_stage.get(), model=model,
                  usage=None, status='error')
    try:
        response = request(client, model)
        usage = getattr(response, 'usage_metadata', None)
        record.update(status='ok', usage=usage.model_dump(mode='json') if usage else None,
                      model_version=getattr(response, 'model_version', None))
        return response
    except Exception as error:
        record.update(error_type=type(error).__name__, status_code=getattr(error, 'code', None))
        raise
    finally:
        record['seconds'] = perf_counter() - start
        sink = _sink.get()
        if sink is not None:
            sink.append(record)
