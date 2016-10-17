# -*- coding: utf-8 -*-
import json

from aiohttp.hdrs import (
    METH_GET,
    METH_POST,
    METH_PUT,
    METH_DELETE
)
from aiohttp import web
from djaio.core.exceptions import BadRequestException
from djaio.core.models import NullInput, NullOutput

from djaio.core.utils import get_int_or_none
from schematics.exceptions import ModelConversionError, ConversionError, DataError


class BaseMethod(object):
    def __init__(self, input_model=NullInput, output_model=NullOutput, description=None):
        self.result = None
        self.input_model = input_model
        self.output_model = output_model
        self.total = None
        self.success = None
        self.errors = []
        self.params = None
        self.output = None
        self.pagination = None
        self.limit = None
        self.offset = None
        self.settings = None
        self.description = description

    def process_request(self, request):
        #Override it for your purposes
        return request.copy()

    async def from_http(self, request):
        self.errors = []
        self.result = []
        if not isinstance(request, web.Request):
            raise web.HTTPBadRequest()

        get_params = self.process_request(request.GET)

        self.limit = request.headers.get('X-Limit') or \
                     get_int_or_none(get_params.pop('limit', None)) or \
                     request.app.settings.LIMIT
        self.offset = request.headers.get('X-Offset') or \
                      get_int_or_none(get_params.pop('offset', None)) or \
                      request.app.settings.OFFSET

        try:
            if request.method in (METH_GET, METH_DELETE):
                self.params = self.input_model(get_params).to_primitive()
            elif request.method in (METH_PUT, METH_POST):
                try:
                    self.params = self.input_model(await request.json()).to_primitive()
                except (ValueError, TypeError):
                    self.params = self.input_model(await request.post()).to_primitive()
        except (ModelConversionError, ConversionError, DataError) as exc:

            errors = []
            for k, v in exc.messages.items():

                if isinstance(v, dict):
                    for _, error in v.items():
                        if isinstance(error, ConversionError):
                            errors.append({k: [x.summary for x in error.messages]})

                elif isinstance(v, ConversionError):
                    errors.append({k: [x.summary for x in v.messages]})

            raise BadRequestException(message=errors)
        self.settings = request.app.settings

    async def execute(self):
        raise NotImplementedError('Please override `execute()` method.')

    def get_pagination(self):
        _pagination_object = {
            'total': self.total,
            'limit': self.limit,
            'offset': self.offset
        }
        if not self.total:
            return
        self.pagination = _pagination_object
        return self.pagination

    async def get_output(self):
        self.result = await self.execute()
        self.output = {
            'result': [self.output_model(x).to_primitive() for x in self.result],
            'success': not self.errors
        }
        if self.errors:
            self.output.update({'errors': self.errors})
        pagination = self.get_pagination()
        if pagination:
            self.output.update({'pagination': pagination})
        return self.output